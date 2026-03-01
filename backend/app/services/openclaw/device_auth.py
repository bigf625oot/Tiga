"""
OpenClaw Device Authentication & Identity
"""
import base64
import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger("openclaw.auth")

class DeviceIdentityManager:
    """
    管理 Ed25519 设备密钥对，实现 Gateway v2 签名格式。
    """

    def __init__(self, key_dir: str | Path | None = None):
        self._dir = Path(key_dir or Path.home() / ".openclaw" / "python-client")
        self._dir.mkdir(parents=True, exist_ok=True)

        self._key_path = self._dir / "device.key"      # 32 字节 raw 私钥
        self._token_path = self._dir / "device_token.json"

        self._priv_bytes, self._pub_bytes = self._load_or_create_keypair()
        
        # 优先使用配置的 Device ID (如果用户明确指定)
        from app.core.config import settings
        if settings.OPENCLAW_DEVICE_ID:
            self._device_id = settings.OPENCLAW_DEVICE_ID
            # 校验一致性
            derived = self._derive_device_id()
            if derived != self._device_id:
                logger.warning(f"使用配置的 Device ID ({self._device_id})，但它与私钥派生 ID ({derived}) 不一致！请检查 .env 配置。")
        else:
            self._device_id = self._derive_device_id()

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def public_key_b64(self) -> str:
        return base64.b64encode(self._pub_bytes).decode()

    def sign(
        self,
        *,
        nonce: str,
        role: str,
        scopes: list[str],
        token: str | None,
        client_id: str,
        client_mode: str,
    ) -> tuple[str, int]:
        """
        使用 v2 pipe-delimited 格式构造并签名认证 payload。
        """
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        except ImportError:
            raise RuntimeError("缺少 cryptography 库，请执行：pip install cryptography")

        signed_at = int(time.time() * 1000)
        scopes_str = ",".join(sorted(scopes))

        # v2 格式：pipe-delimited，包含 nonce
        # 字段顺序：v2 | deviceId | clientId | clientMode | role | scopes | signedAtMs | token | nonce
        # 注意：token 为 Gateway Token (auth.token)，如果使用 deviceToken 登录则为空字符串
        payload_str = "|".join([
            "v2",
            self._device_id,
            client_id,
            client_mode,
            role,
            scopes_str,
            str(signed_at),
            token or "",
            nonce,
        ])
        payload_bytes = payload_str.encode("utf-8")
        logger.debug("签名 payload：%s", payload_str)

        priv_key = Ed25519PrivateKey.from_private_bytes(self._priv_bytes)
        raw_sig = priv_key.sign(payload_bytes)
        sig_b64 = base64.b64encode(raw_sig).decode()

        return sig_b64, signed_at

    def load_device_token(self) -> str | None:
        if not self._token_path.exists():
            return None
        try:
            data = json.loads(self._token_path.read_text())
            return data.get("deviceToken")
        except Exception as exc:
            logger.warning("加载设备令牌失败：%s", exc)
            return None

    def save_device_token(self, token: str, role: str, scopes: list[str]) -> None:
        data = {"deviceToken": token, "role": role, "scopes": scopes}
        self._token_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        logger.info("设备令牌已保存至 %s", self._token_path)

    def clear_device_token(self) -> None:
        if self._token_path.exists():
            try:
                self._token_path.unlink()
                logger.info("设备令牌已清除: %s", self._token_path)
            except Exception as e:
                logger.warning("清除设备令牌失败: %s", e)

    def _load_or_create_keypair(self) -> tuple[bytes, bytes]:
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat
        except ImportError:
            raise RuntimeError("缺少 cryptography 库")

        # 1. 优先从 Settings (Env) 加载
        from app.core.config import settings
        if settings.OPENCLAW_DEVICE_PRIVATE_KEY:
            try:
                # 尝试解码
                candidate_key = settings.OPENCLAW_DEVICE_PRIVATE_KEY.strip()
                priv_raw = base64.b64decode(candidate_key)
                
                # Ed25519 私钥种子通常是 32 字节
                if len(priv_raw) == 32:
                    priv_key = Ed25519PrivateKey.from_private_bytes(priv_raw)
                    pub_raw = priv_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
                    logger.info("已加载配置中的设备私钥 (OPENCLAW_DEVICE_PRIVATE_KEY)")
                    
                    # 验证配置的 ID 是否匹配（可选，仅打印警告）
                    if settings.OPENCLAW_DEVICE_ID:
                        derived_id = hashlib.sha256(pub_raw).hexdigest()
                        if derived_id != settings.OPENCLAW_DEVICE_ID:
                            logger.warning(f"配置的 Device ID ({settings.OPENCLAW_DEVICE_ID}) 与私钥派生的 ID ({derived_id}) 不一致！将使用派生 ID。")
                    
                    return priv_raw, pub_raw
                else:
                    logger.warning(f"配置的私钥长度 ({len(priv_raw)}) 不正确，期望 32 字节。将回退到本地文件。")
            except Exception as e:
                logger.error(f"加载配置中的设备私钥失败: {e}。将回退到本地文件。")

        # 2. 从本地文件加载
        if self._key_path.exists():
            priv_raw = self._key_path.read_bytes()
            priv_key = Ed25519PrivateKey.from_private_bytes(priv_raw)
            pub_raw  = priv_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
            return priv_raw, pub_raw

        priv_key = Ed25519PrivateKey.generate()
        priv_raw = priv_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
        pub_raw = priv_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        self._key_path.write_bytes(priv_raw)
        os.chmod(self._key_path, 0o600)
        return priv_raw, pub_raw

    def _derive_device_id(self) -> str:
        return hashlib.sha256(self._pub_bytes).hexdigest()

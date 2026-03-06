"""
应用场景：
    任务路由锁定与验签机制。
    确保任务能够安全、准确地路由到指定节点，防止篡改和路由冲突。

核心功能：
    - 从payload中提取目标节点标识
    - 路由锁定（添加元数据和签名）
    - 路由验证（签名校验、摘要比对）
    - 防止路由字段冲突和篡改

__author__ = "Tiga"
__version__ = "1.0.0"
__datetime__ = "2026-03-04 09:00:00"
"""

import copy
import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.core.config import settings
from app.services.openclaw.common.errors import DispatchErrorType, DispatchException

ROUTING_TARGET_FIELD = "target_node_uuid"
ROUTING_META_FIELD = "__routing"
SUPPORTED_ROUTE_FIELDS = ("target_node_uuid", "target_node_id", "node_id")
ROUTING_VERSION = "v1"


@dataclass(frozen=True)
class RoutingLockResult:
    payload: Dict[str, Any]
    target_node_uuid: str
    source: str


def _get_routing_secret() -> str:
    secret = (
        getattr(settings, "OPENCLAW_ROUTING_SECRET", None)
        or settings.OPENCLAW_GATEWAY_TOKEN
    )
    if not secret:
        raise DispatchException(
            DispatchErrorType.ROUTING_INVALID,
            "缺少路由签名密钥配置 OPENCLAW_ROUTING_SECRET/OPENCLAW_GATEWAY_TOKEN",
            http_status=403,
            error_code="OPENCLAW_ROUTING_SECRET_MISSING",
        )
    return secret


def _canonical_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _payload_hash(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _validate_node_value(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise DispatchException(
            DispatchErrorType.ROUTING_INVALID,
            f"路由字段 {field_name} 必须为字符串",
            http_status=400,
            error_code="OPENCLAW_ROUTING_FIELD_TYPE_INVALID",
        )
    candidate = value.strip()
    if not candidate:
        raise DispatchException(
            DispatchErrorType.ROUTING_INVALID,
            f"路由字段 {field_name} 不能为空",
            http_status=400,
            error_code="OPENCLAW_ROUTING_FIELD_EMPTY",
        )
    if len(candidate) > 128:
        raise DispatchException(
            DispatchErrorType.ROUTING_INVALID,
            f"路由字段 {field_name} 长度超限",
            http_status=400,
            error_code="OPENCLAW_ROUTING_FIELD_TOO_LONG",
        )
    return candidate


def _extract_candidate_target(payload: Dict[str, Any]) -> Optional[str]:
    found = []
    for key in SUPPORTED_ROUTE_FIELDS:
        if key in payload and payload.get(key) is not None:
            found.append((key, _validate_node_value(payload.get(key), key)))
    if not found:
        return None
    values = {value for _, value in found}
    if len(values) != 1:
        raise DispatchException(
            DispatchErrorType.ROUTING_FORBIDDEN,
            "payload 中存在冲突的目标节点字段",
            http_status=403,
            error_code="OPENCLAW_ROUTING_FIELD_CONFLICT",
        )
    return found[0][1]


def lock_routing_payload(
    payload: Dict[str, Any],
    selected_node_id: str,
    task_id: str,
) -> RoutingLockResult:
    selected = _validate_node_value(selected_node_id, "selected_node_id")
    mutable = copy.deepcopy(payload or {})
    candidate_target = _extract_candidate_target(mutable)
    source = "payload" if candidate_target else "gateway"
    if candidate_target and candidate_target != selected:
        raise DispatchException(
            DispatchErrorType.ROUTING_FORBIDDEN,
            f"payload 目标节点与预选节点不一致: payload={candidate_target}, selected={selected}",
            http_status=403,
            error_code="OPENCLAW_ROUTING_TARGET_MISMATCH",
        )

    mutable[ROUTING_TARGET_FIELD] = selected
    issued_at = int(time.time())
    nonce = str(uuid.uuid4())

    body_without_meta = copy.deepcopy(mutable)
    payload_digest = _payload_hash(body_without_meta)
    signature_payload = f"{selected}|{task_id}|{payload_digest}|{issued_at}|{nonce}|{ROUTING_VERSION}"
    signature = hmac.new(
        _get_routing_secret().encode("utf-8"),
        signature_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    mutable[ROUTING_META_FIELD] = {
        "version": ROUTING_VERSION,
        "task_id": task_id,
        "source": source,
        "issued_at": issued_at,
        "nonce": nonce,
        "payload_sha256": payload_digest,
        "signature": signature,
    }
    return RoutingLockResult(payload=mutable, target_node_uuid=selected, source=source)


def verify_routing_payload(payload: Dict[str, Any], expected_node_id: Optional[str] = None) -> str:
    if ROUTING_META_FIELD not in payload:
        raise DispatchException(
            DispatchErrorType.ROUTING_MISSING,
            "缺少 __routing 元数据",
            http_status=400,
            error_code="OPENCLAW_ROUTING_META_MISSING",
        )
    if ROUTING_TARGET_FIELD not in payload:
        raise DispatchException(
            DispatchErrorType.ROUTING_MISSING,
            "缺少 target_node_uuid 字段",
            http_status=400,
            error_code="OPENCLAW_ROUTING_TARGET_MISSING",
        )
    target = _validate_node_value(payload.get(ROUTING_TARGET_FIELD), ROUTING_TARGET_FIELD)
    if expected_node_id and target != expected_node_id:
        raise DispatchException(
            DispatchErrorType.ROUTING_FORBIDDEN,
            f"目标节点不匹配: expected={expected_node_id}, actual={target}",
            http_status=403,
            error_code="OPENCLAW_ROUTING_EXPECTED_NODE_MISMATCH",
        )

    routing_meta = payload.get(ROUTING_META_FIELD)
    if not isinstance(routing_meta, dict):
        raise DispatchException(
            DispatchErrorType.ROUTING_INVALID,
            "__routing 必须为对象",
            http_status=400,
            error_code="OPENCLAW_ROUTING_META_TYPE_INVALID",
        )

    required_keys = ("task_id", "issued_at", "nonce", "payload_sha256", "signature", "version")
    missing = [k for k in required_keys if not routing_meta.get(k)]
    if missing:
        raise DispatchException(
            DispatchErrorType.ROUTING_MISSING,
            f"__routing 缺失字段: {','.join(missing)}",
            http_status=400,
            error_code="OPENCLAW_ROUTING_META_FIELD_MISSING",
        )

    payload_copy = copy.deepcopy(payload)
    payload_copy.pop(ROUTING_META_FIELD, None)
    payload_digest = _payload_hash(payload_copy)
    if payload_digest != routing_meta.get("payload_sha256"):
        raise DispatchException(
            DispatchErrorType.ROUTING_FORBIDDEN,
            "payload 摘要校验失败，疑似被篡改",
            http_status=403,
            error_code="OPENCLAW_ROUTING_PAYLOAD_HASH_MISMATCH",
        )

    signature_payload = (
        f"{target}|{routing_meta.get('task_id')}|{routing_meta.get('payload_sha256')}|"
        f"{routing_meta.get('issued_at')}|{routing_meta.get('nonce')}|{routing_meta.get('version')}"
    )
    expected_signature = hmac.new(
        _get_routing_secret().encode("utf-8"),
        signature_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, str(routing_meta.get("signature"))):
        raise DispatchException(
            DispatchErrorType.ROUTING_FORBIDDEN,
            "routing 签名校验失败",
            http_status=403,
            error_code="OPENCLAW_ROUTING_SIGNATURE_INVALID",
        )
    return target

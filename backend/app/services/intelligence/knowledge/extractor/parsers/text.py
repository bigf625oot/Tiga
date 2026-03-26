import logging

logger = logging.getLogger(__name__)


def is_text_valid(text: str) -> bool:
    if not text:
        return False

    total_len = len(text)
    if total_len < 50:
        return True

    private_use_count = sum(1 for c in text if "\ue000" <= c <= "\uf8ff")
    if private_use_count / total_len > 0.1:
        logger.warning(f"检测到大量私用区字符 ({private_use_count}/{total_len})，判定为乱码")
        return False

    return True


def sanitize_text(text: str) -> str:
    if not text:
        return ""

    cleaned = text.encode("utf-8", "ignore").decode("utf-8")
    cleaned = cleaned.replace("\x00", "")
    return cleaned

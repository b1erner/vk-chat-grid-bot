from __future__ import annotations
import re
from typing import Optional, Tuple

ID_RE = re.compile(r"\[id(\d+)\|[^\]]+\]|id(\d+)|https?://vk.com/id(\d+)|@id(\d+)", re.IGNORECASE)

def extract_user_id(text: str) -> Optional[int]:
    if not text:
        return None
    m = ID_RE.search(text)
    if m:
        for i in range(1, 5):
            if m.group(i):
                try:
                    return int(m.group(i))
                except Exception:
                    return None
    try:
        return int(text.strip())
    except Exception:
        return None

def parse_command(text: str) -> Tuple[str, str]:
    text = (text or '').strip()
    if not text.startswith('/'):
        return '', ''
    parts = text.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ''
    return cmd, arg

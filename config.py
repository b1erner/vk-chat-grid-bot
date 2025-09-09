from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Optional
from loguru import logger

load_dotenv()

@dataclass
class Config:
    vk_token: str
    owner_id: Optional[int]
    db_path: str
    host: str
    port: int

    @classmethod
    def from_env(cls) -> "Config":
        token = os.getenv("VK_TOKEN") or os.getenv("VK_API_TOKEN") or ""
        if not token:
            logger.warning("VK token not provided in environment (VK_TOKEN).")
        owner = os.getenv("OWNER_ID")
        owner_id = int(owner) if owner and owner.isdigit() else None
        db_path = os.getenv("DB_PATH", "bot.sqlite")
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "10000"))
        return cls(vk_token=token, owner_id=owner_id, db_path=db_path, host=host, port=port)

import os
from dataclasses import dataclass

@dataclass
class Config:
    vk_token: str
    owner_id: int
    database_path: str
    group_id: int

    @staticmethod
    def from_env():
        token = os.getenv("VK_TOKEN")
        owner = os.getenv("OWNER_ID")
        db = os.getenv("DATABASE_PATH", "/var/data/bot.db")
        group = os.getenv("GROUP_ID") or os.getenv("GROUP_ID_INT") or os.getenv("GROUP_ID_NUM")
        if token is None or owner is None:
            raise RuntimeError("VK_TOKEN and OWNER_ID must be set in environment")
        try:
            owner_id = int(owner)
        except Exception:
            raise RuntimeError("OWNER_ID must be an integer")
        try:
            group_id = int(group) if group else 0
        except Exception:
            group_id = 0
        return Config(vk_token=token, owner_id=owner_id, database_path=db, group_id=group_id)

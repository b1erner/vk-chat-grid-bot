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
        group = os.getenv("GROUP_ID") or os.getenv("GROUP_ID_INT") or os.getenv("GROUP")

        default_db_path = os.path.join(os.getcwd(), "data", "bot.db")
        db = os.getenv("DATABASE_PATH", default_db_path)

        # Проверки
        if not token:
            raise ValueError("❌ VK_TOKEN is not set in environment")
        if not owner:
            raise ValueError("❌ OWNER_ID is not set in environment")
        if not group:
            raise ValueError("❌ GROUP_ID (или GROUP_ID_INT, или GROUP) is not set in environment")

        return Config(
            token,
            int(owner),
            db,
            int(group)
        )

import os
import requests
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
        group = os.getenv("GROUP_ID") or os.getenv("GROUP_NAME")

        default_db_path = os.path.join(os.getcwd(), "data", "bot.db")
        db = os.getenv("DATABASE_PATH", default_db_path)

        if not token:
            raise ValueError("❌ VK_TOKEN is not set")
        if not owner:
            raise ValueError("❌ OWNER_ID is not set")
        if not group:
            raise ValueError("❌ GROUP_ID or GROUP_NAME must be set")

        # Если передано имя сообщества, конвертируем в ID
        if not group.isdigit():
            resp = requests.get(
                "https://api.vk.com/method/groups.getById",
                params={"group_id": group, "access_token": token, "v": "5.199"},
                timeout=10
            ).json()
            try:
                group = resp["response"][0]["id"]
            except Exception:
                raise ValueError(f"❌ Failed to resolve group name '{group}' to ID")

        return Config(
            token,
            int(owner),
            db,
            int(group)
        )

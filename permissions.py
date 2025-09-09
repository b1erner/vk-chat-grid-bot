from __future__ import annotations
from vk_client import VK

class Guard:
    def __init__(self, vk: VK, owner_id: int):
        self.vk = vk
        self.owner_id = owner_id

    def only_owner(self, user_id: int) -> bool:
        return user_id == self.owner_id

    def only_chat_admin(self, peer_id: int, user_id: int) -> bool:
        is_admin, _ = self.vk.get_conversation_admin_flags(peer_id, user_id)
        return is_admin

    def protect_targets(self, peer_id: int, target_user_id: int) -> bool:
        # True если целевой пользователь НЕ админ (т.е. можно действовать)
        is_admin, _ = self.vk.get_conversation_admin_flags(peer_id, target_user_id)
        return not is_admin


def is_owner(user_id: int, config) -> bool:
    return user_id == config.owner_id

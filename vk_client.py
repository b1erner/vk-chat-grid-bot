from __future__ import annotations
from typing import Tuple, Optional
from loguru import logger
from vk_api import VkApi, utils as vk_utils
from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.exceptions import ApiError
from constants import SYSTEM_PEER_BASE

class VK:
    def __init__(self, token: str):
        self.session = VkApi(token=token)
        self.api = self.session.get_api()
        try:
            info = self.api.groups.getById()
            self.group_id = info[0]['id'] if info else None
        except Exception:
            self.group_id = None
        self.longpoll = VkBotLongPoll(self.session, group_id=self.group_id) if self.group_id else None
        logger.info(f"VK client initialized for group_id={self.group_id}")

    def _peer_to_chat_id(self, peer_id: int) -> Optional[int]:
        if peer_id > SYSTEM_PEER_BASE:
            return int(peer_id - SYSTEM_PEER_BASE)
        return None

    def send(self, peer_id: int, message: str, keyboard: Optional[dict]=None) -> bool:
        try:
            params = dict(peer_id=peer_id, message=message, random_id=vk_utils.get_random_id())
            if keyboard is not None:
                params['keyboard'] = keyboard
            self.api.messages.send(**params)
            return True
        except ApiError as e:
            logger.warning(f"VK API send failed: {e}")
        except Exception as e:
            logger.exception(e)
        return False

    def remove_user(self, peer_id: int, user_id: int) -> Tuple[bool, str]:
        # Try to remove user from conversation (chat). VK needs chat_id (peer - 2e9)
        chat_id = self._peer_to_chat_id(peer_id)
        if chat_id is None:
            return False, 'not_chat'
        try:
            # messages.removeChatUser is deprecated for group bots, but we'll attempt call that.
            # For group bots new method may be messages.removeConversationUser, but vk_api wrapper may differ.
            try:
                self.api.messages.removeChatUser(chat_id=chat_id, member_id=user_id)
            except Exception:
                # fallback
                self.api.messages.removeConversationUser(peer_id=peer_id, member_id=user_id)
            return True, 'ok'
        except ApiError as e:
            logger.warning(f"remove_user ApiError chat={chat_id} user={user_id}: {e}")
            return False, 'api_error'
        except Exception as e:
            logger.exception(e)
            return False, 'error'

    def get_conversation_admin_flags(self, peer_id: int, user_id: int) -> Tuple[bool, bool]:
        # returns (is_admin_or_owner, is_owner)
        try:
            data = self.api.messages.getConversationMembers(peer_id=peer_id)
            for it in data.get('items', []):
                if it.get('member_id') == user_id:
                    return bool(it.get('is_admin') or it.get('is_owner')), bool(it.get('is_owner'))
        except Exception as e:
            logger.debug(f"get_conversation_admin_flags failed: {e}")
        return False, False

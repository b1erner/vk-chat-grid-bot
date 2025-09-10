from __future__ import annotations

import os
from typing import Optional

from vk_client import VKClient
from config import Config
from db import DB
from permissions import is_owner

SYSTEM_PEER_BASE = 2000000000

class Handlers:
    def __init__(self, vk: VKClient, db: DB, config: Config):
        self.vk = vk
        self.db = db
        self.config = config

    def handle_event(self, event):
        try:
            msg = event.obj['message']
        except Exception:
            return

        peer_id = msg.get('peer_id')
        if not peer_id:
            return

        # handle chat actions (kick/leave)
        action = msg.get('action', {})
        if action:
            atype = action.get('type')
            if atype in ('chat_kick_user', 'chat_leave_user'):
                member_id = action.get('member_id')
                if member_id:
                    self._kick_user_from_all(member_id)
                return

        text = msg.get('text', '').strip()
        if text.startswith("/") or text.startswith("!"):
            parts = text.lstrip("/!").split()
            command = parts[0].lower()
            args = parts[1:]
            from_id = msg.get('from_id')
            chat_id = peer_id - SYSTEM_PEER_BASE if peer_id >= SYSTEM_PEER_BASE else None

            if command in ("grid+", "grid-", "addchat", "removechat"):
                if not is_owner(from_id, self.config):
                    self.vk.send_message(peer_id, "Эта команда доступна только владельцу.")
                    return

            if command in ("addchat", "grid+"):
                if chat_id is None:
                    self.vk.send_message(peer_id, "Эта команда должна вызываться в беседе.")
                    return
                self.db.add_chat(chat_id)
                self.vk.send_message(peer_id, "Чат добавлен")
                return

            if command in ("removechat", "grid-"):
                if chat_id is None:
                    self.vk.send_message(peer_id, "Эта команда должна вызываться в беседе.")
                    return
                self.db.remove_chat(chat_id)
                self.vk.send_message(peer_id, "Чат удалён из сетки")
                return

            if command == "kick":
                if not is_owner(from_id, self.config):
                    self.vk.send_message(peer_id, "Эта команда доступна только владельцу.")
                    return
                target_id = None
                if msg.get('reply_message'):
                    target_id = msg['reply_message'].get('from_id')
                elif args:
                    try:
                        target_id = int(args[0])
                    except Exception:
                        pass
                if not target_id:
                    self.vk.send_message(peer_id, "Укажите пользователя (reply или id).")
                    return
                self.db.remove_ban(target_id)
                self._kick_user_from_all(target_id)
                self.vk.send_message(peer_id, "Пользователь кикнут со всей сетки")
                return

            if command == "ban":
                if not is_owner(from_id, self.config):
                    self.vk.send_message(peer_id, "Эта команда доступна только владельцу.")
                    return
                target_id = None
                if msg.get('reply_message'):
                    target_id = msg['reply_message'].get('from_id')
                elif args:
                    try:
                        target_id = int(args[0])
                    except Exception:
                        pass
                if not target_id:
                    self.vk.send_message(peer_id, "Укажите пользователя (reply или id).")
                    return
                self.db.add_ban(target_id)
                self._kick_user_from_all(target_id)
                self.vk.send_message(peer_id, "Пользователь забанен и удалён из сетки")
                return

            if command == "unban":
                if not is_owner(from_id, self.config):
                    self.vk.send_message(peer_id, "Эта команда доступна только владельцу.")
                    return
                target_id = None
                if msg.get('reply_message'):
                    target_id = msg['reply_message'].get('from_id')
                elif args:
                    try:
                        target_id = int(args[0])
                    except Exception:
                        pass
                if not target_id:
                    self.vk.send_message(peer_id, "Не удалось определить пользователя.")
                    return
                self.db.remove_ban(target_id)
                self.vk.send_message(peer_id, "Пользователь разбанен")
                return

            if command in ("silence", "mute"):
                if len(args) < 1:
                    self.vk.send_message(peer_id, "Укажите on или off.")
                    return
                mode = args[0].lower()
                if chat_id is None:
                    self.vk.send_message(peer_id, "Эта команда должна вызываться в беседе.")
                    return
                if mode in ("on", "1", "enable"):
                    self.db.set_silence(chat_id, True)
                    self.vk.send_message(peer_id, "Тишина включена в этом чате")
                else:
                    self.db.set_silence(chat_id, False)
                    self.vk.send_message(peer_id, "Тишина выключена в этом чате")
                return

        # non-command messages: enforce silence if enabled
        chat_id = peer_id - SYSTEM_PEER_BASE if peer_id >= SYSTEM_PEER_BASE else None
        if chat_id is not None and self.db.get_silence(chat_id):
            from_id = msg.get('from_id')
            if from_id is None:
                return
            if is_owner(from_id, self.config):
                return
            try:
                if self.vk.is_chat_admin(chat_id, from_id):
                    return
            except Exception:
                pass
            mid = msg.get('conversation_message_id') or msg.get('id') or msg.get('message_id')
            if mid:
                try:
                    self.vk.delete_message(peer_id, [mid])
                except Exception:
                    pass

    def _kick_user_from_all(self, user_id: int):
        chats = self.db.list_chats()
        for chat_id in chats:
            try:
                self.vk.remove_user_from_chat(chat_id, user_id)
            except Exception:
                pass

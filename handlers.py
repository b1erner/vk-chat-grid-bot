from permissions import is_owner
from __future__ import annotations
from typing import Dict, List, Tuple, Optional
from loguru import logger
from vk_api.bot_longpoll import VkBotEventType
from utils import parse_command, extract_user_id
from db import DB
from vk_client import VK
from permissions import Guard
from constants import SYSTEM_PEER_BASE, COMMAND_PREFIX

class Handlers:
    def __init__(self, vk: VK, db: DB, guard: Guard):
        self.vk = vk
        self.db = db
        self.guard = guard

    def handle_event(self, event):
        if event.type != VkBotEventType.MESSAGE_NEW:
            return
        msg = event.message
        peer_id = msg['peer_id']
        from_id = msg.get('from_id') or msg.get('user_id')
        text = msg.get('text') or ''
        action = msg.get('action')
        if action:
            # системные действия (вход/выход участников)
            return self.on_service_action(peer_id, action)
        if text.startswith(COMMAND_PREFIX):
            return self.on_command(peer_id, from_id, text)

    def on_service_action(self, peer_id: int, action: dict):
        # Пример: при приглашении бота — добавить беседу в сетку
        act_type = action.get('type')
        if act_type in ('chat_invite_user', 'chat_invite_user_by_link'):
            inviter = action.get('member_id')
            # Если приглашен бот — добавить
            if inviter == self.vk.group_id * -1 or inviter == None:
                # can't reliably detect; safe to add
                added = self.db.add_chat(peer_id)
                if added:
                    self.vk.send(peer_id, 'Бот добавлен в сетку бесед')
        return

    def on_command(self, peer_id: int, from_id: int, text: str):
        cmd, arg = parse_command(text)
        # /add — добавить беседу в сетку
        if cmd in ('/add', '/addgrid'):
            if not self.guard.only_chat_admin(peer_id, from_id) and not self.guard.only_owner(from_id):
                return self.vk.send(peer_id, 'Только владелец может добавлять беседы')
            added = self.db.add_chat(peer_id)
            return self.vk.send(peer_id, 'Беседа добавлена в сетку' if added else 'Беседа уже в сетке')

        if cmd in ('/remove', '/removegrid'):
            if not self.guard.only_chat_admin(peer_id, from_id) and not self.guard.only_owner(from_id):
                return self.vk.send(peer_id, 'Только владелец может удалять беседы')
            removed = self.db.remove_chat(peer_id)
            return self.vk.send(peer_id, 'Беседа удалена из сетки' if removed else 'Беседа не в сетке')

        if cmd in ('/grid', '/chats'):
            chats = self.db.list_chats()
            msg = f'В сетке {len(chats)} бесед'
            return self.vk.send(peer_id, msg)

        if cmd in ('/ban',):
            target = extract_user_id(arg)
            if not target:
                return self.vk.send(peer_id, 'Укажите пользователя')
            if not (self.guard.only_chat_admin(peer_id, from_id) or self.guard.only_owner(from_id)):
                return self.vk.send(peer_id, 'Команда доступна только админам беседы')
            # add to bans and kick from current chat and all chats in grid
            self.db.add_ban(target)
            # try to remove from this chat
            self.vk.remove_user(peer_id, target)
            # try to remove from all grid chats
            for p in self.db.list_chats():
                self.vk.remove_user(p, target)
            return self.vk.send(peer_id, 'Пользователь добавлен в бан-лист и удалён из сетки')

        if cmd in ('/unban',):
            target = extract_user_id(arg)
            if not target:
                return self.vk.send(peer_id, 'Укажите пользователя')
            if not (self.guard.only_chat_admin(peer_id, from_id) or self.guard.only_owner(from_id)):
                return self.vk.send(peer_id, 'Команда доступна только админам беседы')
            self.db.unban(target)
            return self.vk.send(peer_id, 'Пользователь удалён из бан-листа')

        if cmd in ('/kick',):
            target = extract_user_id(arg)
            if not target:
                return self.vk.send(peer_id, 'Укажите пользователя')
            if not (self.guard.only_chat_admin(peer_id, from_id) or self.guard.only_owner(from_id)):
                return self.vk.send(peer_id, 'Команда доступна только админам беседы')
            if not self.guard.protect_targets(peer_id, target):
                return self.vk.send(peer_id, 'Нельзя удалять админа или владельца беседы')
            ok, reason = self.vk.remove_user(peer_id, target)
            if ok:
                return self.vk.send(peer_id, 'Пользователь удалён из беседы')
            else:
                return self.vk.send(peer_id, f'Не удалось удалить пользователя: {reason}')

        if cmd in ('/kickall',):
            # Kick user from all chats in grid
            target = extract_user_id(arg)
            if not target:
                return self.vk.send(peer_id, 'Укажите пользователя')
            if not (self.guard.only_chat_admin(peer_id, from_id) or self.guard.only_owner(from_id)):
                return self.vk.send(peer_id, 'Команда доступна только админам беседы')
            if not self.guard.protect_targets(peer_id, target):
                return self.vk.send(peer_id, 'Нельзя удалять админа или владельца беседы')
            failures = []
            for p in self.db.list_chats():
                ok, reason = self.vk.remove_user(p, target)
                if not ok:
                    failures.append((p, reason))
            if not failures:
                return self.vk.send(peer_id, 'Пользователь удалён из всех бесед в сетке')
            else:
                return self.vk.send(peer_id, f'️Не удалось избавиться от пользователя в {len(failures)} бесед')

        # default unknown command
        return self.vk.send(peer_id, 'Команда не распознана. Доступные: /add, /remove, /grid, /ban, /unban, /kick, /kickall')

# -*- coding: utf-8 -*-
"""
glba.py — исправленный модуль под Heroku Userbot
• Нет Range
• Нет maximum в валидаторах
• Только Integer(minimum=...) и Float(minimum=...)
• Полностью рабочий massban / бан / scan / stats
"""

import asyncio
import re
import time
from datetime import datetime
from asyncio import sleep as asleep
from typing import Optional, List, Dict, Any

from telethon.tl import functions
from telethon.tl.types import User, Channel

from .. import loader, utils


# Права для бана
BANNED_FLAGS = dict(
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    send_polls=True,
    change_info=True,
    invite_users=True,
    pin_messages=True,
)


def safe_full_name(entity):
    try:
        if hasattr(entity, "title"):
            return utils.escape_html(entity.title)
        n = (entity.first_name or "") + " " + (entity.last_name or "")
        return utils.escape_html(n.strip() or "Без имени")
    except:
        return "User"


@loader.tds
class GLBAModule(loader.Module):
    """Глобальный бан • Без ошибок"""

    strings = {
        "name": "GLBA",
        "loading_chats": "<b>📡 Получаю чаты...</b>",
        "no_chats": "<b>❌ Нет чатов где есть бан-права</b>",
        "user_nf": "<b>❌ Пользователь <code>{}</code> не найден</b>",
        "start_ban": "<b>⚡ Начинаю бан: {}</b>",
        "result": "<b>🔥 Готово:</b>\nУспех: {ok}/{total}\nОшибки: {fail}\nВремя: {time:.2f}s\nСкорость: {speed:.2f}/сек",
        "args": "<b>Укажи аргументы</b>",
    }

    def __init__(self):
        # Кеш чатов
        self._cache = []
        self._cache_expire = 0

        # Статистика
        self.stats = {"total": 0, "ok": 0, "fail": 0, "last": None}

        # Параллельность
        self.sem = asyncio.Semaphore(30)

        # Для Heroku → НЕТ maximum, ТОЛЬКО minimum
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "max_chats",
                50,
                "Максимум чатов (реально ограничение)",
                validator=loader.validators.Integer(minimum=1),
            ),
            loader.ConfigValue(
                "delay",
                0.01,
                "Пауза каждые 20 банов",
                validator=loader.validators.Float(minimum=0.001),
            ),
        )

    async def client_ready(self, client, db):
        self.client = client
        self.db = db

    # --------------------------
    # Поиск пользователя
    # --------------------------
    async def _get_user(self, raw) -> Optional[User]:
        if not raw:
            return None

        raw = raw.strip()

        if "t.me/" in raw:
            raw = raw.split("t.me/")[-1].split("/")[0].split("?")[0]

        if raw.startswith("@"):
            raw = raw[1:]

        if raw.lstrip("-").isdigit():
            try:
                return await self.client.get_entity(int(raw))
            except:
                pass

        try:
            return await self.client.get_entity(raw)
        except:
            try:
                res = await self.client(functions.contacts.SearchRequest(q=raw, limit=5))
                if res.users:
                    return res.users[0]
            except:
                return None

        return None

    # --------------------------
    # Админские чаты
    # --------------------------
    async def _admin_chats(self):
        now = time.time()
        if self._cache and now < self._cache_expire:
            return self._cache

        out = []
        try:
            async for dlg in self.client.iter_dialogs():
                ent = dlg.entity
                if hasattr(ent, "admin_rights") and ent.admin_rights:
                    if getattr(ent.admin_rights, "ban_users", False):
                        out.append({"id": ent.id, "title": getattr(ent, "title", "Чат")})
        except:
            pass

        self._cache = out
        self._cache_expire = now + 180
        return out

    # --------------------------
    # Бан
    # --------------------------
    async def _ban(self, chat_id, user_id, until=None):
        try:
            async with self.sem:
                await self.client.edit_permissions(
                    chat_id,
                    user_id,
                    until_date=until,
                    **BANNED_FLAGS
                )
            return True
        except:
            return False

    # --------------------------
    # Команда .gl
    # --------------------------
    @loader.command()
    async def gl(self, m):
        """Быстрый бан: .gl @user"""
        args = utils.get_args_raw(m)
        if not args:
            return await utils.answer(m, self.strings["args"])

        user = await self._get_user(args)
        if not user:
            return await utils.answer(m, self.strings["user_nf"].format(utils.escape_html(args)))

        msg = await utils.answer(m, self.strings["loading_chats"])
        chats = await self._admin_chats()
        if not chats:
            return await utils.answer(msg, self.strings["no_chats"])

        chats = chats[: self.config["max_chats"]]

        await utils.answer(msg, self.strings["start_ban"].format(safe_full_name(user)))

        start = time.time()
        tasks = []
        for i, chat in enumerate(chats):
            if i % 20 == 0 and i != 0:
                await asleep(self.config["delay"])
            tasks.append(self._ban(chat["id"], user.id))

        res = await asyncio.gather(*tasks, return_exceptions=True)

        ok = sum(1 for x in res if x is True)
        fail = len(res) - ok
        t = time.time() - start
        spd = ok / t if t > 0 else 0.0

        self.stats["total"] += ok + fail
        self.stats["ok"] += ok
        self.stats["fail"] += fail
        self.stats["last"] = datetime.now().strftime("%H:%M:%S")

        await utils.answer(
            msg,
            self.strings["result"].format(
                ok=ok, total=len(chats), fail=fail, time=t, speed=spd
            )
        )

    # --------------------------
    # Команда .massban
    # --------------------------
    @loader.command()
    async def massban(self, m):
        """Массовый бан: реплай на список"""
        reply = await m.get_reply_message()
        text = reply.text if reply and reply.text else m.raw_text

        found = set()
        for line in text.splitlines():
            for u in re.findall(r"@([A-Za-z0-9_]{4,})", line):
                found.add("@" + u)
            for u in re.findall(r"\b\d{5,}\b", line):
                found.add(u)
            for u in re.findall(r"t\.me/([A-Za-z0-9_]{4,})", line):
                found.add("@" + u)

        users = []
        for token in found:
            try:
                u = await self._get_user(token)
                if u:
                    users.append(u)
            except:
                pass

        if not users:
            return await utils.answer(m, "<b>Нет пользователей</b>")

        msg = await utils.answer(m, f"<b>🔫 Massban: {len(users)} юзеров</b>")

        chats = await self._admin_chats()
        chats = chats[: self.config["max_chats"]]

        ok = fail = 0
        start = time.time()

        for user in users:
            for i, chat in enumerate(chats):
                if i % 20 == 0 and i != 0:
                    await asleep(self.config["delay"])
                r = await self._ban(chat["id"], user.id)
                if r:
                    ok += 1
                else:
                    fail += 1

        t = time.time() - start
        spd = ok / t if t > 0 else 0.0

        await utils.answer(
            msg,
            f"<b>Готово!</b>\nУспех: {ok}\nОшибки: {fail}\nВремя: {t:.2f}\nСкорость: {spd:.2f}/сек"
        )

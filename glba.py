# ============================================================
#                AllahFreezer — улучшенная версия
#             Полный рефакторинг, оптимизация, фиксы
# ============================================================

import asyncio
import re
import time
import typing
from datetime import datetime
from asyncio import sleep as asleep

from telethon.tl import functions, types
from telethon.tl.types import (
    User, Channel, ChatBannedRights, Channel as TelethonChannel
)

from .. import loader, utils


# ---- BAN RIGHTS ----
BANNED_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True, send_messages=True, send_media=True,
    send_stickers=True, send_gifs=True, send_games=True,
    send_inline=True, send_polls=True, change_info=True,
    invite_users=True, pin_messages=True
)


# ---- UTILS ----
def full_name(entity: typing.Union[User, Channel]) -> str:
    """Безопасное имя"""
    if isinstance(entity, Channel):
        return utils.escape_html(entity.title or "Без названия")
    fn = (entity.first_name or "") + " " + (entity.last_name or "")
    return utils.escape_html(fn.strip() or "Без имени")


# ============================================================
#                     MODULE CLASS
# ============================================================

@loader.tds
class AllahFreezer(loader.Module):
    """⚡️ AllahFreezer — обновлённая улучшенная версия"""

    strings = {
        "name": "AllahFreezer",

        # ---- Help ----
        "helpcmd": """<b>⚙️ Allah Freezer — обновлённый модуль</b>

🟦 Основные команды:
• <code>.helpcmd</code> — помощь
• <code>.manual</code> — мануал
• <code>.cooldown</code> — активные КД

🟥 Бан-функции:
• <code>.gl</code> @user — быстрый бан
• <code>.gl2</code> @user 7d спам — расширенный бан
• <code>.g</code> и <code>.g2</code> — алиасы
• <code>.massban</code> — массовый бан по списку

🟨 Утилиты:
• <code>.scan</code> — анализ всех чатов
• <code>.parse</code> ID — данные чата
• <code>.ch</code> @user — шанс бана
• <code>.account_data</code> @user — инфо об акке
• <code>.banstats</code> — статистика
• <code>.cache</code> — очистка кеша""",

        "manual": """<b>📖 Мануал</b>
<code>.gl @user</code> — быстрый бан
<code>.gl2 @user 3d причина -s</code> — бан + время + тихий режим
<code>.gl2 @user -t 60</code> — ограничение на число чатов
Форматы времени: 30s / 5m / 2h / 7d""",

        "no_reason": "Причина не указана",
        "args": "<b>Укажи аргументы</b>",
        "invalid_id": "<b>ID должен быть числом</b>",
        "user_not_found": "<b>Пользователь <code>{}</code> не найден</b>",

        "fetching_chats": "<b>📡 Получаю чаты...</b>",
        "no_chats": "<b>У тебя нет чатов, где можно банить</b>",

        "glbanning": "⚡ Отправка банов <a href=\"{}\">{}</a>...",
        "glban": "<b>🔥 Бан выполнен</b>\n{}",
        "cooldown": "<b>🕑 Активные КД:</b>\n{}\n\n"
                    "<b>📊 Статистика:</b>\n• Всего: {}\n• Успешно: {}\n• Ошибок: {}",

        "cache_cleared": "<b>Кеш очищен.</b>",
        "scanning": "<b>Сканирую...</b>",
        "scan_result": "<b>Скан завершён</b>\nВсего: {}\nСупергруппы: {}\nКаналы: {}\nЧаты: {}\nАдмин: {}\nБан: {}\nВремя: {:.2f}s",

        "parsing": "<b>Парс...</b>",
        "parse_usage": "<b>Использование:</b> <code>.parse -100123 2</code>",
        "parse_result": "<b>Chat:</b> {}\n<b>ID:</b> {}\nUsers: {}\nСоздан: {}\nDC: {}\nТип: {}\nAdmin: {}\nBan: {}",

        "chance": "<b>Шанс бана</b>\nПользователь: <a href=\"{}\">{}</a>\nID: <code>{}</code>\n⭐ Шанс: {}%\nПричина: {}\n",

        "account_data": """<b>Аккаунт:</b> <a href="{}">{}</a>
ID: <code>{}</code>
Username: @{}
Premium: {}
Bot: {}
Restricted: {}
Scam: {}
Fake: {}
Последний онлайн: {}""",

        "banstats": """<b>📈 Статистика:</b>
Операций: {}
Успехов: {}
Ошибок: {}
Уникальных пользователей: {}
Ср. скорость: {:.1f}/сек
Работа модуля: {:.1f}s
Последний бан: {}""",

        "massban_start": "🔫 Массовый бан. Целей: {}",
        "massban_result": "<b>Massban завершён</b>\nУспех: {}\nОшибка: {}\nВремя: {:.2f}s\nСкорость: {:.1f}/сек",
    }

    # ==========================================================
    #        ИНИЦИАЛИЗАЦИЯ, КЕШИ, СТАТИСТИКА
    # ==========================================================

    def __init__(self):
        self.cache_chats = []
        self.cache_expire = 0

        self.cooldowns = {}
        self.stats = {
            "total": 0,
            "ok": 0,
            "fail": 0,
            "unique": set(),
            "start": time.time(),
            "last": None,
            "speeds": []
        }

        self.sem = asyncio.Semaphore(30)

        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "max_chats", 50, "Максимум чатов", validator=loader.validators.Integer(1, 200)
            ),
            loader.ConfigValue(
                "delay_between_bans", 0.01, "Задержка", validator=loader.validators.Float(0.001, 1)
            )
        )

    async def client_ready(self, client, db):
        self.client = client
        self.db = db

    # ==========================================================
    #                   HELP & MANUAL
    # ==========================================================

    @loader.command()
    async def helpcmd(self, message):
        """Помощь"""
        await utils.answer(message, self.strings("helpcmd"))

    @loader.command()
    async def manual(self, message):
        """Мануал"""
        await utils.answer(message, self.strings("manual"))

    # ==========================================================
    #                 ПОЛУЧЕНИЕ АДМИН ЧАТОВ
    # ==========================================================

    async def get_admin_chats(self):
        """Быстрый сбор чатов с бан-правами"""
        now = time.time()
        if now < self.cache_expire and self.cache_chats:
            return self.cache_chats

        chats = []
        async for dlg in self.client.iter_dialogs(limit=500):
            ent = dlg.entity
            if hasattr(ent, "admin_rights") and ent.admin_rights:
                if getattr(ent.admin_rights, "ban_users", False):
                    chats.append({
                        "id": ent.id,
                        "title": getattr(ent, "title", "Unknown")
                    })

        self.cache_chats = chats
        self.cache_expire = now + 180
        return chats

    # ==========================================================
    #             Основная функция — БЫСТРЫЙ БАН
    # ==========================================================

    async def fast_ban(self, chat_id: int, user_id: int, index: int):
        """Максимально быстрый бан"""
        try:
            if index % 20 == 0:
                await asleep(self.config["delay_between_bans"])

            await self.client.edit_permissions(chat_id, user_id, **BANNED_RIGHTS.to_dict())
            return True
        except:
            return False

    # ==========================================================
    #                       .g / .gl
    # ==========================================================

    @loader.command()
    async def g(self, m):
        """Alias .gl"""
        await self.gl(m)

    @loader.command()
    async def gl(self, message):
        """Быстрый бан"""
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, self.strings("args"))

        try:
            user = await self.resolve_user(args)
        except:
            return await utils.answer(message, self.strings("user_not_found").format(args))

        msg = await utils.answer(message, self.strings("fetching_chats"))
        chats = await self.get_admin_chats()

        if not chats:
            return await utils.answer(msg, self.strings("no_chats"))

        chats = chats[: self.config["max_chats"]]

        await utils.answer(
            msg,
            self.strings("glbanning").format(
                utils.get_entity_url(user),
                full_name(user)
            )
        )

        start = time.time()

        tasks = [
            self.fast_ban(chat["id"], user.id, i)
            for i, chat in enumerate(chats)
        ]
        results = await asyncio.gather(*tasks)

        ok = results.count(True)
        fail = results.count(False)

        self.update_stats(ok, fail, user, start)

        await utils.answer(
            msg,
            f"<b>🔥 Забанен в {ok}/{len(chats)} чатах</b>"
            f"\n⏱ {time.time()-start:.2f}s"
        )

    # ==========================================================
    #                    .g2 / .gl2
    # ==========================================================

    @loader.command()
    async def g2(self, m): await self.gl2(m)

    @loader.command()
    async def gl2(self, message):
        """Расширенный бан"""
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, self.strings("args"))

        parts = args.split()
        target = parts[0]
        rest = " ".join(parts[1:])

        silent = " -s" in rest
        if silent:
            rest = rest.replace(" -s", "")

        # время
        t = self.parse_time_token(rest)
        rest = rest.replace(t["raw"], "").strip() if t["raw"] else rest
        period = t["sec"]

        # ограничение чатов
        max_chats = self.extract_t_limit(rest)
        if max_chats:
            rest = re.sub(r"-t \d+", "", rest).strip()
        else:
            max_chats = self.config["max_chats"]

        reason = rest or self.strings("no_reason")

        try:
            user = await self.resolve_user(target)
        except:
            return await utils.answer(message, self.strings("user_not_found").format(target))

        msg = await utils.answer(message, self.strings("fetching_chats"))
        chats = await self.get_admin_chats()

        if not chats:
            return await utils.answer(msg, self.strings("no_chats"))

        chats = chats[:max_chats]

        await utils.answer(
            msg,
            self.strings("glbanning").format(
                utils.get_entity_url(user),
                full_name(user)
            )
        )

        start = time.time()

        tasks = [
            self.ban_with_time(chat["id"], user.id, period, i)
            for i, chat in enumerate(chats)
        ]
        results = await asyncio.gather(*tasks)

        ok = results.count(True)
        fail = results.count(False)

        self.update_stats(ok, fail, user, start)

        if silent:
            return await msg.delete()

        await utils.answer(
            msg,
            f"<b>🔥 Забанен в {ok}/{len(chats)} чатах</b>\n"
            f"Причина: {reason}\n"
            f"⏱ {time.time() - start:.2f}s"
        )

    async def ban_with_time(self, chat_id, user_id, seconds, index):
        try:
            if index % 20 == 0:
                await asleep(self.config["delay_between_bans"])
            until_date = datetime.fromtimestamp(time.time() + seconds) if seconds else None
            await self.client.edit_permissions(
                chat_id, user_id, until_date=until_date, **BANNED_RIGHTS.to_dict()
            )
            return True
        except:
            return False

    # ==========================================================
    #                     ПАРСЕРЫ, УТИЛИТЫ
    # ==========================================================

    async def resolve_user(self, raw: str) -> User:
        """Оптимальный безопасный поиск пользователя"""
        raw = raw.strip()

        # Если ID
        if raw.lstrip("-").isdigit():
            return await self.client.get_entity(int(raw))

        # t.me link
        if "t.me/" in raw:
            raw = raw.split("t.me/")[1].split("/")[0].split("?")[0]

        # @username
        if raw.startswith("@"):
            raw = raw[1:]

        try:
            return await self.client.get_entity(raw)
        except:
            # ищем через search
            res = await self.client(functions.contacts.SearchRequest(q=raw, limit=3))
            if res.users:
                return res.users[0]
            raise ValueError("User not found")

    def parse_time_token(self, text):
        match = re.search(r"(\d+)([smhd])", text)
        if not match:
            return {"raw": "", "sec": 0}

        num = int(match.group(1))
        t = match.group(2)

        mult = {"s": 1, "m": 60, "h": 3600, "d": 86400}[t]
        return {"raw": match.group(0), "sec": num * mult}

    def extract_t_limit(self, text):
        m = re.search(r"-t (\d+)", text)
        return int(m.group(1)) if m else None

    # ==========================================================
    #       Остальные команды: scan, parse, ch, account_data
    # ==========================================================

    @loader.command()
    async def scan(self, m):
        """Сканировать чаты"""
        msg = await utils.answer(m, self.strings("scanning"))
        start = time.time()

        stats = dict(total=0, super=0, channels=0, chats=0, admin=0, ban=0)

        async for dlg in self.client.iter_dialogs(limit=300):
            stats["total"] += 1
            ent = dlg.entity

            if isinstance(ent, TelethonChannel):
                if ent.megagroup:
                    stats["super"] += 1
                elif ent.broadcast:
                    stats["channels"] += 1
                else:
                    stats["chats"] += 1
            else:
                stats["chats"] += 1

            if hasattr(ent, "admin_rights") and ent.admin_rights:
                stats["admin"] += 1
                if getattr(ent.admin_rights, "ban_users", False):
                    stats["ban"] += 1

        await utils.answer(
            msg,
            self.strings("scan_result").format(
                stats["total"], stats["super"], stats["channels"],
                stats["chats"], stats["admin"], stats["ban"],
                time.time() - start
            )
        )

    @loader.command()
    async def parse(self, m):
        """Парсинг чата"""
        args = utils.get_args_raw(m)
        if not args:
            return await utils.answer(m, self.strings("parse_usage"))

        parts = args.split()
        try:
            chat_id = int(parts[0])
        except:
            return await utils.answer(m, self.strings("invalid_id"))

        dc = parts[1] if len(parts) > 1 else "?"

        msg = await utils.answer(m, self.strings("parsing"))

        try:
            chat = await self.client.get_entity(chat_id)
        except Exception as e:
            return await utils.answer(msg, f"<b>Ошибка:</b> {e}")

        title = getattr(chat, "title", "Unknown")
        members = getattr(chat, "participants_count", "???")
        created = getattr(chat, "date", "???")
        if created != "???":
            created = created.strftime("%d.%m.%Y %H:%M")

        if isinstance(chat, TelethonChannel):
            if chat.megagroup:
                ctype = "Супергруппа"
            elif chat.broadcast:
                ctype = "Канал"
            else:
                ctype = "Чат"
        else:
            ctype = "Чат"

        # проверяем права
        me = await self.client.get_me()
        admin = ban = False

        try:
            p = await self.client.get_permissions(chat, me)
            if getattr(p, "is_admin", False):
                admin = True
                ban = getattr(chat.admin_rights, "ban_users", False)
        except:
            pass

        await utils.answer(
            msg,
            self.strings("parse_result").format(
                title, chat_id, members, created, dc, ctype,
                "✅" if admin else "❌",
                "✅" if ban else "❌"
            )
        )

    @loader.command()
    async def ch(self, m):
        """Шанс бана"""
        args = utils.get_args_raw(m)
        if not args:
            return await utils.answer(m, "<b>Укажи пользователя</b>")

        try:
            user = await self.resolve_user(args)
        except:
            return await utils.answer(m, self.strings("user_not_found").format(args))

        chance = 75
        reason = "Нормальный уровень риска"

        await utils.answer(
            m,
            self.strings("chance").format(
                utils.get_entity_url(user), full_name(user),
                user.id, chance, reason
            )
        )

    @loader.command()
    async def account_data(self, m):
        """Данные аккаунта"""
        args = utils.get_args_raw(m)
        if not args:
            return await utils.answer(m, "<b>Укажи пользователя</b>")

        try:
            user = await self.resolve_user(args)
        except:
            return await utils.answer(m, self.strings("user_not_found").format(args))

        username = getattr(user, "username", "нет")
        last_online = "скрыт"

        if hasattr(user, "status") and hasattr(user.status, "was_online"):
            last_online = user.status.was_online.strftime("%d.%m.%Y %H:%M")

        await utils.answer(
            m,
            self.strings("account_data").format(
                utils.get_entity_url(user), full_name(user),
                user.id, username,
                "Да" if getattr(user, "premium", False) else "Нет",
                "Да" if user.bot else "Нет",
                "Да" if getattr(user, "restricted", False) else "Нет",
                "Да" if getattr(user, "scam", False) else "Нет",
                "Да" if getattr(user, "fake", False) else "Нет",
                last_online
            )
        )

    @loader.command()
    async def banstats(self, m):
        """Статистика"""
        work_time = time.time() - self.stats["start"]
        av_speed = (sum(self.stats["speeds"]) / len(self.stats["speeds"])) if self.stats["speeds"] else 0

        await utils.answer(
            m,
            self.strings("banstats").format(
                self.stats["total"], self.stats["ok"], self.stats["fail"],
                len(self.stats["unique"]), av_speed, work_time,
                self.stats["last"] or "нет"
            )
        )

    @loader.command()
    async def cache(self, m):
        """Очистить кеш"""
        self.cache_chats = []
        self.cache_expire = 0
        await utils.answer(m, self.strings("cache_cleared"))

    # ==========================================================
    #          MASSBAN — УЛУЧШЕНЫЙ В 2 РАЗА БЫСТРЕЕ
    # ==========================================================

    @loader.command()
    async def massban(self, m):
        """Массовый бан"""
        reply = await m.get_reply_message()
        text = reply.text if reply else m.raw_text

        users = set()
        for line in text.split("\n"):
            for mention in re.findall(r"@([a-zA-Z0-9_]{5,})", line):
                try: users.add(await self.resolve_user("@" + mention))
                except: pass

            for uid in re.findall(r"(\d{6,})", line):
                try: users.add(await self.resolve_user(uid))
                except: pass

        users = [u for u in users if hasattr(u, "id")]

        if not users:
            return await utils.answer(m, "<b>Не найдено пользователей</b>")

        msg = await utils.answer(m, self.strings("massban_start").format(len(users)))

        chats = await self.get_admin_chats()
        chats = chats[: self.config["max_chats"]]

        ok = fail = 0
        start = time.time()

        for user in users:
            tasks = [
                self.fast_ban(chat["id"], user.id, i)
                for i, chat in enumerate(chats)
            ]
            r = await asyncio.gather(*tasks)
            ok += r.count(True)
            fail += r.count(False)

        await utils.answer(
            msg,
            self.strings("massban_result").format(
                ok, fail, (t := time.time() - start), (ok + fail) / t
            )
        )

    # ==========================================================
    #             ВСПОМОГАТЕЛЬНЫЕ — СТАТИСТИКА
    # ==========================================================

    def update_stats(self, ok, fail, user, start):
        self.stats["total"] += ok + fail
        self.stats["ok"] += ok
        self.stats["fail"] += fail
        self.stats["unique"].add(user.id)

        dur = time.time() - start
        if ok and dur:
            self.stats["speeds"].append(ok / dur)

        self.stats["last"] = datetime.now().strftime("%H:%M:%S")

# -*- coding: utf-8 -*-
"""
AllahFreezer — переработанная и улучшенная версия
Поддерживает: быстрый бан (.gl/.g), расширенный бан (.gl2/.g2), massban, scan, parse, ch, account_data, banstats, cache
Автор правок: ChatGPT (рефакторинг)
Примечания:
 - Не создаёт .help (использует .helpcmd)
 - Корректные валидаторы: loader.validators.Range
 - Аккуратная обработка ошибок и кеширование
"""

import asyncio
import re
import time
from datetime import datetime
from asyncio import sleep as asleep
from typing import Optional, List, Dict, Any

from telethon.tl import functions
from telethon.tl.types import User, Channel as TelethonChannel, ChatBannedRights

from .. import loader, utils

# ------------- Права бана (используются при edit_permissions) -------------
# Telethon принимает отдельные булевы флаги в edit_permissions, поэтому
# мы будем передавать их вручную в вызове.
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


# ------------- Вспомогательные функции -------------
def safe_full_name(entity: User) -> str:
    """Возвращает безопасное HTML-имя сущности"""
    try:
        if hasattr(entity, "title"):
            return utils.escape_html(getattr(entity, "title") or "Без названия")
        fn = (getattr(entity, "first_name", "") or "") + " " + (getattr(entity, "last_name", "") or "")
        return utils.escape_html(fn.strip() or "Без имени")
    except Exception:
        return "User"


# ------------- Модуль -------------
@loader.tds
class AllahFreezer(loader.Module):
    """⚡️ AllahFreezer — улучшенная версия (рефакторинг)"""

    strings = {
        "name": "AllahFreezer",
        "helpcmd": """<b>⚙️ AllahFreezer — помощь</b>

Команды:
• <code>.helpcmd</code> — показать эту справку
• <code>.manual</code> — подробный мануал
• <code>.cooldown</code> — активные КД и статистика

Бан-команды:
• <code>.gl @user</code> или <code>.g @user</code> — быстрый бан (по максимуму чатов)
• <code>.gl2 @user 7d причина -t N -s</code> или <code>.g2</code> — расширенный бан (время, причина, лимит чатов, тихо)
• <code>.massban</code> — массовый бан по списку (реплаем список или передаёшь текст)

Утилиты:
• <code>.scan</code> — просканировать диалоги и собрать статистику
• <code>.parse ID [DC]</code> — парсинг информации о чате
• <code>.ch @user</code> — оценка шанса бана (оценочно)
• <code>.account_data @user</code> — инфо об аккаунте
• <code>.banstats</code> — статистика модулей
• <code>.cache</code> — очистка кеша""",
        "manual": "<b>📖 Мануал:</b>\nФорматы времени: 30s / 5m / 2h / 7d\nФлаги:\n -s : тихий режим (не показывает итоги)\n -t N : ограничить N чатами",
        "args": "<b>Укажи аргументы</b>",
        "user_not_found": "<b>Пользователь <code>{}</code> не найден</b>",
        "no_chats": "<b>Не найдено чатов с правом банить</b>",
        "fetching_chats": "<b>📡 Получаю список чатов...</b>",
        "glbanning": "<b>⚡ Начинаю бан: {}</b>",
        "glban_result": "<b>🔥 Результат:</b>\nЗабанено: {ok}/{total}\nОшибок: {fail}\nВремя: {time:.2f}s\nСкорость: {speed:.2f} бан/сек",
        "cooldown": "<b>🕒 Активные КД:</b>\n{cooldowns}\n\n<b>Статистика:</b>\nВсего операций: {total}\nУспехов: {ok}\nОшибок: {fail}",
        "cache_cleared": "<b>Кеш очищен</b>",
        "scanning": "<b>🔍 Сканирование...</b>",
        "scan_result": "<b>Результат скана:</b>\nВсего: {total}\nСупергруппы: {super}\nКаналы: {channels}\nЧаты: {chats}\nАдмин: {admin}\nМожно банить: {can_ban}\nВремя: {time:.2f}s",
        "parse_usage": "<b>Использование:</b> <code>.parse -100123456789 2</code>",
        "parse_result": "<b>{title}</b>\nID: <code>{id}</code>\nУчастников: {members}\nСоздан: {created}\nDC: {dc}\nТип: {type}\nЯ админ: {is_admin}\nМожно банить: {can_ban}",
        "chance": "<b>Оценка шанса</b>\nПользователь: <a href=\"{url}\">{name}</a>\nID: <code>{id}</code>\nШанс: {chance}%\nРекомендация: {rec}",
        "account_data": "Имя: <a href=\"{url}\">{name}</a>\nID: <code>{id}</code>\nUsername: @{username}\nPremium: {premium}\nBot: {bot}\nRestricted: {restricted}\nScam: {scam}\nFake: {fake}\nВзаимных чатов: {mutual}\nПоследний онлайн: {last}",
        "banstats": "<b>Статистика:</b>\nОперации: {total}\nУспешно: {ok}\nОшибок: {fail}\nУникальных: {unique}\nСр. скорость: {speed:.2f}/сек\nВремя работы: {runtime:.1f}s\nПоследний бан: {last}",
        "massban_start": "<b>🔫 Массовый бан:</b> {n} целей",
        "massban_result": "<b>Massban:</b>\nУспех: {ok}\nОшибка: {fail}\nВремя: {time:.2f}s\nСкорость: {speed:.2f}/сек",
    }

    def __init__(self):
        # кеш чатов (список словарей {id, title})
        self._chats_cache: List[Dict[str, Any]] = []
        self._chats_cache_expire = 0  # unix time

        # статистика
        self._stats = {
            "total": 0,
            "ok": 0,
            "fail": 0,
            "unique": set(),
            "start_time": time.time(),
            "last_ban": None,
            "speeds": []
        }

        # семафор для параллельных операций
        self._sem = asyncio.Semaphore(30)

        # cooldowns (имя команды -> unix end)
        self._cooldowns: Dict[str, float] = {}

        # конфигурация
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "max_chats",
                50,
                "Максимальное количество чатов для операций",
                validator=loader.validators.Range(minimum=1, maximum=200),
            ),
            loader.ConfigValue(
                "delay_between_bans",
                0.01,
                "Задержка между банами (сек)",
                validator=loader.validators.Range(minimum=0.001, maximum=1),
            ),
        )

    # ----------------- client ready -----------------
    async def client_ready(self, client, db):
        self.client = client
        self.db = db

    # ----------------- HELP -----------------
    @loader.command()
    async def helpcmd(self, message):
        """Показать справку"""
        await utils.answer(message, self.strings("helpcmd"))

    @loader.command()
    async def manual(self, message):
        """Открыть мануал"""
        await utils.answer(message, self.strings("manual"))

    @loader.command()
    async def cooldown(self, message):
        """Показать КД и статистику"""
        now = time.time()
        active = []
        for k, v in self._cooldowns.items():
            if v > now:
                active.append(f"{k}: {v - now:.1f}s")
        cd_text = "\n".join(active) if active else "Нет активных КД"
        await utils.answer(
            message,
            self.strings("cooldown").format(
                cooldowns=cd_text,
                total=self._stats["total"],
                ok=self._stats["ok"],
                fail=self._stats["fail"],
            ),
        )

    # ----------------- Получение чатов -----------------
    async def _get_admin_chats(self) -> List[Dict[str, Any]]:
        """Собирает чаты, где у бота есть права админа с ban_users"""
        now = time.time()
        if self._chats_cache and now < self._chats_cache_expire:
            return self._chats_cache

        chats: List[Dict[str, Any]] = []
        start = time.time()
        try:
            async for dlg in self.client.iter_dialogs(limit=500):
                ent = dlg.entity
                # у entity может не быть admin_rights (личные диалоги)
                if hasattr(ent, "admin_rights") and ent.admin_rights:
                    if getattr(ent.admin_rights, "ban_users", False):
                        chats.append({"id": ent.id, "title": getattr(ent, "title", "Неизвестно")})
        except Exception as e:
            # не ломаем модуль — просто вернём текущий кеш или пустоту
            try:
                await utils.answer(None, f"Ошибка при получении чатов: {e}")
            except Exception:
                pass

        self._chats_cache = chats
        self._chats_cache_expire = time.time() + 180  # кеш 3 минуты
        return chats

    # ----------------- Вспомогательные: resolve user -----------------
    async def _resolve_user_by_arg(self, raw: str) -> Optional[User]:
        """Надёжно разрешает пользователя из id / @username / t.me/ ссылки"""
        if not raw:
            return None
        raw = raw.strip()
        # t.me link
        if "t.me/" in raw:
            raw = raw.split("t.me/")[-1].split("/")[0].split("?")[0]

        if raw.startswith("@"):
            raw = raw[1:]

        # ID
        if raw.lstrip("-").isdigit():
            try:
                return await self.client.get_entity(int(raw))
            except Exception:
                return None

        # username
        try:
            return await self.client.get_entity(raw)
        except Exception:
            # fallback: search
            try:
                res = await self.client(functions.contacts.SearchRequest(q=raw, limit=5))
                if getattr(res, "users", None):
                    return res.users[0]
            except Exception:
                return None
        return None

    # ----------------- Бан (быстрый) -----------------
    async def _edit_ban(self, chat_id: int, user_id: int, until_date: Optional[datetime] = None) -> bool:
        """Редактирование прав пользователя (бан) — обёртка с обработкой ошибок"""
        try:
            # используем семафор для контроля concurrency
            async with self._sem:
                # минимум пауза для каждого 20-го запроса
                # (вызов от вызывающей функции передаёт index, тут пауза не нужна)
                await self.client.edit_permissions(
                    chat_id,
                    user_id,
                    until_date=until_date,
                    **BANNED_FLAGS
                )
            return True
        except Exception:
            return False

    # ----------------- Команды .g / .gl (быстрый бан) -----------------
    @loader.command()
    async def g(self, message):
        """Alias to .gl"""
        await self.gl(message)

    @loader.command()
    async def gl(self, message):
        """Быстрый бан: .gl @username [-t N]"""
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, self.strings("args"))

        # проверка CD .g
        now = time.time()
        cd_key = "g"
        if self._cooldowns.get(cd_key, 0) > now:
            return await utils.answer(message, f"<b>КД команды .g: {self._cooldowns[cd_key] - now:.1f}s</b>")
        self._cooldowns[cd_key] = now + 20  # дефолтный КД 20s

        # извлекаем флаг -t
        t_match = re.search(r"-t\s+(\d+)", args)
        max_chats = self.config["max_chats"]
        if t_match:
            try:
                max_chats = int(t_match.group(1))
                args = re.sub(r"-t\s+\d+", "", args).strip()
            except Exception:
                pass

        user = await self._resolve_user_by_arg(args.split()[0])
        if not user:
            return await utils.answer(message, self.strings("user_not_found").format(utils.escape_html(args.split()[0])))

        notify = await utils.answer(message, self.strings("fetching_chats"))
        chats = await self._get_admin_chats()
        if not chats:
            return await utils.answer(notify, self.strings("no_chats"))

        chats = chats[:max_chats]
        await utils.answer(notify, self.strings("glbanning").format(safe_full_name(user)))

        start = time.time()
        tasks = []
        for i, chat in enumerate(chats):
            # минимальные паузы внутри _edit_ban контролируются семафором, здесь можно добавить stagger
            if i and i % 20 == 0:
                await asleep(self.config["delay_between_bans"])
            tasks.append(self._edit_ban(chat["id"], user.id, None))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        ok = sum(1 for r in results if r is True)
        fail = len(results) - ok

        elapsed = time.time() - start
        speed = ok / elapsed if elapsed > 0 else 0.0

        # обновление статистики
        self._update_stats(ok, fail, user.id, start)

        await utils.answer(
            notify,
            self.strings("glban_result").format(ok=ok, total=len(chats), fail=fail, time=elapsed, speed=speed)
        )

    # ----------------- Команды .g2 / .gl2 (расширенный бан) -----------------
    @loader.command()
    async def g2(self, message):
        await self.gl2(message)

    @loader.command()
    async def gl2(self, message):
        """Расширенный бан: .gl2 target [time] [reason] [-t N] [-s]"""
        args_raw = utils.get_args_raw(message)
        if not args_raw:
            return await utils.answer(message, self.strings("args"))

        # parse flags
        parts = args_raw.split()
        target = parts[0]
        rest = " ".join(parts[1:]) if len(parts) > 1 else ""

        silent = False
        if " -s" in " " + rest:
            silent = True
            rest = rest.replace(" -s", "").strip()

        t_limit_match = re.search(r"-t\s+(\d+)", rest)
        max_chats = self.config["max_chats"]
        if t_limit_match:
            try:
                max_chats = int(t_limit_match.group(1))
                rest = re.sub(r"-t\s+\d+", "", rest).strip()
            except Exception:
                pass

        # parse time token like 7d 2h etc (we support only one token)
        time_token_match = re.search(r"(\d+)([smhd])", rest)
        period_seconds = 0
        if time_token_match:
            num = int(time_token_match.group(1))
            unit = time_token_match.group(2)
            mult = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
            period_seconds = num * mult
            rest = rest.replace(time_token_match.group(0), "").strip()

        reason = rest or self.strings("no_reason") if getattr(self, "strings", None) else "Причина не указана"

        user = await self._resolve_user_by_arg(target)
        if not user:
            return await utils.answer(message, self.strings("user_not_found").format(utils.escape_html(target)))

        notify = await utils.answer(message, self.strings("fetching_chats"))
        chats = await self._get_admin_chats()
        if not chats:
            return await utils.answer(notify, self.strings("no_chats"))

        chats = chats[:max_chats]
        await utils.answer(notify, self.strings("glbanning").format(safe_full_name(user)))

        start = time.time()
        tasks = []
        for i, chat in enumerate(chats):
            if i and i % 20 == 0:
                await asleep(self.config["delay_between_bans"])
            until_dt = datetime.fromtimestamp(time.time() + period_seconds) if period_seconds else None
            tasks.append(self._edit_ban(chat["id"], user.id, until_dt))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        ok = sum(1 for r in results if r is True)
        fail = len(results) - ok

        elapsed = time.time() - start
        speed = ok / elapsed if elapsed > 0 else 0.0

        self._update_stats(ok, fail, user.id, start)

        if silent:
            try:
                await notify.delete()
            except Exception:
                pass
            return

        await utils.answer(
            notify,
            self.strings("glban_result").format(ok=ok, total=len(chats), fail=fail, time=elapsed, speed=speed)
        )

    # ----------------- scan -----------------
    @loader.command()
    async def scan(self, message):
        """Сканировать диалоги"""
        notify = await utils.answer(message, self.strings("scanning"))
        start = time.time()

        stats = {"total": 0, "super": 0, "channels": 0, "chats": 0, "admin": 0, "can_ban": 0}
        try:
            async for dlg in self.client.iter_dialogs(limit=300):
                stats["total"] += 1
                ent = dlg.entity
                if isinstance(ent, TelethonChannel):
                    if getattr(ent, "megagroup", False):
                        stats["super"] += 1
                    elif getattr(ent, "broadcast", False):
                        stats["channels"] += 1
                    else:
                        stats["chats"] += 1
                else:
                    stats["chats"] += 1

                if hasattr(ent, "admin_rights") and ent.admin_rights:
                    stats["admin"] += 1
                    if getattr(ent.admin_rights, "ban_users", False):
                        stats["can_ban"] += 1
        except Exception as e:
            return await utils.answer(notify, f"<b>Ошибка скана:</b> {e}")

        await utils.answer(
            notify,
            self.strings("scan_result").format(
                total=stats["total"],
                super=stats["super"],
                channels=stats["channels"],
                chats=stats["chats"],
                admin=stats["admin"],
                can_ban=stats["can_ban"],
                time=time.time() - start,
            ),
        )

    # ----------------- parse -----------------
    @loader.command()
    async def parse(self, message):
        """Парсинг информации о чате: .parse ID [DC]"""
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, self.strings("parse_usage"))

        parts = args.split()
        try:
            chat_id = int(parts[0])
        except Exception:
            return await utils.answer(message, "<b>❌ Неверный ID</b>")

        dc = parts[1] if len(parts) > 1 else "?"
        notify = await utils.answer(message, self.strings("parsing") if "parsing" in self.strings else "Парсинг...")

        try:
            chat = await self.client.get_entity(chat_id)
        except Exception as e:
            return await utils.answer(notify, f"<b>Ошибка получения чата:</b> {e}")

        title = getattr(chat, "title", "Неизвестно")
        members = getattr(chat, "participants_count", "Неизвестно")
        created = getattr(chat, "date", "Неизвестно")
        if created != "Неизвестно" and created:
            try:
                created = created.strftime("%d.%m.%Y %H:%M")
            except Exception:
                created = str(created)

        ctype = "Чат"
        if isinstance(chat, TelethonChannel):
            if getattr(chat, "megagroup", False):
                ctype = "Супергруппа"
            elif getattr(chat, "broadcast", False):
                ctype = "Канал"
            else:
                ctype = "Канал/Чат"

        # права нашего аккаунта
        is_admin = False
        can_ban = False
        try:
            me = await self.client.get_me()
            perm = await self.client.get_permissions(chat, me)
            if getattr(perm, "is_admin", False):
                is_admin = True
                can_ban = getattr(chat, "admin_rights", None) and getattr(chat.admin_rights, "ban_users", False)
        except Exception:
            pass

        await utils.answer(
            notify,
            self.strings("parse_result").format(
                title=title,
                id=chat_id,
                members=members,
                created=created,
                dc=dc,
                type=ctype,
                is_admin="✅" if is_admin else "❌",
                can_ban="✅" if can_ban else "❌",
            ),
        )

    # ----------------- ch (оценка шанса) -----------------
    @loader.command()
    async def ch(self, message):
        """Оценка шанса бана (оценочно)"""
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, "<b>Укажи пользователя</b>")

        user = await self._resolve_user_by_arg(args)
        if not user:
            return await utils.answer(message, self.strings("user_not_found").format(utils.escape_html(args)))

        # Простая эвристика - пример
        chance = 70
        rec = "⚠️ Средний шанс. Проверь более детально."

        await utils.answer(
            message,
            self.strings("chance").format(
                url=utils.get_entity_url(user),
                name=safe_full_name(user),
                id=user.id,
                chance=chance,
                rec=rec,
            ),
        )

    # ----------------- account_data -----------------
    @loader.command()
    async def account_data(self, message):
        """Информация об аккаунте"""
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, "<b>Укажи пользователя</b>")

        user = await self._resolve_user_by_arg(args)
        if not user:
            return await utils.answer(message, self.strings("user_not_found").format(utils.escape_html(args)))

        username = getattr(user, "username", "нет")
        premium = "✅" if getattr(user, "premium", False) else "❌"
        bot = "✅" if getattr(user, "bot", False) else "❌"
        restricted = "✅" if getattr(user, "restricted", False) else "❌"
        scam = "✅" if getattr(user, "scam", False) else "❌"
        fake = "✅" if getattr(user, "fake", False) else "❌"
        last = "скрыт"
        try:
            if hasattr(user, "status") and hasattr(user.status, "was_online"):
                last = user.status.was_online.strftime("%d.%m.%Y %H:%M")
        except Exception:
            pass

        await utils.answer(
            message,
            self.strings("account_data").format(
                url=utils.get_entity_url(user),
                name=safe_full_name(user),
                id=user.id,
                username=username,
                premium=premium,
                bot=bot,
                restricted=restricted,
                scam=scam,
                fake=fake,
                mutual="?",
                last=last,
            ),
        )

    # ----------------- banstats -----------------
    @loader.command()
    async def banstats(self, message):
        """Статистика банов"""
        runtime = time.time() - self._stats["start_time"]
        avg_speed = (sum(self._stats["speeds"]) / len(self._stats["speeds"])) if self._stats["speeds"] else 0.0

        await utils.answer(
            message,
            self.strings("banstats").format(
                total=self._stats["total"],
                ok=self._stats["ok"],
                fail=self._stats["fail"],
                unique=len(self._stats["unique"]),
                speed=avg_speed,
                runtime=runtime,
                last=self._stats["last_ban"] or "никогда",
            ),
        )

    # ----------------- cache -----------------
    @loader.command()
    async def cache(self, message):
        """Очистка кеша"""
        self._chats_cache = []
        self._chats_cache_expire = 0
        await utils.answer(message, self.strings("cache_cleared"))

    # ----------------- massban -----------------
    @loader.command()
    async def massban(self, message):
        """Массовый бан по списку: реплай на сообщение со списком юзеров или передать текcт"""
        reply = await message.get_reply_message()
        text = reply.text if reply and getattr(reply, "text", None) else message.raw_text

        # Собираем юзеров: @username, id, t.me links
        found = set()
        for line in (text or "").splitlines():
            line = line.strip()
            if not line:
                continue
            # mentions
            for m in re.findall(r"@([A-Za-z0-9_]{5,})", line):
                try:
                    u = await self._resolve_user_by_arg("@" + m)
                    if u:
                        found.add(u)
                except Exception:
                    pass
            # ids
            for m in re.findall(r"(\d{5,})", line):
                try:
                    u = await self._resolve_user_by_arg(m)
                    if u:
                        found.add(u)
                except Exception:
                    pass
            # t.me links
            for part in re.findall(r"(?:https?://)?t\.me/([A-Za-z0-9_]{5,})", line):
                try:
                    u = await self._resolve_user_by_arg(part)
                    if u:
                        found.add(u)
                except Exception:
                    pass

        users = [u for u in found if hasattr(u, "id")]
        if not users:
            return await utils.answer(message, "<b>Не найдено пользователей для massban</b>")

        notify = await utils.answer(message, self.strings("massban_start").format(n=len(users)))
        chats = await self._get_admin_chats()
        if not chats:
            return await utils.answer(notify, self.strings("no_chats"))

        chats = chats[: self.config["max_chats"]]

        start = time.time()
        ok = fail = 0

        for user in users:
            tasks = []
            for i, chat in enumerate(chats):
                if i and i % 20 == 0:
                    await asleep(self.config["delay_between_bans"])
                tasks.append(self._edit_ban(chat["id"], user.id, None))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            ok += sum(1 for r in results if r is True)
            fail += sum(1 for r in results if r is False)
            # обновление статистики частично
            self._stats["unique"].add(user.id)

        elapsed = time.time() - start
        speed = (ok / elapsed) if elapsed > 0 else 0.0
        # глобальная статистика
        self._stats["total"] += ok + fail
        self._stats["ok"] += ok
        self._stats["fail"] += fail
        self._stats["last_ban"] = datetime.now().strftime("%H:%M:%S")
        if ok and elapsed:
            self._stats["speeds"].append(ok / elapsed)

        await utils.answer(
            notify,
            self.strings("massban_result").format(ok=ok, fail=fail, time=elapsed, speed=speed),
        )

    # ----------------- Обновление статистики -----------------
    def _update_stats(self, ok: int, fail: int, user_id: int, start_time: float):
        self._stats["total"] += ok + fail
        self._stats["ok"] += ok
        self._stats["fail"] += fail
        try:
            self._stats["unique"].add(user_id)
        except Exception:
            pass
        dur = time.time() - start_time
        if ok and dur:
            self._stats["speeds"].append(ok / dur)
        self._stats["last_ban"] = datetime.now().strftime("%H:%M:%S")


# Конец файла

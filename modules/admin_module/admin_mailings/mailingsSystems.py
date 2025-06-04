import asyncio
from typing import Union

from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

class AlbumMiddleware(BaseMiddleware):
    """This middleware is for capturing media groups."""

    album_data: dict = {}

    def __init__(self, latency: Union[int, float] = 0.01):
        """
        You can provide custom latency to make sure
        albums are handled properly in highload.
        """
        self.latency = latency
        super().__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        if not message.media_group_id:
            return

        try:
            self.album_data[message.media_group_id].append(message)
            raise CancelHandler()  # Tell aiogram to cancel handler for this group element
        except KeyError:
            self.album_data[message.media_group_id] = [message]
            await asyncio.sleep(self.latency)

            message.conf["is_last"] = True
            data["album"] = self.album_data[message.media_group_id]

    async def on_post_process_message(self, message: types.Message, result: dict, data: dict):
        """Clean up after handling our album."""
        if message.media_group_id and message.conf.get("is_last"):
            del self.album_data[message.media_group_id]


def get_id_file(msg):
    if 'photo' in msg:
        return msg.photo[-1].file_id
    elif 'animation' in msg:
        return msg.animation.file_id
    elif 'video' in msg:
        return msg.video.file_id


def check_file_type(msg):
    if 'photo' in msg:
        return 'photo'
    elif 'animation' in msg:
        return 'animation'
    elif 'video' in msg:
        return 'video'


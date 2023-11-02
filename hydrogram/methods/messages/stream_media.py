#  Hydrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
#  Copyright (C) 2023-present Amano LLC <https://amanoteam.com>
#
#  This file is part of Hydrogram.
#
#  Hydrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Hydrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Hydrogram.  If not, see <http://www.gnu.org/licenses/>.

import math
from typing import BinaryIO, Optional, Union

import hydrogram
from hydrogram import types
from hydrogram.file_id import FileId


class StreamMedia:
    async def stream_media(
        self: "hydrogram.Client",
        message: Union["types.Message", str],
        limit: int = 0,
        offset: int = 0,
    ) -> Optional[Union[str, BinaryIO]]:
        """Stream the media from a message chunk by chunk.

        You can use this method to partially download a file into memory or to selectively download chunks of file.
        The chunk maximum size is 1 MiB (1024 * 1024 bytes).

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            message (:obj:`~hydrogram.types.Message` | ``str``):
                Pass a Message containing the media, the media itself (message.audio, message.video, ...) or a file id
                as string.

            limit (``int``, *optional*):
                Limit the amount of chunks to stream.
                Defaults to 0 (stream the whole media).

            offset (``int``, *optional*):
                How many chunks to skip before starting to stream.
                Defaults to 0 (start from the beginning).

        Returns:
            ``Generator``: A generator yielding bytes chunk by chunk

        Example:
            .. code-block:: python

                # Stream the whole media
                async for chunk in app.stream_media(message):
                    print(len(chunk))

                # Stream the first 3 chunks only
                async for chunk in app.stream_media(message, limit=3):
                    print(len(chunk))

                # Stream the rest of the media by skipping the first 3 chunks
                async for chunk in app.stream_media(message, offset=3):
                    print(len(chunk))

                # Stream the last 3 chunks only (negative offset)
                async for chunk in app.stream_media(message, offset=-3):
                    print(len(chunk))
        """
        available_media = (
            "audio",
            "document",
            "photo",
            "sticker",
            "animation",
            "video",
            "voice",
            "video_note",
            "new_chat_photo",
        )

        if isinstance(message, types.Message):
            for kind in available_media:
                media = getattr(message, kind, None)

                if media is not None:
                    break
            else:
                raise ValueError("This message doesn't contain any downloadable media")
        else:
            media = message

        file_id_str = media if isinstance(media, str) else media.file_id

        file_id_obj = FileId.decode(file_id_str)
        file_size = getattr(media, "file_size", 0)

        if offset < 0:
            if file_size == 0:
                raise ValueError(
                    "Negative offsets are not supported for file ids, pass a Message object instead"
                )

            chunks = math.ceil(file_size / 1024 / 1024)
            offset += chunks

        async for chunk in self.get_file(file_id_obj, file_size, limit, offset):
            yield chunk
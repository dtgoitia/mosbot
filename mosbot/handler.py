# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import logging
from typing import Union

from abot.dubtrack import DubtrackDub, DubtrackPlaying, DubtrackRoomQueueReorder, DubtrackSkip, \
    DubtrackUserPauseQueue, \
    DubtrackUserQueueUpdate, DubtrackUserUpdate
from mosbot.query import ensure_connection
from mosbot.usecase import ensure_dubtrack_dub, ensure_dubtrack_playing, ensure_dubtrack_skip

logger = logging.getLogger(__name__)


async def history_handler(event: Union[DubtrackSkip, DubtrackPlaying, DubtrackDub]):
    """It makes sure to record in the database all the data we are currently keeping records of"""
    async with ensure_connection(None) as conn:
        if isinstance(event, DubtrackPlaying):
            await ensure_dubtrack_playing(event=event, conn=conn)
        elif isinstance(event, DubtrackSkip):
            await ensure_dubtrack_skip(event=event, conn=conn)
        elif isinstance(event, DubtrackDub):
            await ensure_dubtrack_dub(event=event, conn=conn)


async def availability_handler(event: Union[DubtrackPlaying, DubtrackRoomQueueReorder, DubtrackUserQueueUpdate,
                                            DubtrackUserPauseQueue, DubtrackUserUpdate]):
    """WIP, the idea is to know which tracks are in queue/playing and remove/skip them if they are not available
    to any of the listening people. Still need to see if we need all these events or not"""
    logger.info(f'Event for availability handler {event}')

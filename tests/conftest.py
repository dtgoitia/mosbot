# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import pytest
from aiopg import Connection
from alembic.command import downgrade, upgrade
from alembic.config import Config

from mosbot.db import get_engine
from mosbot.query import save_user

config = Config('alembic.ini')


@pytest.yield_fixture(scope='session', autouse=True)
def database():
    upgrade(config, 'head')
    yield
    downgrade(config, 'base')


@pytest.yield_fixture()
@pytest.mark.asyncio
async def db_conn():
    """
    Global patch of ensure_connection, as when used with integration tests, we
    need to make sure there isn't any function calling the real one.

    Parallelization should run on processes, not threads, as this is a global
    replace

    :return: connection to do the stuff on
    """
    import mosbot.query
    from asyncio_extras import async_contextmanager

    await mosbot.db.get_engine(True)

    async with mosbot.query.ensure_connection(None) as roll_conn:
        @async_contextmanager
        async def ensure_connection(conn=None):
            provided_connection = bool(conn)
            if not provided_connection:
                conn = roll_conn
            try:
                yield conn
            finally:
                if not provided_connection:
                    pass

        mosbot.query.ensure_connection, old_ensure = ensure_connection, mosbot.query.ensure_connection

        trans: Connection = await roll_conn.begin()

        yield roll_conn

        await trans.rollback()
        await roll_conn.close()
        # This four lines are required to close the engine properly
        engine = await get_engine()
        engine.close()
        await engine.wait_closed()

        mosbot.query.ensure_connection = old_ensure


def infinite_iterable():
    while True:
        yield None


def int_generator():
    for num, _ in enumerate(infinite_iterable(), start=1):
        yield num


def str_generator(name_format='{num}'):
    for num, _ in enumerate(infinite_iterable(), start=1):
        yield name_format.format(num=num)


@pytest.fixture
def user_generator(db_conn):
    id_generator = int_generator()
    username_generator = str_generator('Username {num}')
    dtid_generator = str_generator('{num:08}-{num:04}-{num:04}-{num:04}-{num:010}')
    country_generator = str_generator('Country {num}')

    async def generate_user():
        user_dict = {
            'id': next(id_generator),
            'username': next(username_generator),
            'dtid': next(dtid_generator),
            'country': next(country_generator),
        }
        user_dict = await save_user(user_dict=user_dict, conn=db_conn)
        return user_dict

    return generate_user

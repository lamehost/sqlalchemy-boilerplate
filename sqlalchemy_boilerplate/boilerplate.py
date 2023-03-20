"""
Defines the major class provided by the package:
 - Boilerplate: SQL database abstraction class.
 - AsyncBoilerplate: SQL database abstraction class with async methods
"""


import logging
from urllib.parse import urlparse
from typing import Union, Generator, AsyncGenerator
import json

from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.exc import (
    SQLAlchemyError,
    OperationalError
)
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .common import BASE


LOGGER = logging.getLogger(__name__)


class Boilerplate:
    """
    SQL database abstraction class. Allows users to create, read and delete
    tasks and results.

    Arguments:
    ----------
    url: database url
    echo: whether echo SQL queries or not
    create_tables: whether create SQL tables or not
    session: Session object used to connect to the DB. By default a new one
             is created

    """
    def __init__(
        self,
        url: str,
        echo: bool = False,
        create_tables: bool = False,
        session: Union[bool, Session] = False,
    ) -> None:
        parsed_url = urlparse(url)
        self.__create_tables = create_tables
        self.__engine_kwargs = {
            "echo": echo,
            "json_serializer": lambda obj: json.dumps(
                obj,
                ensure_ascii=False,
                default=str
            )
        }
        # We only need SQLite for unittest, but we're going to make it a
        # first class citizen anyway
        if parsed_url.scheme.lower() == 'postgresql':
            self.url = url
        elif parsed_url.scheme.lower() == 'sqlite':
            self.url = url
            # StaticPool is needed when SQLite is ran in memory
            self.__engine_kwargs['poolclass'] = StaticPool
            self.__engine_kwargs['connect_args'] = {"check_same_thread": False}
        else:
            error = (
                'Database can be either "sqlite" or "postgresql", '
                f'not: "{parsed_url.scheme}"'
            )
            raise ValueError(error)

        if session is True:
            raise ValueError('Session can be either false or AsyncSession')

        self.session = session
        self.engine = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args, **kwargs):
        self.disconnect()

    def __call__(self):
        self.connect()
        return self

    def connect(self, force: bool = False) -> bool:
        """
        Connects instance to database.

        Arguments:
        ----------
        force: bool
            Force reconnection even if a session exists already. Default: False
        """
        if self.session:
            if not force:
                return self.session

        LOGGER.info('Connecting to database')

        try:
            self.engine = create_engine(self.url, **self.__engine_kwargs)

            # Create tables if requested
            if self.__create_tables:
                BASE.metadata.create_all(bind=self.engine)

            session = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )

            self.session = session()
        except SQLAlchemyError as error:
            LOGGER.error(error)
            raise error from error
        finally:
            try:
                self.session.close()
            except AttributeError:
                pass

        return self.session

    def disconnect(self):
        """Safely disconnect the database"""
        if self.session is not None:
            self.session.close()

        if self.engine is not None:
            self.engine.dispose()

        LOGGER.info('Disconnected from database')

    def execute(self, query: str) -> Generator[tuple, str, None]:
        """
        Executes a query and yeild rows


        Arguments:
        ----------
        query: str
            Query to be executed

        Returns:
        --------
        Generator[tuple, str, None]: Result rows
        """
        query = text(query)
        with self.engine.begin() as connection:
            with connection.execution_options(
                stream_results=True
            ).execute(
                query
            ) as rows:
                yield from rows


class AsyncBoilerplate:
    """
    SQL database abstraction class. Allows users to create, read and delete
    tasks and results. All methods are async.

    Arguments:
    ----------
    url: database url
    echo: whether echo SQL queries or not
    create_tables: whether create SQL tables or not
    session: Session object used to connect to the DB. By default a new one
             is created
    """

    def __init__(
        self,
        url: str,
        echo: bool = False,
        create_tables: bool = False,
        session: Union[bool, AsyncSession] = False,
    ) -> None:
        self.__create_tables = create_tables
        self.__engine_kwargs = {
            "echo": echo,
            "json_serializer": lambda obj: json.dumps(
                obj,
                ensure_ascii=False,
                default=str
            )
        }
        # We only need SQLite for unittest, but we're going to make it a
        # first class citizen anyway
        parsed_url = urlparse(url)
        if parsed_url.scheme.lower() == 'postgresql':
            self.url = f'postgresql+asyncpg://{url[13:]}'
        elif parsed_url.scheme.lower() == 'sqlite':
            self.url = f'sqlite+aiosqlite://{url[9:]}'
            # StaticPool is needed when SQLite is ran in memory
            self.__engine_kwargs['poolclass'] = StaticPool
            self.__engine_kwargs['connect_args'] = {"check_same_thread": False}
        else:
            error = (
                'Database can be either "sqlite" or "postgresql", '
                f'not: "{parsed_url.scheme}"'
            )
            raise ValueError(error)

        if session is True:
            raise ValueError('Session can be either false or AsyncSession')

        self.session = session
        self.engine = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.disconnect()

    async def __call__(self):
        await self.connect()
        return self

    async def connect(self, force: bool = False) -> None:
        """
        Connects instance to database.

        Arguments:
        ----------
        force: bool
            Force reconnection even if a session exists already. Default: False
        """
        if self.session:
            if not force:
                return self.session

        LOGGER.info('Connecting to database')

        try:
            self.engine = create_async_engine(self.url, **self.__engine_kwargs)

            # Create tables if requested
            if self.__create_tables:
                try:
                    async with self.engine.begin() as connection:
                        await connection.run_sync(BASE.metadata.create_all)
                    LOGGER.info('Connected to database')
                except OperationalError as error:
                    LOGGER.error(error)
                    raise RuntimeError(error) from error

            make_session = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
                class_=AsyncSession
            )

        except SQLAlchemyError as error:
            LOGGER.error(error)
            raise error from error

        self.session = make_session()

        return self.session

    async def disconnect(self):
        """Safely disconnect the database"""
        if self.session is not None:
            await self.session.close()

        if self.engine is not None:
            await self.engine.dispose()

        LOGGER.info('Disconnected from database')

    async def execute(self, query: str) -> AsyncGenerator[tuple, str]:
        """
        Executes a query and yeild rows


        Arguments:
        ----------
        query: str
            Query to be executed

        Returns:
        --------
        AsyncGenerator[tuple, str]: Result rows
        """
        query = text(query)
        async with self.engine.begin() as connection:
            async for row in await connection.stream(query):
                yield row

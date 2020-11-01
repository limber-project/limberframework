"""Database Service Provider

Classes:
- DatabaseServiceProvider: Registers database services.
"""
from sqlalchemy.orm import Session, sessionmaker

from limberframework.database.connections import Connection, make_connection
from limberframework.foundation.application import Application
from limberframework.support.services import Service, ServiceProvider


class DatabaseServiceProvider(ServiceProvider):
    """Registers database services to the service container."""

    def register(self, app: Application) -> None:
        """Registers the database connection and session
        services to the service container.

        Arguments:
        app limberframework.foundation.application.Application --
        the service container.
        """

        async def register_database_connection(app: Application) -> Connection:
            """Closure for establshing a database connection service.

            Arguments:
            app Application -- foundation.application.Application object

            Returns:
            Connection object
            """
            config_service = await app.make("config")
            config = config_service.get_section("database")
            return await make_connection(config)

        app.bind(Service("db.connection", register_database_connection))

        async def register_database_session(app: Application) -> Session:
            """Closure for establishing a database session
            using the existing database connection.

            Arguments:
            app Application -- foundation.application.Application object

            Returns:
            Session object
            """
            db_connection = await app.make("db.connection")
            return sessionmaker(bind=db_connection.engine)()

        app.bind(Service("db.session", register_database_session, defer=True))

from unittest.mock import MagicMock
from sqlalchemy.orm import Session, sessionmaker
from limberframework.config.config_service_provider import ConfigServiceProvider
from limberframework.database.connections import SqliteConnection
from limberframework.database.database_service_provider import DatabaseServiceProvider

def test_database_service_provider():
    mock_app = MagicMock()
    database = DatabaseServiceProvider(mock_app)
    database.register()

    assert mock_app.bind.call_count == 2

def test_config_service_provider():
    mock_app = MagicMock()
    config = ConfigServiceProvider(mock_app)
    config.register()

    assert mock_app.bind.called_once()

from datetime import datetime, timedelta
from math import ceil
from os import getcwd
from unittest.mock import patch
from pytest import raises, mark
from limberframework.cache.stores import make_store, FileStore, MemcacheStore, RedisStore, Store

@mark.parametrize('config,store', [
    ({'driver': 'file', 'path': '/test'}, FileStore),
    ({'driver': 'redis', 'host': 'localhost', 'port': 6379, 'db': 0, 'password': None}, RedisStore),
    ({'driver': 'memcache', 'host': 'localhost', 'port': 11211}, MemcacheStore)
])
def test_make_store(config, store):
    response = make_store(config)

    assert isinstance(response, store)

def test_make_store_invalid_driver():
    config = {
        'driver': 'test'
    }

    with raises(ValueError) as excinfo:
        make_store(config)

    assert f"Unsupported cache driver {config['driver']}." in str(excinfo.value)

@mark.parametrize('directory,path', [
    ('/test','/test/a94a8fe5ccb19ba61c4c0873d391e987982fbbd3'),
    ('/Users/test/projects/limber/storage/cache', '/Users/test/projects/limber/storage/cache/a94a8fe5ccb19ba61c4c0873d391e987982fbbd3')
])
def test_file_store_path(directory, path):
    key = 'test'

    file_store = FileStore(directory)
    response = file_store.path(key)

    assert response == path

@patch('limberframework.cache.stores.FileSystem')
def test_file_store_get(mock_file_system):
    date = datetime.now() + timedelta(seconds=60)
    value = 'test'
    content = date.isoformat() + ',' + value
    mock_file_system.read_file.return_value = content

    file_store = FileStore('/test')
    response = file_store.get('test')

    assert response == {
        'data': value,
        'expires_at': date
    }

@patch('limberframework.cache.stores.FileSystem')
def test_file_store_get_expired(mock_file_system):
    date = datetime.now() - timedelta(seconds=60)
    value = 'test'
    content = date.isoformat() + ',' + value
    mock_file_system.read_file.return_value = content

    file_store = FileStore('/test')
    response = file_store.get('test')

    assert response == {
        'data': None,
        'expires_at': None
    }

@patch('limberframework.cache.stores.FileSystem')
def test_file_store_get_invalid_file(mock_file_system):
    mock_file_system.read_file.side_effect = FileNotFoundError()

    file_store = FileStore('/test')
    response = file_store.get('test')

    assert response == {
        'data': None,
        'expires_at': None
    }

@patch('limberframework.cache.stores.FileSystem')
def test_file_store_put(mock_file_system):
    key = 'test'
    value = 'test'
    expires_at = datetime.now()

    file_store = FileStore('/test')
    response = file_store.put(key, value, expires_at)

    assert response
    mock_file_system.write_file.assert_called_once()

@patch('limberframework.cache.stores.FileSystem')
def test_file_store_add_invalid_file(mock_file_system):
    mock_file_system.has_file.return_value = False
    key = 'test'
    value = 'test'
    expires_at = datetime.now()

    file_store = FileStore('/test')
    response = file_store.add(key, value, expires_at)

    assert response == False

@patch('limberframework.cache.stores.FileSystem')
def test_file_store_add(mock_file_system):
    mock_file_system.has_file.return_value = True
    key = 'test'
    value = 'test'
    expires_at = datetime.now()

    file_store = FileStore('/test')
    response = file_store.add(key, value, expires_at)

    assert response

@patch('limberframework.cache.stores.FileSystem')
def test_file_store_get_item(mock_file_system):
    date = datetime.now() - timedelta(seconds=60)
    value = 'test'
    content = date.isoformat() + ',' + value
    mock_file_system.read_file.return_value = content

    file_store = FileStore('/test')
    response = file_store['test']

    assert response == {
        'data': None,
        'expires_at': None
    }

@mark.parametrize('expires_at,has_expired', [
    (datetime(2020, 8, 12, second=1), False),
    (datetime(2020, 8, 12), True),
    (datetime(2020, 8, 11, 11, 59, 59), True)
])
@patch('limberframework.cache.stores.datetime')
def test_store_has_expired(mock_datetime, expires_at, has_expired):
    mock_datetime.now.return_value = datetime(2020, 8, 12)

    response = Store.has_expired(expires_at)

    assert response == has_expired

def test_store_encode():
    value = 'test'
    expires_at = datetime(2020, 8, 12)

    response = Store.encode(value, expires_at)

    assert response == '2020-08-12T00:00:00,test'

def test_store_decode():
    contents = '2020-08-12T00:00:00,test'

    response = Store.decode(contents)

    assert response == {
        'value': 'test',
        'expires_at': datetime(2020, 8, 12)
    }

@mark.parametrize('contents,payload', [
    (None, {'data': None, 'expires_at': None}),
    ('2020-08-12T00:00:00,test'.encode(), {'data': 'test', 'expires_at': datetime(2020, 8, 12)})
])
def test_store_process(contents, payload):
    response = Store.process(contents)
    assert response == payload

@mark.parametrize('data,expires_at,payload', [
    (None, None, {'data': None, 'expires_at': None}),
    ('test', datetime(2020, 8, 12), {'data': 'test', 'expires_at': datetime(2020, 8, 12)}),
])
def test_payload(data, expires_at, payload):
    response = Store.payload(data, expires_at)
    assert response == payload

@patch('limberframework.cache.stores.Redis')
def test_redis_store_get(mock_redis):
    mock_redis.return_value.get.return_value = '2020-08-12T00:00:00,test'.encode()

    redis_store = RedisStore('localhost', 6379, 0, None)
    response = redis_store.get('test')

    assert response == {
        'data': 'test',
        'expires_at': datetime(2020, 8, 12)
    }

@patch('limberframework.cache.stores.datetime')
@patch('limberframework.cache.stores.Redis')
def test_redis_store_add(mock_redis, mock_datetime):
    key = 'test'
    value = 'test'
    expires_at = datetime(2020, 8, 12, 1)
    now = datetime(2020, 8, 12)
    ex = expires_at - now
    mock_redis.return_value.set.return_value = True
    mock_datetime.now.return_value = now

    redis_store = RedisStore('localhost', 6379, 0, None)
    response = redis_store.add(key, value, expires_at)

    assert response
    mock_redis.return_value.set.assert_called_once_with(key, '2020-08-12T01:00:00,test', ex=ex, nx=True)

@patch('limberframework.cache.stores.datetime')
@patch('limberframework.cache.stores.Redis')
def test_redis_store_put(mock_redis, mock_datetime):
    key = 'test'
    value = 'test'
    expires_at = datetime(2020, 8, 12, 1)
    now = datetime(2020, 8, 12)
    ex = expires_at - now
    mock_redis.return_value.set.return_value = True
    mock_datetime.now.return_value = now

    redis_store = RedisStore('localhost', 6379, 0, None)
    response = redis_store.put(key, value, expires_at)

    assert response
    mock_redis.return_value.set.assert_called_once_with(key, '2020-08-12T01:00:00,test', ex=ex)

@patch('limberframework.cache.stores.Client')
def test_memcache_store_get(mock_memcache):
    mock_memcache.return_value.get.return_value = '2020-08-12T00:00:00,test'.encode()

    memcache_store = MemcacheStore('localhost', 11211)
    response = memcache_store.get('test')

    assert response == {
        'data': 'test',
        'expires_at': datetime(2020, 8, 12)
    }

@patch('limberframework.cache.stores.datetime')
@patch('limberframework.cache.stores.Client')
def test_memcache_store_add(mock_memcache, mock_datetime):
    key = 'test'
    value = 'test'
    expires_at = datetime(2020, 8, 12, 1)
    now = datetime(2020, 8, 12)
    expire = ceil((expires_at - now).total_seconds())
    mock_memcache.return_value.get.return_value = None
    mock_memcache.return_value.set.return_value = True
    mock_datetime.now.return_value = now

    memcache_store = MemcacheStore('localhost', 11211)
    response = memcache_store.add(key, value, expires_at)

    assert response
    mock_memcache.return_value.set.assert_called_once_with(key, '2020-08-12T01:00:00,test', expire=expire)

@patch('limberframework.cache.stores.Client')
def test_memcache_store_add_existing(mock_memcache):
    memcache_store = MemcacheStore('localhost', 11211)
    response = memcache_store.add('test', 'test', datetime(2020, 8, 12, 1))

    assert not response

@patch('limberframework.cache.stores.datetime')
@patch('limberframework.cache.stores.Client')
def test_memcache_store_put(mock_memcache, mock_datetime):
    key = 'test'
    value = 'test'
    expires_at = datetime(2020, 8, 12, 1)
    now = datetime(2020, 8, 12)
    expire = ceil((expires_at - now).total_seconds())
    mock_memcache.return_value.set.return_value = True
    mock_datetime.now.return_value = now

    memcache_store = MemcacheStore('localhost', 11211)
    response = memcache_store.put(key, value, expires_at)

    assert response
    mock_memcache.return_value.set.assert_called_once_with(key, '2020-08-12T01:00:00,test', expire=expire)

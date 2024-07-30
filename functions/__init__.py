#__init__.py
from .connection_module import get_mongo_client, get_database_and_collection

__all__ = ['get_mongo_client', 'get_database_and_collection']

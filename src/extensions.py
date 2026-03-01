"""Application extensions (database instance, etc.)."""

from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
#from sqlalchemy import event
#from sqlalchemy.engine import Engine

db = SQLAlchemy()
cache = Cache()

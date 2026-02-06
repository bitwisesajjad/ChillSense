from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()

## the Exercise 1. Introduction to Web Development says sqlite doesn't enforce foreign keys by default.
# so we need this hack to turn them on, otherwise ondelete='SET NULL' won't work.
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
from sqlalchemy import create_engine, Column, Table, ForeignKey, MetaData
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Integer, String, Date, DateTime, Float, Boolean, Text)
from scrapy.utils.project import get_project_settings
import pymysql
pymysql.install_as_MySQLdb()

Base = declarative_base()


def db_connect():
    """
    Performs database connection using database settings from settings.py.
    Returns sqlalchemy engine instance
    """
    return create_engine(get_project_settings().get("CONNECTION_STRING"))


def create_table(engine):
    Base.metadata.create_all(engine)


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True)
    title = Column('title', String(500))
    author = Column('author', String(500))
    date = Column('date', DateTime())
    link = Column('link', String(500), unique=True)
    journal = Column('journal', String(100))
    text = Column('text', Text())
    processed_text = Column('processed_text', Text())
    meta = Column('meta', Text())

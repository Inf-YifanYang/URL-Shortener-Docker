from .config import get_settings
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import Boolean, Column, String, Integer, DateTime

engine = create_engine(get_settings().DATABASE_URL,
                       connect_args={'check_same_thread': False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class URLMapping(Base):
    __tablename__ = 'long_short_urls_mappings'

    id = Column(Integer, primary_key=True, index=True)
    long_url = Column(String, nullable=False)
    short_url = Column(String, unique=True, nullable=False)
    creation_time = Column(DateTime, nullable=False)
    expiration_time = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Initialize the database
    Base.metadata.create_all(bind=engine)
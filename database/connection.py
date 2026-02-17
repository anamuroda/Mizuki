from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# cria o arquivo mizuki.db na raiz
# check_same_thread=False é apenas para SQLite com multithreading/async
DATABASE_URL = "sqlite:///./mizuki.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
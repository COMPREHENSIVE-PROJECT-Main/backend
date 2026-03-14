import os
from fastapi import FastAPI
from sqlalchemy import create_engine, text

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "서버 실행중"}

@app.get("/db") # db 연결 확인용
async def check_db():
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")

    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try: # test
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"message": "db 연결확인 완료 (정상)"}
    
    except Exception as e:
        return {"message": f"db 연결 실패", "error": str(e)}
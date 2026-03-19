# FastAPI 앱의 진입점
# 서버 시작/종료 시 해야 할 작업과 API 엔드포인트를 여기서 관리함
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

import app.models
from app.database import engine, create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버가 시작될 때 실행됨
    create_tables()  # 테이블이 없으면 자동으로 생성
    yield
    # yield 아래는 서버가 종료될 때 실행


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "서버 실행중"}


@app.get("/db")  # DB 연결 확인용 엔드포인트
async def check_db():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))  # 가장 간단한 쿼리로 연결 확인
        return {"message": "db 연결확인 완료 (정상)"}
    except Exception:
        return {"message": "db 연결 실패"}

# Backend

FastAPI 기반 백엔드와 AI 서비스를 함께 관리하는 프로젝트입니다.

현재 프로젝트는 `backend`, `ai`, `com` 영역으로 나뉘며, Docker Compose 기준으로 아래 컨테이너들을 함께 실행합니다.

- `main-backend`: 일반 API, 인증, DB 처리
- `ai-service`: AI 전용 서비스, LangGraph 확장 대상
- `main-db`: PostgreSQL
- `redis`: 캐시/상태 저장
- `ollama`: 로컬 모델 서버
- `ollama-init`: Ollama 모델 사전 pull

## Project Structure

```text
.
├── app
│   ├── ai
│   │   ├── core
│   │   ├── db
│   │   ├── schemas
│   │   ├── services
│   │   ├── utils
│   │   ├── Dockerfile
│   │   └── main.py
│   ├── backend
│   │   ├── api
│   │   │   └── endpoints
│   │   ├── db
│   │   ├── models
│   │   ├── schemas
│   │   ├── services
│   │   ├── utils
│   │   ├── Dockerfile
│   │   └── main.py
│   ├── com
│   └── config.py
├── docker-compose.yml
├── example.env
├── README.md
└── requirements.txt
```

## Directory Guide

### `app/backend`

일반 백엔드 로직이 들어 있습니다.

- `main.py`: FastAPI 앱 진입점
- `api/`: 라우터와 엔드포인트
- `db/`: SQLAlchemy 엔진, 세션 관리
- `models/`: 백엔드에서 사용하는 DB 모델
- `schemas/`: 요청/응답 스키마
- `services/`: 인증 등 비즈니스 로직
- `utils/`: JWT, 의존성 주입, 입력 검증 유틸
- `Dockerfile`: `main-backend` 컨테이너 빌드 파일

### `app/ai`

AI 관련 로직이 들어 있습니다.

- `main.py`: AI 서비스 진입점
- `core/`: AI 설정, 캐시, LLM 선택, 벡터 인덱스 설정
- `db/`: Redis, 벡터 DB 연결
- `schemas/`: LLM, 임베딩, 벡터 관련 스키마
- `services/`: Ollama 호출, 임베딩 생성, 벡터 DB 처리
- `utils/`: 텍스트 분할 유틸
- `Dockerfile`: `ai-service` 컨테이너 빌드 파일

### `app/com`

백엔드와 AI가 공통으로 사용하는 모듈입니다.

- `logger.py`: 공통 로거

### `app/config.py`

앱 전역 설정 파일입니다. DB, Redis, Ollama, JWT 관련 환경변수를 읽습니다.

## Containers

### `main-backend`

- Dockerfile: [app/backend/Dockerfile](/Users/mooji/school/backend/app/backend/Dockerfile)
- Port: `8080`
- 역할: 인증, 일반 API, DB 처리

### `ai-service`

- Dockerfile: [app/ai/Dockerfile](/Users/mooji/school/backend/app/ai/Dockerfile)
- Port: `8090`
- 역할: AI 전용 API, LangGraph 확장 대상

### `main-db`

- Image: `postgres:16.2-alpine`
- 역할: 서비스 데이터 저장

### `redis`

- Image: `redis:7.2-alpine`
- 역할: 캐시, 임시 상태 저장

### `ollama`

- Image: `ollama/ollama:latest`
- Port: `11434`
- 역할: 로컬 LLM/Embedding 서버

### `ollama-init`

- 역할: 시작 시 `gemma3:4b`, `nomic-embed-text` 모델 pull

## Run

`.env` 파일을 준비한 뒤 실행합니다.

```bash
docker compose up --build
```

확인용 기본 주소:

- Backend: `http://localhost:8080`
- AI Service: `http://localhost:8090/health`
- Ollama: `http://localhost:11434`

## Infra Files

- `docker-compose.yml`: 전체 컨테이너 오케스트레이션
- `example.env`: 환경변수 예시 파일
- `requirements.txt`: 파이썬 의존성 목록

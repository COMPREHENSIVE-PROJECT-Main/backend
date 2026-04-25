# Backend

FastAPI 기반 백엔드와 AI 파이프라인을 함께 관리하는 프로젝트입니다.

현재 프로젝트는 `backend`, `ai`, `com` 영역으로 나뉘며, Docker Compose 기준으로 아래 컨테이너들을 함께 실행합니다.

- `main-backend`: 일반 API, 인증, DB 처리, AI 파이프라인 호출
- `main-db`: PostgreSQL
- `redis`: 캐시/상태 저장

## Project Structure

```text
.
├── app
│   ├── ai
│   │   ├── agents
│   │   ├── core
│   │   ├── db
│   │   ├── ml
│   │   ├── models
│   │   ├── schemas
│   │   ├── services
│   │   ├── utils
│   │   ├── main.py
│   │   └── requirements.txt
│   ├── backend
│   │   ├── api
│   │   │   └── endpoints
│   │   ├── db
│   │   ├── models
│   │   ├── schemas
│   │   ├── services
│   │   ├── utils
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   ├── com
│   └── config.py
├── docker-compose.yml
├── example.env
├── README.md
└── ...
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
- `requirements.txt`: 백엔드 컨테이너 의존성 목록

### `app/ai`

AI 관련 로직이 들어 있습니다.

- `main.py`: AI 인덱싱/상태 생성 CLI 진입점
- `core/`: AI 설정, 캐시, Azure OpenAI/OpenAI 런타임 설정
- `db/`: Redis, 벡터 DB 연결
- `schemas/`: LLM, 임베딩, 벡터 관련 스키마
- `services/`: Azure OpenAI 채팅 호출, OpenAI 임베딩, 벡터 DB 처리
- `utils/`: 텍스트 분할 유틸
- `ml/`: 형사/민사 분류 ML 모델 파일
- `requirements.txt`: AI CLI/파이프라인 의존성 목록

### `app/com`

백엔드와 AI가 공통으로 사용하는 모듈입니다.

- `logger.py`: 공통 로거

### `app/config.py`

앱 전역 설정 파일입니다. DB, Redis, JWT 관련 환경변수를 읽습니다.

## Containers

### `main-backend`

- Dockerfile: [app/backend/Dockerfile](/Users/mooji/school/backend/app/backend/Dockerfile)
- Port: `8080`
- 역할: 인증, 일반 API, DB 처리, `app/ai` 파이프라인 직접 호출

### `main-db`

- Image: `postgres:16.2-alpine`
- 역할: 서비스 데이터 저장

### `redis`

- Image: `redis:7.2-alpine`
- 역할: 캐시, 임시 상태 저장

## Run

`.env` 파일을 준비한 뒤 실행합니다.

```bash
docker compose up --build
```

확인용 기본 주소:

- Backend: `http://localhost:8080`

## Dependencies

의존성 파일은 `backend`와 `ai`가 각각 따로 관리합니다.

- 백엔드 패키지 추가: [app/backend/requirements.txt](/Users/mooji/school/backend/app/backend/requirements.txt)에 추가
- AI 패키지 추가: [app/ai/requirements.txt](/Users/mooji/school/backend/app/ai/requirements.txt)에 추가

공통 패키지라도 현재 구조에서는 두 컨테이너가 각각 빌드되므로, 둘 다 필요하면 두 파일에 모두 넣어야 합니다.

의존성 수정 후에는 이미지를 다시 빌드해야 합니다.

```bash
docker compose up --build
```

## Infra Files

- `docker-compose.yml`: 전체 컨테이너 오케스트레이션
- `example.env`: 환경변수 예시 파일
- `app/backend/requirements.txt`: 백엔드 의존성 목록
- `app/ai/requirements.txt`: AI 서비스 의존성 목록

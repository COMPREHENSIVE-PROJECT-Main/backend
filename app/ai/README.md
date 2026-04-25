# AI CLI

`app/ai`는 독립 HTTP 서버가 아니라 CLI 기반 AI 모듈이다.  
현재는 ChromaDB에 법률 데이터셋을 임베딩하고, 이후 멀티 에이전트 재판 파이프라인에서 검색용으로 사용하는 것이 1차 목적이다.

## 데이터셋 구조

현재 `app/dataset` 아래 데이터셋은 세 종류다.

- `app/dataset/case_law`
- `app/dataset/statutes`
- `app/dataset/sentencing_guidelines`

권장 컬렉션 매핑은 다음과 같다.

- `case_law` -> `cases`
- `statutes` -> `statutes`
- `sentencing_guidelines` -> `sentencing`

## 환경 변수

`.env`에 최소한 아래 값이 필요하다.

```env
# OpenAI Embedding
OPENAI_API_KEY=your_openai_api_key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Azure OpenAI Chat
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
LLM_TIMEOUT_SECONDS=300

CHROMA_PATH=./chroma_db
REDIS_URL=redis://localhost:6379
```

실제 설정 로딩은 [runtime.py](/Users/mooji/school/backend/app/ai/core/runtime.py)에서 처리한다.

## 설치

```bash
pip install -r app/ai/requirements.txt
```

## CLI 사용법

### 1. 판례 인덱싱

```bash
python3 -m app.ai.main --index-case-law --collection-name cases
```

### 2. 법조문 인덱싱

```bash
python3 -m app.ai.main --index-statutes --collection-name statutes
```

### 3. 양형기준 인덱싱

```bash
python3 -m app.ai.main --index-sentencing --collection-name sentencing
```

### 4. 전체 병렬 인덱싱

```bash
python3 -m app.ai.main --all
```

`--all`은 아래 세 컬렉션으로 고정 실행된다.

- `cases`
- `statutes`
- `sentencing`

### 5. 공통 옵션

```bash
python3 -m app.ai.main --index-case-law \
  --collection-name cases \
  --batch-size 100 \
  --chunk-size 800 \
  --overlap 150 \
  --skip-if-collection-exists
```

옵션 의미:

- `--batch-size`: Chroma upsert 배치 크기
- `--chunk-size`: 텍스트 분할 크기
- `--overlap`: 청크 간 overlap
- `--skip-if-collection-exists`: 컬렉션에 데이터가 있으면 전체 인덱싱 스킵

## 로그 예시

### 판례 인덱싱

```text
[INFO] [app.ai.db.vector_db] ChromaDB 로컬 연결 성공: ./chroma_db
[INFO] [app.ai.db.vector_db] 컬렉션 획득: cases (embedding_provider=openai, embedding_model=text-embedding-3-small)
[INFO] [app.ai.services.indexing_service] 판례 데이터셋 인덱싱 시작: root=/Users/mooji/school/backend/app/dataset/case_law, collection=cases, files=8000, batch_size=100, chunk_size=800, overlap=150
[INFO] [app.ai.services.indexing_service] 판례 JSON 인덱싱 시작: file=administration/1981~2016/(전주)2010누1281.json, progress=1/8000
[INFO] [app.ai.services.indexing_service] 판례 JSON 인덱싱 완료: file=administration/1981~2016/(전주)2010누1281.json, indexed_chunks=23, successful_files=1, total_indexed_chunks=23
[INFO] [app.ai.services.indexing_service] 판례 데이터셋 인덱싱 종료: root=/Users/mooji/school/backend/app/dataset/case_law, collection=cases, discovered_files=8000, successful_files=8000, skipped_files=0, failed_files=0, total_indexed_chunks=...
```

### 법조문 인덱싱

```text
[INFO] [app.ai.db.vector_db] 컬렉션 획득: statutes (embedding_provider=openai, embedding_model=text-embedding-3-small)
[INFO] [app.ai.services.indexing_service] 법조문 데이터셋 인덱싱 시작: root=/Users/mooji/school/backend/app/dataset/statutes, collection=statutes, files=1709, batch_size=100, chunk_size=800, overlap=150
[INFO] [app.ai.services.indexing_service] 법조문 JSON 인덱싱 시작: file=000001.json, progress=1/1709
[INFO] [app.ai.services.indexing_service] 법조문 JSON 인덱싱 완료: file=000001.json, indexed_chunks=14, successful_files=1, total_indexed_chunks=14
```

### 양형기준 인덱싱

```text
[INFO] [app.ai.db.vector_db] 컬렉션 획득: sentencing (embedding_provider=openai, embedding_model=text-embedding-3-small)
[INFO] [app.ai.services.indexing_service] 양형기준 데이터셋 인덱싱 시작: root=/Users/mooji/school/backend/app/dataset/sentencing_guidelines, collection=sentencing, files=47, batch_size=100, chunk_size=800, overlap=150
[INFO] [app.ai.services.indexing_service] 양형기준 JSON 인덱싱 시작: file=강도범죄.json, progress=1/47
[INFO] [app.ai.services.indexing_service] 양형기준 JSON 인덱싱 완료: file=강도범죄.json, indexed_chunks=24, successful_files=1, total_indexed_chunks=24
```

## 현재 인덱싱 동작

### 판례

[index_case_law_dataset()](/Users/mooji/school/backend/app/ai/services/indexing_service.py)는:

- `app/dataset/case_law` 아래 모든 `json` 파일을 재귀 탐색한다
- 사건 메타데이터와 사건 유형(`administrative`, `civil`, `criminal`)을 추출한다
- `facts`, `assrs`, `dcss`, `disposal`, `close` 등을 청크로 분할한다
- `cases` 컬렉션에 upsert 한다

### 법조문

[index_statutes_dataset()](/Users/mooji/school/backend/app/ai/services/indexing_service.py)는:

- `app/dataset/statutes` 아래 JSON 배열을 읽는다
- 각 조문을 `law_name`, `article_number`, `article_title`, `article_content` 중심 텍스트로 구성한다
- `statutes` 컬렉션에 upsert 한다

### 양형기준

[index_sentencing_dataset()](/Users/mooji/school/backend/app/ai/services/indexing_service.py)는:

- `app/dataset/sentencing_guidelines` 아래 JSON 배열을 읽는다
- 각 기준을 `crime_type`, `sub_type`, `sentencing_type`, `sentencing_min/max`, `aggravating`, `mitigating`, `probation_criteria` 중심 텍스트로 구성한다
- `sentencing` 컬렉션에 upsert 한다

## 참고

- Chroma는 로컬 persistent mode로 동작한다.
- 임베딩 생성은 OpenAI `text-embedding-3-small` 기준으로 동작한다.
- 채팅 호출은 Azure OpenAI deployment name을 `model` 값으로 사용한다.
- 개별 인덱싱 명령에서는 `--collection-name`을 명시하는 편이 안전하다.
- 전체 병렬 인덱싱은 `--all`을 쓰는 것이 가장 단순하다.

# MindDock Backend Prototype

이 저장소는 MindDock 기억 플랫폼의 백엔드 프로토타입을 FastAPI 기반으로 구현한 것입니다. RESTful API를 통해 사용자, 기억(Memory), 첨부파일을 관리하며 멀티모달 입력 확장을 고려한 구조로 설계되었습니다.

## 주요 구성

- `app/main.py`: FastAPI 엔트리포인트
- `app/api`: 버전별 라우터, 의존성 주입 모듈
- `app/services`: 도메인 서비스 계층 (비즈니스 로직)
- `app/repositories`: 데이터 액세스 레이어
- `app/models`: SQLAlchemy ORM 모델
- `app/schemas`: Pydantic 기반 요청/응답 스키마
- `app/storage`: 첨부파일 저장 디렉터리 (로컬 파일 시스템)

## 빠른 시작

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

실행 후 `http://localhost:8000/docs`에서 자동 생성된 OpenAPI 문서를 확인할 수 있습니다.

### 통합 실행 스크립트

반복되는 개발 명령은 `scripts/minddock.sh` 하나로 모았습니다. 최초 1회 실행 권한을 부여한 뒤 아래 서브커맨드를 활용하세요.

```bash
chmod +x scripts/minddock.sh   # 최초 1회

./scripts/minddock.sh setup        # 가상환경 생성 및 requirements 설치
./scripts/minddock.sh backend      # FastAPI 개발 서버 (자동 reload)
./scripts/minddock.sh frontend     # Vite 개발 서버
./scripts/minddock.sh docker       # Docker 빌드 및 실행
./scripts/minddock.sh test         # pytest 실행
./scripts/minddock.sh format       # ruff 기반 포맷팅
./scripts/minddock.sh rag-reindex  # 저장된 모든 기억 임베딩 재생성
```

`./scripts/minddock.sh help`로 전체 명령 목록과 환경 변수를 확인할 수 있습니다.

### Docker 실행

```bash
chmod +x scripts/run_docker.sh
./scripts/run_docker.sh
```

환경 변수로 `IMAGE_NAME`, `CONTAINER_NAME`, `HOST_PORT`, `ENV_FILE`을 전달해 빌드/실행 구성을 조정할 수 있습니다. 기본적으로 호스트의 `app/storage` 디렉터리가 컨테이너의 `/app/app/storage`에 마운트되어 첨부파일이 지속됩니다.

### 프론트엔드 (Vite + React)

```bash
chmod +x scripts/run_frontend.sh
./scripts/run_frontend.sh
```

기본적으로 `http://localhost:5173`에서 동작하며, Vite 개발 서버가 `/api` 경로를 FastAPI 백엔드(`http://localhost:8000`)로 프록시합니다. 프로덕션 빌드는 `frontend` 디렉터리에서 `npm run build`로 생성할 수 있습니다.

## RAG 파이프라인 & 워크플로 엔진

- 메모가 생성/수정/삭제될 때 워크플로 엔진이 이벤트(`memory.created|updated|deleted`)를 감지해 임베딩을 갱신하거나 정리합니다.
- OpenAI API 키가 설정되어 있으면 `text-embedding-3-small`(기본값)로 벡터를 생성하고, 미설정 시 해시 기반 로컬 임베딩으로 대체합니다.
- 어시스턴트 응답은 자동으로 RAG 검색을 수행해 관련 메모를 컨텍스트로 전달하며, 프론트엔드에서도 참고한 메모 목록과 점수를 확인할 수 있습니다.
- 기존 데이터에 대해 재색인이 필요하면 `./scripts/minddock.sh rag-reindex` 명령을 실행하세요.

## 주요 API 요약

- `POST /api/v1/users/`: 사용자 생성
- `POST /api/v1/memories/`: 기억 생성
- `POST /api/v1/memories/transcribe`: 음성 파일을 업로드해 자동으로 텍스트 메모와 첨부 저장
- `GET /api/v1/memories/?owner_id=...`: 사용자별 기억 조회
- `POST /api/v1/memories/{memory_id}/attachments`: 첨부파일 업로드
- `GET /api/v1/memories/{memory_id}/attachments/{attachment_id}`: 첨부파일 다운로드

## 환경 변수

`.env` 파일 또는 환경 변수로 다음 값을 재정의할 수 있습니다.

- `MINDDOCK_SQL_DATABASE_URL`: 데이터베이스 URL (기본값: 프로젝트 루트의 SQLite)
- `MINDDOCK_STORAGE_DIR`: 첨부파일 저장 경로
- `MINDDOCK_PROJECT_NAME`: API 문서 제목
- `MINDDOCK_OPENAI_API_KEY`: OpenAI GPT 모델 호출 시 사용할 API 키 (미설정 시 로컬 요약 모드 응답 제공)
- `MINDDOCK_OPENAI_MODEL`: 사용할 OpenAI 모델 이름 (기본값: `gpt-4o-mini`)
- `MINDDOCK_OPENAI_TRANSCRIPTION_MODEL`: 음성 인식에 사용할 OpenAI 모델 이름 (기본값: `gpt-4o-transcribe`)
- `MINDDOCK_OPENAI_EMBEDDING_MODEL`: RAG 임베딩에 사용할 OpenAI 모델 이름 (기본값: `text-embedding-3-small`)
- `MINDDOCK_RAG_ENABLED`: RAG 파이프라인 활성화 여부 (기본값: `True`)
- `MINDDOCK_RAG_DEFAULT_TOP_K`: RAG 검색 시 기본으로 가져오는 메모 개수 (기본값: `3`)
- `MINDDOCK_RAG_LOCAL_VECTOR_SIZE`: 로컬 해시 임베딩 벡터 크기 (기본값: `512`)

## 확장 고려 사항

- 인증/인가 계층(JWT, OAuth2)
- 워크플로 엔진에 스케줄러/외부 알림 채널 연동
- 태스크 자동화, 에이전트 핸드오프, 실시간 협업 시나리오
- 멀티테넌시 및 조직 단위 권한 관리

MindDock 백엔드는 향후 멀티모달 캡처와 자동 구조화, RAG 기반 응답, 워크플로 자동화를 단계적으로 확장할 수 있도록 모듈형 구조를 따릅니다.

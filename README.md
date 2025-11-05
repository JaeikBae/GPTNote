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

### Docker 실행

```bash
chmod +x scripts/run_docker.sh
./scripts/run_docker.sh
```

환경 변수로 `IMAGE_NAME`, `CONTAINER_NAME`, `HOST_PORT`, `ENV_FILE`을 전달해 빌드/실행 구성을 조정할 수 있습니다. 기본적으로 호스트의 `app/storage` 디렉터리가 컨테이너의 `/app/app/storage`에 마운트되어 첨부파일이 지속됩니다.

## 주요 API 요약

- `POST /api/v1/users/`: 사용자 생성
- `POST /api/v1/memories/`: 기억 생성
- `GET /api/v1/memories/?owner_id=...`: 사용자별 기억 조회
- `POST /api/v1/memories/{memory_id}/attachments`: 첨부파일 업로드
- `GET /api/v1/memories/{memory_id}/attachments/{attachment_id}`: 첨부파일 다운로드

## 환경 변수

`.env` 파일 또는 환경 변수로 다음 값을 재정의할 수 있습니다.

- `MINDDOCK_SQL_DATABASE_URL`: 데이터베이스 URL (기본값: 프로젝트 루트의 SQLite)
- `MINDDOCK_STORAGE_DIR`: 첨부파일 저장 경로
- `MINDDOCK_PROJECT_NAME`: API 문서 제목

## 확장 고려 사항

- 인증/인가 계층(JWT, OAuth2)
- RAG 파이프라인 연계 및 벡터 스토리지 통합
- 이벤트 기반 워크플로 엔진 및 알림 시스템
- 멀티테넌시 및 조직 단위 권한 관리

MindDock 백엔드는 향후 멀티모달 캡처와 자동 구조화, RAG 기반 응답, 워크플로 자동화를 단계적으로 확장할 수 있도록 모듈형 구조를 따릅니다.

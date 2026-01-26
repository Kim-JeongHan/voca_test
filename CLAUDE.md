# CLAUDE.md - voca_test

## Project Context

C++ 단어 학습 프로그램. CSV 단어장을 로드하여 퀴즈/테스트를 수행하고 오답을 관리한다.

## Tech Stack

### C++ Core
- Language: C++17
- Build System: CMake 3.10+
- Linter: clang-format (v16)
- Pre-commit: pre-commit hooks enabled

### Python Backend
- Language: Python 3.12
- Framework: FastAPI
- ORM: SQLAlchemy
- Package Manager: uv (recommended)
- Database: SQLite (dev) / PostgreSQL (prod)

## Operational Commands

```bash
# Build (script)
./build.sh

# Run tests
cd build && ctest --output-on-failure

# Run application
./run.sh simple 1
./run.sh multiple 1 2 3

# Pre-commit
pre-commit run -a

# Format check
clang-format -i src/*.cpp include/voca_test/*.hpp

# Generate TTS audio for word decks
uv sync
uv run generate_audio.py

# Backend (FastAPI)
cd backend
uv sync
cp .env.example .env  # Edit with API keys
uv run python init_db.py --sample
uv run uvicorn app.main:app --reload

# Backend tests
cd backend && uv run pytest

# Docker Compose (full stack)
docker-compose up -d
```

## Golden Rules

### Immutable

- C++17 표준 준수
- 모든 헤더는 `include/voca_test/` 경로에 위치
- 모든 구현은 `src/` 경로에 위치

### Do's

- 새 클래스 추가 시 헤더(.hpp)와 구현(.cpp) 분리
- CMakeLists.txt에 새 소스 파일 등록
- 새 모듈 추가 시 `tests/test_*.cpp` 테스트 작성
- pre-commit 통과 후 커밋

### Don'ts

- 헤더에 구현 코드 작성 금지 (인라인 제외)
- `using namespace std;` 전역 사용 금지
- 하드코딩된 경로 사용 금지 (`../docs/words/` 패턴 유지)

## Standards & References

### File Naming

- Headers: `include/voca_test/{module}.hpp`
- Sources: `src/{module}.cpp`
- Tests: `tests/test_{module}.cpp`

### Git Convention

- Commit format: `{Type}: {Message}` 또는 `:{emoji}: {message}`
- Type/Emoji: `Fix:` or `:bug:` (fix), `:sparkles:` (feature), `:recycle:` (refactor)
- Branch: feature/*, bugfix/*, refactor/*

### Maintenance Policy

코드와 규칙 간 괴리 발생 시 CLAUDE.md 업데이트를 제안할 것.

## Architecture Overview

```
TestVoca (Facade)
    |
    +-- VocaLoader      : CSV 파일 로딩
    +-- VocaRepository  : 단어 데이터 저장소
    +-- VocaTestEngine  : 채점 로직
    +-- VocaResult      : 점수/오답 관리
    +-- VocaSaver       : 결과 저장
    +-- VocaSession     : 세션 상태 관리
```

## Web UI (docs/)

PWA 기반 웹 인터페이스. GitHub Pages를 통해 배포됨.

### 구조

```
docs/
├── index.html       : 메인 HTML (3개 화면: home, session, summary)
├── css/style.css    : 스타일시트
├── js/
│   ├── app.js       : 메인 애플리케이션 로직
│   ├── storage.js   : IndexedDB 저장소 래퍼 (v4: image 캐시, wrong stats 포함)
│   ├── tts.js       : TTS 모듈 (Dictionary API + ElevenLabs)
│   └── image_association.js : 연상 이미지 모듈 (HuggingFace SD API)
├── audio/           : Pre-generated TTS 오디오 파일
├── icons/           : PWA 아이콘 (icon.svg, icon-192.png, icon-512.png)
├── wasm/            : C++ WASM 빌드 출력 (선택적)
├── words/           : 단어장 CSV 파일 (GitHub Pages와 C++ 공용)
├── manifest.json    : PWA 매니페스트
└── sw.js            : 서비스 워커 (오프라인 지원, 현재 v8)
```

### 주요 기능

- **힌트 버튼**: 클릭 시 순차적 힌트 표시 (2회 이상 사용 시 오답 처리)
- **제출 버튼**: 답안 제출 (Enter 키와 동일)
- **Save & Quit**: 세션 저장 후 종료
- **Wrong Only**: 오답만 재학습
- **TTS 발음**: 단어 표시/오답 시 발음 재생 (스피커 버튼으로 수동 재생 가능)
- **연상 이미지**: 오답 2회 이상 시 AI 생성 연상 이미지 표시 (이미지 버튼으로 수동 생성 가능)

### 수정 시 주의

- `app.js` 수정 시 WASM/JS fallback 양쪽 모두 고려
- `storage.js`의 DB_VERSION 변경 시 onupgradeneeded 핸들러 확인
- CSS는 모바일 우선 반응형 디자인
- `tts.js`의 workerUrl은 배포된 Cloudflare Worker URL로 설정 필요
- `image_association.js`의 workerUrl은 배포된 Image Worker URL로 설정 필요
- `sw.js`의 CACHE_NAME 버전은 에셋 변경 시 증가 필요

## Python Backend (backend/)

FastAPI 기반 백엔드. TTS, 이미지 생성, 퀴즈 세션 관리 REST API 제공.

### 아키텍처

```
backend/
├── app/
│   ├── api/v1/          # API 라우트 (tts, image, session, decks)
│   ├── core/            # C++ 엔진 래퍼 (pybind11)
│   ├── models/          # SQLAlchemy 모델
│   ├── schemas/         # Pydantic 스키마
│   ├── services/        # 비즈니스 로직 (TTS, Image, Session)
│   ├── config.py        # 설정
│   ├── database.py      # DB 설정
│   └── main.py          # FastAPI 앱
├── tests/               # pytest 테스트
├── .env.example         # 환경 변수 템플릿
├── pyproject.toml       # uv 프로젝트 설정
└── Dockerfile
```

### 주요 API 엔드포인트

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/tts` | POST | TTS 오디오 생성 |
| `/api/v1/image` | POST | 연상 이미지 생성 |
| `/api/v1/session/start` | POST | 퀴즈 세션 시작 |
| `/api/v1/session/{id}/submit` | POST | 답안 제출 |
| `/api/v1/decks` | GET | 덱 목록 조회 |

### 로컬 개발

```bash
cd backend
uv sync                           # 의존성 설치
cp .env.example .env              # 환경 변수 설정
uv run python init_db.py --sample # DB 초기화 (샘플 데이터)
uv run uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs

### Docker Compose 배포

```bash
# 프로젝트 루트에서
cp backend/.env.example backend/.env
docker-compose up -d

# 서비스 확인
# - Backend: http://localhost:8000
# - Frontend: http://localhost:3000
# - PostgreSQL: localhost:5432
```

### 환경 변수

```env
DATABASE_URL=sqlite:///./voca.db
ELEVENLABS_API_KEY=your_key  # Optional: TTS 발음용
CORS_ORIGINS_STR=http://localhost:3000,http://127.0.0.1:3000
```

### 테스트

```bash
cd backend
uv run pytest                     # 전체 테스트
uv run pytest --cov=app           # 커버리지 포함
```

자세한 내용은 [UV_GUIDE.md](./UV_GUIDE.md) 및 [backend/README.md](./backend/README.md) 참조.

## Cloudflare Worker (Legacy)

> **Note**: Python Backend 사용 권장. Cloudflare Worker는 레거시로 유지됨.

ElevenLabs TTS API 프록시. API 키를 서버 측에 안전하게 보관.

### 배포

```bash
cd cloudflare-worker
npm install -g wrangler
wrangler login
wrangler secret put ELEVENLABS_API_KEY  # .env 파일의 키 입력
wrangler deploy
```

배포 후 URL을 `docs/js/tts.js`의 `CONFIG.workerUrl`에 설정.

### 구조

```
cloudflare-worker/
├── src/index.js     : Worker 코드 (입력 검증, 타임아웃, CORS)
├── wrangler.toml    : 배포 설정
└── README.md        : 배포 가이드
```

### 보안

- voice_id는 서버에서 고정 (클라이언트 변경 불가)
- 텍스트 길이 제한 (100자)
- 8초 타임아웃
- Content-Type 검증

## Cloudflare Worker - Image (Legacy)

> **Note**: Python Backend 사용 권장. Cloudflare Worker는 레거시로 유지됨.

HuggingFace Stable Diffusion API 프록시. 연상 이미지 생성용.

### 배포

```bash
cd cloudflare-worker-image
npm install -g wrangler
wrangler login
wrangler secret put HUGGINGFACE_API_KEY  # HuggingFace API 토큰 입력
wrangler deploy
```

배포 후 URL을 `docs/js/image_association.js`의 `CONFIG.workerUrl`에 설정.

### 구조

```
cloudflare-worker-image/
├── src/index.js     : Worker 코드 (프롬프트 빌드, 타임아웃, CORS)
├── wrangler.toml    : 배포 설정
└── README.md        : 배포 가이드
```

### 이미지 생성 정책

- 같은 단어에 대해 **오답 2회 이상** 시 자동 생성
- 또는 사용자가 수동으로 이미지 버튼 클릭 시
- 단어당 **1회만** 생성 (이후 캐시 사용)
- 프롬프트: "Surreal educational illustration... No text, no letters..."

### 보안

- API 키는 서버에서만 사용
- 단어 길이 제한 (50자)
- 30초 타임아웃
- Content-Type 검증

## Audio Generation

TTS 오디오 사전 생성을 위한 Python 스크립트.

```
generate_audio.py    : ElevenLabs API를 통한 오디오 생성
pyproject.toml       : uv 프로젝트 설정 (Python 의존성 정의)
.python-version      : Python 버전 관리 (uv 자동 설치)
```

생성된 오디오는 `docs/audio/`에 저장되며, 오프라인 사용을 위해 캐싱됨.

### 환경 설정

```bash
# uv 설치 (한 번만)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 동기화 (자동으로 Python 설치 및 가상환경 생성)
uv sync

# TTS 오디오 생성 실행
uv run generate_audio.py
```

## Context Map

- **[Core Logic (src/)](./src/CLAUDE.md)** — 핵심 비즈니스 로직 수정 시
- **[Tests (tests/)](./tests/CLAUDE.md)** — 테스트 작성 및 수정 시
- **[Web UI (docs/)](./docs/)** — 웹 인터페이스 수정 시
- **[Backend (backend/)](./backend/README.md)** — FastAPI 백엔드 수정 시
- **[UV Guide](./UV_GUIDE.md)** — Python/uv 사용법

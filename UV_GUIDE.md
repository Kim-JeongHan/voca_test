# uv 사용 가이드

이 프로젝트는 uv를 사용하여 Python 의존성을 관리합니다.

## 🚀 빠른 시작

### 1. uv 설치 (한 번만)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

설치 후 터미널을 재시작하거나:
```bash
source ~/.bashrc  # or ~/.zshrc
```

### 2. 프로젝트 설정

#### 루트 디렉토리 (TTS 오디오 생성)

```bash
# 의존성 동기화 (자동으로 Python 3.12 설치 및 가상환경 생성)
uv sync --no-build-isolation

# TTS 오디오 생성 실행
uv run generate_audio.py
```

#### Backend (FastAPI)

```bash
cd backend

# 의존성 동기화
uv sync --no-build-isolation

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집하여 API 키 입력

# DB 초기화
uv run python init_db.py --sample

# 서버 시작
uv run uvicorn app.main:app --reload

# 테스트 실행
PYTHONPATH=/home/jeong/workspace/voca_test/backend uv run pytest

# 커버리지 포함 테스트
PYTHONPATH=/home/jeong/workspace/voca_test/backend uv run pytest --cov=app
```

## 📦 주요 명령어

### 의존성 관리

```bash
# 의존성 동기화 (pyproject.toml 기반)
uv sync

# 빌드 격리 없이 동기화 (스크립트 프로젝트용)
uv sync --no-build-isolation

# 새 패키지 추가
uv add package-name

# 개발 의존성 추가
uv add --dev package-name

# 패키지 제거
uv remove package-name
```

### 스크립트 실행

```bash
# Python 스크립트 실행
uv run python script.py

# 모듈 실행
uv run python -m module_name

# uvicorn 실행
uv run uvicorn app.main:app --reload

# pytest 실행
uv run pytest
```

### 가상환경 관리

```bash
# 가상환경 활성화 (선택사항 - uv run으로 자동 처리됨)
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 가상환경 비활성화
deactivate

# 가상환경 삭제
rm -rf .venv
```

## 🔧 문제 해결

### 문제: ModuleNotFoundError

```bash
# Backend에서 app 모듈을 찾을 수 없는 경우
PYTHONPATH=/path/to/backend uv run python script.py
```

### 문제: Build 에러

```bash
# 스크립트 프로젝트에서 빌드 에러가 발생하는 경우
uv sync --no-build-isolation
```

### 문제: Python 버전 문제

```bash
# .python-version 파일 확인
cat .python-version

# uv가 자동으로 해당 버전 설치
```

## 📊 프로젝트 구조

```
voca_test/
├── pyproject.toml       # 루트 프로젝트 설정 (TTS 스크립트)
├── .python-version      # Python 3.12
├── .venv/              # 루트 가상환경
├── generate_audio.py   # TTS 오디오 생성 스크립트
│
└── backend/
    ├── pyproject.toml   # Backend 프로젝트 설정
    ├── .python-version  # Python 3.12
    ├── .venv/          # Backend 가상환경
    └── app/            # FastAPI 애플리케이션
```

## ⚡ uv vs pip 성능 비교

| 작업 | pip | uv | 속도 향상 |
|------|-----|----|----|
| 의존성 설치 | ~30초 | ~3초 | **10배** |
| 가상환경 생성 | ~5초 | ~1초 | **5배** |
| 의존성 해결 | ~10초 | ~1초 | **10배** |

## 🎯 uv 장점

1. **빠른 속도**: Rust로 작성되어 pip보다 10-100배 빠름
2. **자동 Python 관리**: `.python-version` 파일 기반으로 Python 자동 설치
3. **Lock 파일**: `uv.lock`으로 재현 가능한 빌드 보장
4. **간편한 사용**: `uv run`으로 가상환경 활성화 없이 실행
5. **호환성**: pip, requirements.txt와 호환

## 📚 더 알아보기

- [uv 공식 문서](https://github.com/astral-sh/uv)
- [pyproject.toml 가이드](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)

## 💡 팁

### 기존 pip 워크플로우와 함께 사용

uv와 pip를 같이 사용할 수 있습니다:

```bash
# uv로 의존성 관리
uv sync

# 가상환경 활성화 후 pip 사용
source .venv/bin/activate
pip list
```

### CI/CD에서 사용

```yaml
# GitHub Actions 예시
- name: Install uv
  run: |
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "$HOME/.cargo/bin" >> $GITHUB_PATH

- name: Sync dependencies
  run: uv sync --no-build-isolation

- name: Run tests
  run: uv run pytest
```

## ❓ 자주 묻는 질문

**Q: requirements.txt는 어떻게 되나요?**
A: 호환성을 위해 requirements.txt를 유지하고 있지만, uv는 pyproject.toml을 우선 사용합니다.

**Q: 가상환경을 수동으로 활성화해야 하나요?**
A: 아니요! `uv run` 명령어가 자동으로 가상환경을 사용합니다.

**Q: pip로 설치한 패키지가 있는데요?**
A: `uv sync`를 실행하면 pyproject.toml 기준으로 재동기화됩니다.

**Q: uv.lock 파일은 커밋해야 하나요?**
A: 네! 재현 가능한 빌드를 위해 uv.lock을 git에 커밋하세요.

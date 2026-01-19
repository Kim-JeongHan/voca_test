# CLAUDE.md - voca_test

## Project Context

C++ 단어 학습 프로그램. CSV 단어장을 로드하여 퀴즈/테스트를 수행하고 오답을 관리한다.

## Tech Stack

- Language: C++17
- Build System: CMake 3.10+
- Linter: clang-format (v16)
- Pre-commit: pre-commit hooks enabled

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
- 하드코딩된 경로 사용 금지 (`../words/` 패턴 유지)

## Standards & References

### File Naming

- Headers: `include/voca_test/{module}.hpp`
- Sources: `src/{module}.cpp`
- Tests: `tests/test_{module}.cpp`

### Git Convention

- Commit prefix: `:sparkles:` (feature), `:bug:` (fix), `:recycle:` (refactor)
- Branch: feature/*, bugfix/*, refactor/*

### Maintenance Policy

코드와 규칙 간 괴리 발생 시 CLAUDE.md 업데이트를 제안할 것.

## Architecture Overview

```
TestVoca (Facade)
    |
    +-- VocaLoader      : CSV 파일 로딩
    +-- VocaRepository  : 단어 데이터 저장소
    +-- VocaEngine      : 채점 로직
    +-- VocaResult      : 점수/오답 관리
    +-- VocaSaver       : 결과 저장
    +-- VocaSession     : 세션 상태 관리
```

## Context Map

- **[Core Logic (src/)](./src/CLAUDE.md)** — 핵심 비즈니스 로직 수정 시
- **[Tests (tests/)](./tests/CLAUDE.md)** — 테스트 작성 및 수정 시

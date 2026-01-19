# src/CLAUDE.md - Core Implementation

## Module Context

핵심 비즈니스 로직 구현부. 모든 클래스는 `include/voca_test/`의 헤더를 구현한다.

## Module Structure

| File | Class | Responsibility |
|------|-------|----------------|
| voca.cpp | TestVoca | Facade, 전체 흐름 제어 |
| voca_loader.cpp | VocaLoader | CSV 파싱 및 로딩 |
| voca_repository.cpp | VocaRepository | 단어 데이터 저장/조회 |
| voca_engine.cpp | VocaTestEngine | 정답 비교 로직 |
| voca_result.cpp | VocaResult | 점수 및 오답 관리 |
| voca_saver.cpp | VocaSaver | 결과 CSV 저장 |
| voca_session.cpp | VocaSession | 세션 상태 관리 |

## Implementation Patterns

### Include 순서

```cpp
#include "voca_test/{header}.hpp"  // 1. 자체 헤더
#include <standard_lib>             // 2. 표준 라이브러리
#include <third_party>              // 3. 서드파티 (해당 시)
```

### 에러 처리

- 파일 없음: 빈 벡터 반환 또는 예외
- 잘못된 CSV 형식: 해당 라인 스킵

### 채점 로직 (VocaTestEngine::isCorrect)

1. 공백 제거
2. 따옴표 제거
3. 쉼표 구분 복수 정답 처리
4. 정렬 후 비교

## Local Golden Rules

### Do's

- 새 멤버 함수는 헤더에 선언 후 구현
- private 멤버는 `_` suffix 사용
- const 참조로 파라미터 전달

### Don'ts

- 전역 변수 사용 금지
- cout 직접 호출 최소화 (TestVoca에서만 출력)
- 순환 의존성 금지

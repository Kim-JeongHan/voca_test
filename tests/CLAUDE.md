# tests/CLAUDE.md - Test Suite

## Module Context

단위 테스트 모음. 각 핵심 모듈별 테스트 파일 존재.

## Test Files

- test_loader.cpp — VocaLoader CSV 파싱 테스트
- test_engine.cpp — VocaTestEngine 채점 로직 테스트
- test_result.cpp — VocaResult 점수 관리 테스트
- test_session.cpp — VocaSession 세션 관리 테스트
- test_regression.cpp — 회귀 테스트

## Operational Commands

```bash
# 전체 테스트
cd build && ctest --output-on-failure

# 개별 테스트
./build/test_engine
./build/test_loader
./build/test_result
./build/test_session
./build/test_regression
```

## Implementation Patterns

### 테스트 구조

```cpp
#include "voca_test/{module}.hpp"
#include <cassert>
#include <iostream>

void test_case_name() {
    // Arrange
    // Act
    // Assert using assert()
}

int main() {
    test_case_name();
    std::cout << "All tests passed!" << std::endl;
    return 0;
}
```

### Naming Convention

- 파일: `test_{module}.cpp`
- 함수: `test_{feature}_{scenario}()`

## Local Golden Rules

### Do's

- 각 테스트 함수는 독립적으로 실행 가능해야 함
- assert 실패 시 명확한 메시지 출력
- 엣지 케이스 포함 (빈 입력, 특수문자 등)

### Don'ts

- 테스트 간 상태 공유 금지
- 실제 파일 시스템 의존 최소화
- 하드코딩된 절대 경로 사용 금지

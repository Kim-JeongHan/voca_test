
# A. 디렉터리 구조 & 헤더 파일 설계

## A-00_설계 원칙

* **기존 include/voca_test/voca.hpp 유지**
* 외부 공개 API는 최소화
* 내부 구현은 `detail/` 또는 `core/` 성격으로 분리
* 헤더–소스 1:1 매칭 유지

---

## A-01_목표 디렉터리 구조

```text
voca_test/
├─ include/
│  └─ voca_test/
│     ├─ voca.hpp                # 기존 외부 API (Facade)
│     ├─ voca_loader.hpp         # CSV 로딩
│     ├─ voca_repository.hpp     # 단어 데이터 저장소
│     ├─ voca_engine.hpp         # 출제/채점 로직
│     ├─ voca_result.hpp         # 점수/오답 관리
│     └─ voca_saver.hpp          # 결과 저장
│
├─ src/
│  ├─ voca.cpp                   # TestVoca 구현 (Facade)
│  ├─ voca_loader.cpp
│  ├─ voca_repository.cpp
│  ├─ voca_engine.cpp
│  ├─ voca_result.cpp
│  └─ voca_saver.cpp
│
├─ words/
│  └─ *.csv
│
├─ tests/
│  ├─ test_engine.cpp            # 채점 로직 테스트
│  ├─ test_loader.cpp            # CSV 파싱 테스트
│  ├─ test_result.cpp            # 점수/오답 테스트
│  └─ test_regression.cpp        # 전체 동작 회귀 테스트
│
├─ simple_main.cpp
├─ multiple_main.cpp
├─ CMakeLists.txt
└─ README.md
```

---

## A-02_헤더 책임 요약 표

| 파일                  | 책임               |
| ------------------- | ---------------- |
| voca.hpp            | 외부 API, 실행 진입점   |
| voca_loader.hpp     | CSV 파일 → (단어, 뜻) |
| voca_repository.hpp | 단어 데이터 보관        |
| voca_engine.hpp     | 채점 알고리즘          |
| voca_result.hpp     | 점수·오답 상태         |
| voca_saver.hpp      | 결과 파일 출력         |

---

## A-03_각 헤더의 최소 인터페이스 설계

### voca_loader.hpp

```cpp
#pragma once
#include <string>
#include <vector>

namespace voca {

class VocaLoader {
public:
    bool loadCSV(const std::string& path,
                 std::vector<std::pair<std::string, std::string>>& out);
};

}
```

---

### voca_repository.hpp

```cpp
#pragma once
#include <vector>
#include <string>

namespace voca {

class VocaRepository {
public:
    void set(std::vector<std::pair<std::string, std::string>>&& data);
    size_t size() const;
    const std::pair<std::string, std::string>& at(size_t idx) const;

private:
    std::vector<std::pair<std::string, std::string>> data_;
};

}
```

---

### voca_engine.hpp

```cpp
#pragma once
#include <string>

namespace voca {

class VocaTestEngine {
public:
    bool isCorrect(const std::string& answer,
                   const std::string& correct) const;

private:
    std::string normalize_(const std::string& s) const;
};

}
```

---

### voca_result.hpp

```cpp
#pragma once
#include <vector>
#include <string>

namespace voca {

struct WrongVoca {
    std::string word;
    std::string correct;
};

class VocaResult {
public:
    void markCorrect();
    void markWrong(const WrongVoca& w);

    int score() const;
    int total() const;
    const std::vector<WrongVoca>& wrongList() const;

private:
    int correct_{0};
    int total_{0};
    std::vector<WrongVoca> wrong_;
};

}
```

---

### voca_saver.hpp

```cpp
#pragma once
#include <string>
#include <vector>
#include "voca_result.hpp"

namespace voca {

class VocaSaver {
public:
    bool saveWrongCSV(const std::string& base_name,
                      const std::vector<WrongVoca>& list,
                      int mode);
};

}
```

---

## A-04_voca.hpp (Facade 유지 전략)

```cpp
#pragma once

namespace voca {

class TestVoca {
public:
    TestVoca(/* 기존 생성자 시그니처 유지 */);
    void runTest();

private:
    // 내부 객체 조합
};

}
```

> 외부 사용자는 **리팩토링 사실을 전혀 인지하지 못함**

---

# D. 리팩토링 후 테스트 전략

## D-00_테스트 목표

* 리팩토링 전/후 **동작 완전 동일 보장**
* 기능 단위 테스트 + 전체 흐름 회귀 테스트 병행
* 테스트 프레임워크 없이도 실행 가능한 구조 유지

---

## D-01_테스트 레벨 분류

| 레벨               | 목적           |
| ---------------- | ------------ |
| Unit Test        | 개별 로직 검증     |
| Integration Test | 클래스 조합 검증    |
| Regression Test  | 기존 결과 동일성 검증 |

---

## D-02_Unit Test 설계

### 1️⃣ 채점 로직 테스트 (`test_engine.cpp`)

테스트 항목:

* 공백 무시
* 따옴표 제거
* 복수 정답 처리
* 순서 무관 비교

```cpp
assert(engine.isCorrect("apple", "apple"));
assert(engine.isCorrect("a,b", "b,a"));
assert(engine.isCorrect(" \"dog\" ", "dog"));
assert(!engine.isCorrect("cat", "dog"));
```

---

### 2️⃣ CSV 파싱 테스트 (`test_loader.cpp`)

* 정상 CSV
* 빈 줄
* 쉼표 포함 의미
* 파일 없음

```cpp
assert(loader.loadCSV("test.csv", out));
assert(out.size() == 10);
```

---

### 3️⃣ 결과 관리 테스트 (`test_result.cpp`)

* 점수 증가
* 오답 저장
* total count 일관성

---

## D-03_Integration Test

### 목적

* `Loader → Repository → Engine → Result` 흐름 검증

```cpp
VocaLoader loader;
VocaRepository repo;
VocaTestEngine engine;
VocaResult result;
```

* 실제 입력 없이 mock answer 사용
* 콘솔 출력 없이 로직만 검증

---

## D-04_Regression Test (가장 중요)

### 핵심 원칙

> **리팩토링 전 결과 == 리팩토링 후 결과**

#### 방법

1. 기존 실행 결과 저장

```bash
./run.sh simple 1 > before.txt
```

2. 리팩토링 후 동일 실행

```bash
./run.sh simple 1 > after.txt
diff before.txt after.txt
```

3. 저장된 CSV 파일 비교

```bash
diff words/xxx_wrong.csv words/xxx_wrong_new.csv
```

---

## D-05_테스트 자동화 옵션 (선택)

* CMake `add_executable(test_engine ...)`
* `ctest` 연동 가능
* CI 전환 시에도 그대로 사용 가능

---

## D-06_완료 체크리스트

* 모든 unit test 통과
* regression diff 없음
* `simple_main.cpp`, `multiple_main.cpp` 수정 최소
* clang-format 적용 후 가독성 개선


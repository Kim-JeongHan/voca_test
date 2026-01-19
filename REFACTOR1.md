# voca_test 클래스 분리 리팩토링 계획서

## 00_목표

본 리팩토링의 목표는 다음과 같다.

* 현재 동작을 **100% 유지**한다
* 단일 클래스에 집중된 책임을 분리한다
* 이후 기능 추가(출제 전략, 학습 이력, UI 확장)를 **구조 변경 없이** 가능하게 만든다
* C++ 초급~중급 수준에서도 유지보수 가능한 구조를 만든다

---

## 01_현 구조 문제 정의

### 01-1. 현재 `TestVoca`의 책임 과다

`TestVoca` 클래스는 아래 역할을 모두 수행하고 있다.

* CSV 파일 경로 구성
* 파일 I/O 및 파싱
* 단어 데이터 보관
* 출제 순서 결정
* 사용자 입력 처리
* 채점 로직
* 점수 계산
* 오답 관리
* 결과 출력
* CSV 저장

이는 **Single Responsibility Principle(SRP)** 위반 상태이다.

---

### 01-2. 문제점 정리

* 기능 추가 시 `voca.cpp`가 비대해짐
* 테스트 로직과 I/O 로직이 강하게 결합됨
* 출제/채점 방식 변경이 전체 코드 수정으로 이어짐
* 다른 UI(CLI → GUI, Web)로 재사용하기 어려움

---

## 02_리팩토링 기본 전략

### 02-1. 핵심 원칙

* **행위 중심 분리** (데이터 / 로직 / I/O)
* 상속 최소화, **구성(composition)** 중심
* STL 컨테이너 유지
* 예외 대신 return-based error handling 유지 (현재 스타일 존중)

---

### 02-2. 분리 기준

| 구분 기준 | 설명            |
| ----- | ------------- |
| 데이터   | 단어, 뜻, 통계     |
| 로직    | 출제, 채점        |
| I/O   | 파일 로딩, 저장, 출력 |
| 실행    | 모드 제어, 흐름 제어  |

---

## 03_목표 클래스 구조

### 03-1. 전체 구조 개요

```
TestVoca (Facade)
 ├─ VocaLoader
 ├─ VocaRepository
 ├─ VocaTestEngine
 ├─ VocaResult
 └─ VocaSaver
```

> `TestVoca`는 **외부 API를 유지하기 위한 Facade 역할**만 담당한다.

---

## 04_클래스별 책임 정의

### 04-1. `VocaLoader` (파일 로딩 전담)

**책임**

* CSV 파일 읽기
* 문자열 파싱
* 에러 검증

**주요 인터페이스**

```cpp
class VocaLoader {
public:
    bool load(const std::string& path,
              std::vector<std::pair<std::string, std::string>>& out);
};
```

**비고**

* `../words/` 경로 규칙은 여기서만 관리
* 테스트 시 mock 가능

---

### 04-2. `VocaRepository` (단어 데이터 보관)

**책임**

* 단어/뜻 데이터 보관
* 인덱스 접근 제공

```cpp
class VocaRepository {
public:
    void set(std::vector<std::pair<std::string, std::string>>&& data);
    size_t size() const;
    const std::pair<std::string, std::string>& at(size_t idx) const;
};
```

---

### 04-3. `VocaTestEngine` (출제 & 채점)

**책임**

* 문제 순서 생성
* 입력 정규화
* 정답 비교 로직

```cpp
class VocaTestEngine {
public:
    bool testOne(const std::string& answer,
                 const std::string& correct) const;
};
```

**포함 로직**

* 공백 제거
* 따옴표 제거
* 복수 정답(쉼표) 처리
* 정렬 후 비교

> 이후 전략 패턴 확장 포인트

---

### 04-4. `VocaResult` (결과 상태 관리)

**책임**

* 점수 계산
* 오답 목록 관리

```cpp
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
};
```

---

### 04-5. `VocaSaver` (결과 저장)

**책임**

* 결과 CSV 저장
* 모드별 파일명 규칙 관리

```cpp
class VocaSaver {
public:
    bool saveWrong(const std::string& base,
                   const std::vector<WrongVoca>& list,
                   int mode);
};
```

---

## 05_TestVoca의 최종 역할

### 05-1. Facade 패턴 적용

`TestVoca`는 다음만 담당한다.

* 객체 조합
* 모드 분기
* 전체 실행 흐름 제어

```cpp
class TestVoca {
public:
    void runTest();

private:
    VocaLoader loader_;
    VocaRepository repo_;
    VocaTestEngine engine_;
    VocaResult result_;
    VocaSaver saver_;
};
```

---

## 06_단계별 리팩토링 계획

### Step 1. 로직 추출 (기능 변경 없음)

* 채점 함수 분리 → `VocaTestEngine`
* 오답 벡터 분리 → `VocaResult`

### Step 2. I/O 분리

* CSV 로딩 → `VocaLoader`
* 저장 → `VocaSaver`

### Step 3. Facade 정리

* `TestVoca`는 기존 API 유지
* `simple_main.cpp`, `multiple_main.cpp` 수정 없음

---

## 07_리팩토링 완료 기준

* 기존 실행 결과와 **완전히 동일**
* diff 기준:

  * `simple_main.cpp`, `multiple_main.cpp` 변경 최소
* 각 클래스 파일이 **200줄 이하**
* 이후 기능 추가 시 기존 클래스 수정 없이 확장 가능

---

## 08_향후 확장 포인트 명시

* `VocaTestEngine` → 출제 전략 분리
* `VocaRepository` → 통계 데이터 추가
* `VocaSaver` → JSON 저장 추가
* UI 레이어 분리 (CLI / GUI)


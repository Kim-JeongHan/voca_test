# voca_test

단어 학습용 C++ 프로젝트입니다. CSV 단어장을 읽어 퀴즈/테스트를 수행하는 프로그램을 빌드합니다.

## 프로젝트 구조
- include/voca_test/voca.hpp: 외부 API(Facade)
- include/voca_test/voca_loader.hpp: CSV 로딩
- include/voca_test/voca_repository.hpp: 단어 데이터 저장소
- include/voca_test/voca_engine.hpp: 채점 로직
- include/voca_test/voca_result.hpp: 점수/오답 관리
- include/voca_test/voca_saver.hpp: 결과 저장
- src/voca.cpp: `TestVoca` 흐름 제어
- src/voca_loader.cpp: CSV 로딩 구현
- src/voca_repository.cpp: 저장소 구현
- src/voca_engine.cpp: 채점 구현
- src/voca_result.cpp: 결과 관리 구현
- src/voca_saver.cpp: 저장 구현
- src/simple_main.cpp: 단일 테스트 실행 예제
- src/multiple_main.cpp: 여러 단어장 테스트 실행 예제
- words/: 학습용 CSV 단어장

## 빌드 방법
### 스크립트 사용
```bash
./build.sh
```

### 직접 CMake 실행
```bash
cmake -S . -B build
cmake --build build
```

## 테스트
로컬 테스트 실행:

```bash
./build.sh
./run.sh --test
```

## CI (GitHub Actions)
`push`/`pull_request` 시 자동으로 빌드와 테스트를 수행합니다.

- 설정 파일: [.github/workflows/ci.yml](.github/workflows/ci.yml)

## 실행 예시
`run.sh`를 사용하면 실행 경로를 자동으로 맞춰줍니다.

```bash
./run.sh simple 1
./run.sh multiple 1 2 3
```

모드를 미리 지정하려면 `MODE` 환경 변수를 사용합니다.

```bash
MODE=0 ./run.sh simple 1
MODE=1 ./run.sh multiple 1 2 3
```

## 단어장 형식
`words/` 폴더의 CSV 파일을 사용합니다. 각 줄은 `단어,뜻` 형식입니다.

## 내부 로직 요약
- [include/voca_test/voca.hpp](include/voca_test/voca.hpp): `TestVoca` Facade
- [include/voca_test/voca_loader.hpp](include/voca_test/voca_loader.hpp): CSV 로딩
- [include/voca_test/voca_repository.hpp](include/voca_test/voca_repository.hpp): 단어 데이터 저장소
- [include/voca_test/voca_engine.hpp](include/voca_test/voca_engine.hpp): 채점 로직
- [include/voca_test/voca_result.hpp](include/voca_test/voca_result.hpp): 점수/오답 관리
- [include/voca_test/voca_saver.hpp](include/voca_test/voca_saver.hpp): 결과 저장

### 데이터 로딩
1. 생성자에서 `../words/` 경로와 파일 번호(또는 파일명 리스트)를 받아 CSV 기본 경로를 구성합니다.
2. `VocaLoader::loadCSV()`가 각 CSV의 라인을 읽어 `단어,뜻`으로 분리해 저장합니다.
3. `VocaRepository`에 단어 목록을 보관합니다.

### 테스트 진행 흐름 (`runTest()`)
1. 단어 인덱스를 셔플해 출제 순서를 랜덤화합니다.
2. 모드 선택(`mode_()`):
	 - 연습 모드(0): 전체 단어 테스트 → 오답만 재시험 → 최종 오답 저장
	 - 테스트 모드(1): 고정 크기(`test_size_`=100) 시험 → 오답 저장

### 오답 즉시 반복 & 힌트 단계
- 틀린 단어는 즉시 재출제됩니다(세션 내에서 빠져나가지 못함).
- 틀릴수록 힌트가 강화됩니다.
	- 1회: 글자 수 공개
	- 2회: 첫 글자 공개
	- 3회: 앞부분 일부 공개
	- 4회 이상: 정답 공개 후 재입력 요구

### 답안 채점 방식 (`Test_()`)
`VocaTestEngine::isCorrect()` 기준으로 채점합니다.

- 입력 답안과 정답에서 공백을 제거합니다.
- 정답이 따옴표로 감싸져 있으면 앞/뒤 따옴표를 제거합니다.
- 정답에 쉼표가 포함된 경우 복수 정답으로 간주하고, 답안/정답을 쉼표로 분리해 정렬 후 비교합니다.
- 불일치 시 오답 리스트에 추가하고 정답을 출력합니다.

### 결과 출력 및 저장
- `printScore_()`에서 `점수 / 총문항`을 출력합니다.
- `printWrongVoca_()`에서 오답 리스트를 출력합니다.
- `VocaSaver::saveWrongCSV()`가 모드에 따라 다음 파일로 저장합니다.
	- 연습 모드: `{원본파일}_wrong.csv`
	- 테스트 모드: `{원본파일}_test.csv`

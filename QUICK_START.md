# Quick Start Guide - FastAPI Backend

## 🚀 5분 안에 시작하기

### Option 1: Docker Compose (가장 쉬움)

```bash
# 1. 환경 변수 복사
cp backend/.env.example backend/.env

# 2. API 키 입력 (선택사항 - 테스트는 키 없이 가능)
nano backend/.env

# 3. 실행
docker-compose up -d

# 4. 접속
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
# Frontend: http://localhost:3000
```

### Option 2: Python 로컬 실행

```bash
# 1. 가상환경 생성
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경 설정
cp .env.example .env

# 4. DB 초기화 (샘플 데이터 포함)
python init_db.py --sample

# 5. 서버 시작
uvicorn app.main:app --reload

# 6. 접속
# http://localhost:8000/docs
```

## 📚 첫 API 호출

### 1. Swagger UI 사용 (추천)

1. http://localhost:8000/docs 접속
2. 각 엔드포인트 클릭
3. "Try it out" 버튼
4. 파라미터 입력
5. "Execute" 실행

### 2. cURL 사용

```bash
# 단어장 목록
curl http://localhost:8000/api/v1/decks

# 세션 시작 (샘플 데이터 사용)
curl -X POST http://localhost:8000/api/v1/session/start \
  -H "Content-Type: application/json" \
  -d '{"deck_id": 1}'

# 응답 예시:
# {
#   "id": 1,
#   "deck_id": 1,
#   "current_index": 0,
#   "score": 0,
#   "total_questions": 5,
#   "is_completed": false
# }

# 문제 가져오기
curl http://localhost:8000/api/v1/session/1/prompt

# 응답 예시:
# {
#   "word": "escape",
#   "index": 0,
#   "progress": "1/5",
#   "total": 5,
#   "current": 1
# }

# 답안 제출
curl -X POST http://localhost:8000/api/v1/session/1/submit \
  -H "Content-Type: application/json" \
  -d '{"answer": "탈출하다", "hint_used": 0}'

# 응답 예시:
# {
#   "is_correct": true,
#   "correct_answer": "탈출하다",
#   "score": 1,
#   "progress": "1/5"
# }
```

### 3. Python 스크립트

```python
import requests

BASE = 'http://localhost:8000/api/v1'

# 세션 시작
r = requests.post(f'{BASE}/session/start', json={'deck_id': 1})
session_id = r.json()['id']
print(f'Session started: {session_id}')

# 퀴즈 플로우
while True:
    # 문제
    r = requests.get(f'{BASE}/session/{session_id}/prompt')
    if r.status_code == 404:  # 완료
        break

    prompt = r.json()
    print(f"\nQ{prompt['current']}/{prompt['total']}: {prompt['word']}")

    # 답변
    answer = input('Your answer: ')
    r = requests.post(f'{BASE}/session/{session_id}/submit',
                      json={'answer': answer, 'hint_used': 0})
    result = r.json()

    if result['is_correct']:
        print('✅ Correct!')
    else:
        print(f'❌ Wrong! Answer: {result["correct_answer"]}')
    print(f'Score: {result["score"]}')

# 요약
r = requests.get(f'{BASE}/session/{session_id}/summary')
summary = r.json()
print(f'\n=== Summary ===')
print(f'Score: {summary["score"]}/{summary["total_questions"]} ({summary["percentage"]}%)')
print(f'Wrong words: {", ".join(summary["wrong_words"])}')
```

## 📤 CSV 단어장 업로드

### 1. CSV 파일 준비

```csv
word,meaning
escape,탈출하다
abandon,버리다
achieve,성취하다
```

### 2. 업로드

**cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/decks/upload \
  -F "file=@mywords.csv" \
  -F "name=My Vocabulary" \
  -F "description=Custom word list"
```

**Swagger UI:**
1. http://localhost:8000/docs
2. `POST /api/v1/decks/upload`
3. "Try it out"
4. 파일 선택
5. Execute

**Python:**
```python
import requests

files = {'file': open('mywords.csv', 'rb')}
data = {'name': 'My Vocabulary', 'description': 'Custom word list'}

r = requests.post('http://localhost:8000/api/v1/decks/upload',
                  files=files, data=data)
print(r.json())
```

## 🎯 주요 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/` | 루트 |
| GET | `/health` | 헬스체크 |
| GET | `/docs` | API 문서 (Swagger) |
| POST | `/api/v1/tts` | TTS 생성 |
| POST | `/api/v1/image` | 이미지 생성 |
| GET | `/api/v1/decks` | 단어장 목록 |
| POST | `/api/v1/decks/upload` | CSV 업로드 |
| POST | `/api/v1/session/start` | 세션 시작 |
| GET | `/api/v1/session/{id}/prompt` | 문제 |
| POST | `/api/v1/session/{id}/submit` | 답안 제출 |
| GET | `/api/v1/session/{id}/summary` | 요약 |

## 🔧 문제 해결

### 포트 충돌
```bash
# 다른 포트 사용
uvicorn app.main:app --port 8080
```

### DB 초기화
```bash
rm backend/voca.db
python backend/init_db.py --sample
```

### Docker 재시작
```bash
docker-compose down
docker-compose up -d --build
```

### 로그 확인
```bash
# Docker
docker-compose logs -f backend

# Python
# 서버 터미널 확인
```

## 📖 다음 단계

1. ✅ 백엔드 실행 완료
2. 📚 [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - 프론트엔드 연결
3. 📘 [backend/README.md](backend/README.md) - 상세 문서
4. 🚀 배포 가이드 참고

## 💡 팁

- **API 키 없이 테스트**: TTS/Image 제외한 모든 기능 사용 가능
- **샘플 데이터**: `--sample` 플래그로 5개 단어 자동 생성
- **자동 문서**: `/docs` 에서 모든 API 인터랙티브 테스트
- **DB 탐색**: SQLite GUI 도구로 `voca.db` 확인 가능

## 🎉 완료!

백엔드가 정상 작동하면 프론트엔드 연결을 시작하세요!

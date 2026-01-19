# Voca TTS Proxy - Cloudflare Worker

ElevenLabs TTS API 프록시. API 키를 서버 측에 안전하게 보관합니다.

## 배포 방법

### 1. Wrangler CLI 설치
```bash
npm install -g wrangler
```

### 2. Cloudflare 로그인
```bash
wrangler login
```

### 3. API 키 설정
```bash
cd cloudflare-worker
wrangler secret put ELEVENLABS_API_KEY
# 프롬프트에서 .env 파일의 API 키 입력
```

### 4. 배포
```bash
wrangler deploy
```

### 5. URL 확인
배포 후 출력되는 URL을 `docs/js/tts.js`의 `CONFIG.workerUrl`에 설정:
```
https://voca-tts-proxy.<your-subdomain>.workers.dev
```

## API 사용법

### Request
```bash
curl -X POST https://voca-tts-proxy.xxx.workers.dev \
  -H "Content-Type: application/json" \
  -d '{"text": "hello", "voice_id": "JBFqnCBsd6RMkjVDRZzb"}' \
  --output test.mp3
```

### Response
- Success: `audio/mpeg` binary
- Error: JSON `{"error": "message"}`

## Voice IDs

| Voice | ID | Language |
|-------|-----|----------|
| George | JBFqnCBsd6RMkjVDRZzb | English |
| Rachel | 21m00Tcm4TlvDq8ikWAM | English |

더 많은 음성: https://elevenlabs.io/voice-library

# Stable Diffusion Local Setup

AUTOMATIC1111 Stable Diffusion WebUI를 Docker로 실행하여 로컬에서 이미지를 생성합니다.

## 📊 현재 상태

- ✅ Docker 컨테이너: 실행 중
- ⏳ 패키지 설치: PyTorch 2.2GB 다운로드 중 (2200.7 MB)
- ⏳ 모델 다운로드: 대기 중
- ⏳ WebUI API: 준비 중

**예상 완료 시간**: 10-20분 (첫 실행)
**현재 버전**: Stable Diffusion WebUI v1.10.1

## 사전 준비

### GPU가 있는 경우 (권장)
```bash
# NVIDIA Docker 설치 확인
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### GPU가 없는 경우 (CPU 모드)
docker-compose.yml에서 GPU 관련 설정을 제거하고 CPU 모드로 실행합니다.

## 설치 및 실행

### 1. Docker Compose로 실행

```bash
# Stable Diffusion WebUI 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f stable-diffusion
```

처음 실행 시 모델을 자동으로 다운로드합니다 (약 4GB, 시간이 걸릴 수 있음).

### 2. WebUI 접속

브라우저에서 http://localhost:7860 으로 접속하여 정상 동작 확인

### 3. API 테스트

```bash
# API 엔드포인트 확인
curl http://localhost:7860/sdapi/v1/sd-models

# 이미지 생성 테스트
node test_sd_local.js apple
```

## API 엔드포인트

- **WebUI**: http://localhost:7860
- **API 문서**: http://localhost:7860/docs
- **텍스트→이미지**: http://localhost:7860/sdapi/v1/txt2img

## 중지 및 재시작

```bash
# 중지
docker-compose down

# 재시작
docker-compose restart

# 완전 삭제 (모델 파일 포함)
docker-compose down -v
rm -rf sd-models sd-outputs
```

## CPU 모드로 실행 (GPU 없는 경우)

docker-compose.yml을 다음과 같이 수정:

```yaml
version: '3.8'

services:
  stable-diffusion:
    image: universonic/stable-diffusion-webui:latest
    container_name: sd-webui
    ports:
      - "7860:7860"
    environment:
      - CLI_ARGS=--api --listen --port 7860 --skip-torch-cuda-test --no-half --precision full --use-cpu all
    volumes:
      - ./sd-models:/app/stable-diffusion-webui/models
      - ./sd-outputs:/app/stable-diffusion-webui/outputs
    restart: unless-stopped
```

**참고**: CPU 모드는 매우 느립니다 (이미지 1장당 5-10분 이상).

## 문제 해결

### 메모리 부족
- GPU VRAM이 부족한 경우: `--lowvram` 또는 `--medvram` 플래그 추가
- RAM이 부족한 경우: 작은 모델 사용

### 모델 수동 다운로드
```bash
# sd-models 폴더 생성
mkdir -p sd-models/Stable-diffusion

# 모델 다운로드 (예: Stable Diffusion 1.5)
cd sd-models/Stable-diffusion
wget https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors
```

## 성능 최적화

### xformers 활성화 (GPU만 해당)
```yaml
environment:
  - CLI_ARGS=--api --listen --xformers
```

### 더 빠른 샘플러 사용
테스트 스크립트에서 `sampler_name: "DPM++ 2M Karras"` 사용

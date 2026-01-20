# Voca Image Proxy - Cloudflare Worker

HuggingFace Stable Diffusion API proxy for vocabulary association images.

## Features

- Keeps HuggingFace API key secure on server-side
- Generates association images for vocabulary words
- CORS headers for PWA access
- Input validation (word length limit)
- Timeout handling (30 seconds)
- Model loading retry support

## Deployment

1. Install Wrangler CLI:
```bash
npm install -g wrangler
```

2. Login to Cloudflare:
```bash
wrangler login
```

3. Set your HuggingFace API key:
```bash
wrangler secret put HUGGINGFACE_API_KEY
# Enter your HuggingFace API token when prompted
```

4. Deploy:
```bash
wrangler deploy
```

5. Note the deployed URL (e.g., `https://voca-image-proxy.<your-subdomain>.workers.dev`)

6. Update `docs/js/image_association.js` with the Worker URL.

## API Usage

### Request

```bash
POST https://voca-image-proxy.<subdomain>.workers.dev/
Content-Type: application/json

{
  "word": "escape"
}
```

### Response (Success)

- **Status**: 200
- **Content-Type**: image/png
- **Body**: PNG image binary

### Response (Model Loading)

- **Status**: 503
- **Body**: `{"error": "Model is loading", "estimated_time": 20, "retry": true}`

Client should retry after `estimated_time` seconds.

### Response (Error)

- **Status**: 400/502/504/500
- **Body**: `{"error": "error message"}`

## Getting HuggingFace API Key

1. Go to https://huggingface.co/
2. Sign up or log in
3. Go to Settings > Access Tokens
4. Create a new token with "Read" permission
5. Copy the token

## Rate Limits

HuggingFace free tier has rate limits. The PWA is designed to:
- Only generate images for words with 2+ wrong attempts
- Cache images permanently to avoid re-generation
- Fail silently without disrupting quiz flow

## Model

Uses `stabilityai/stable-diffusion-xl-base-1.0` for high-quality image generation.

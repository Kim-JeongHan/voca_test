# Voca GitHub Proxy - Cloudflare Worker

GitHub API proxy for committing association images to the repository.

## Features

- Commits generated images to `docs/images/` in the repo
- Updates existing images if they already exist
- Returns raw GitHub URL for the committed image

## Deployment

1. Install Wrangler CLI:
```bash
npm install -g wrangler
```

2. Login to Cloudflare:
```bash
wrangler login
```

3. Create a GitHub Personal Access Token:
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scope: `repo` (Full control of private repositories)
   - Copy the token

4. Set your GitHub token:
```bash
wrangler secret put GITHUB_TOKEN
# Paste your GitHub Personal Access Token when prompted
```

5. Update `wrangler.toml` with your GitHub info:
```toml
[vars]
GITHUB_OWNER = "your-username"
GITHUB_REPO = "voca_test"
GITHUB_BRANCH = "master"
```

6. Deploy:
```bash
wrangler deploy
```

7. Note the deployed URL and update `docs/js/image_association.js`.

## API Usage

### Request

```bash
POST https://voca-github-proxy.<subdomain>.workers.dev/
Content-Type: application/json

{
  "word": "escape",
  "imageBase64": "iVBORw0KGgo..."  // Base64 encoded PNG (without data:image/png;base64, prefix)
}
```

### Response (Success)

```json
{
  "success": true,
  "url": "https://raw.githubusercontent.com/owner/repo/master/docs/images/escape.png",
  "path": "docs/images/escape.png"
}
```

### Response (Error)

```json
{
  "error": "error message"
}
```

## Security

- GitHub token is stored securely as a Cloudflare secret
- Word is sanitized (alphanumeric and hyphens only)
- Only PNG images are accepted

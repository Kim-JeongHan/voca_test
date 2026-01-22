# Migration Guide: Node.js → FastAPI

Complete guide for migrating from Cloudflare Workers + PWA to FastAPI backend.

## Overview

**Before:** Node.js Cloudflare Workers (3 workers) + Static PWA
**After:** FastAPI Backend + Updated PWA → Future: Mobile App Support

## Architecture Comparison

### Old Architecture
```
Browser (PWA)
    ↓ Direct API Calls
Cloudflare Workers (Node.js)
    ├── voca-tts-proxy (ElevenLabs)
    ├── voca-image-proxy (HuggingFace)
    └── voca-github-proxy (GitHub)

Data Storage: IndexedDB (Browser Only)
```

### New Architecture
```
Frontend (PWA / Future Mobile App)
    ↓ REST API (JSON)
FastAPI Backend (Python)
    ├── TTS Service (ElevenLabs + Cache)
    ├── Image Service (HuggingFace + Cache)
    ├── Session Service (C++ Engine)
    └── Deck Service (CSV Upload)
    ↓
Database (PostgreSQL / SQLite)
    ├── Users, Decks, Words
    ├── Sessions, Answers
    ├── WrongStats
    └── Caches (Audio, Images)
```

## Migration Steps

### Phase 1: Backend Setup ✅ COMPLETED

All backend infrastructure is ready:
- ✅ FastAPI app with CORS
- ✅ SQLAlchemy models (8 tables)
- ✅ Pydantic schemas (API contracts)
- ✅ Services (TTS, Image, Session)
- ✅ API routes (4 routers)
- ✅ Docker setup
- ✅ C++ engine wrapper (Python fallback)

### Phase 2: Database Initialization

1. **Install dependencies**

**Using uv (Recommended):**
```bash
cd backend

# Install uv (한 번만)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 동기화
uv sync
```

**Using pip:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Initialize database**
```bash
# Using uv
uv run python init_db.py --sample

# Using pip
python init_db.py --sample
```

4. **Verify setup**
```bash
# Using uv
uv run uvicorn app.main:app --reload

# Using pip
uvicorn app.main:app --reload

# Visit: http://localhost:8000/docs
```

### Phase 3: Frontend Migration

The frontend needs to replace:
- IndexedDB → FastAPI REST calls
- Cloudflare Worker URLs → Backend API endpoints

#### 3.1 Create API Client

Create `docs/js/api_client.js`:

```javascript
const API_BASE = 'http://localhost:8000/api/v1';

class VocaAPI {
    async getTTS(text) {
        const res = await fetch(`${API_BASE}/tts`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text})
        });

        if (!res.ok) throw new Error('TTS failed');
        return await res.blob(); // Audio blob
    }

    async getImage(word) {
        const res = await fetch(`${API_BASE}/image`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({word})
        });

        if (!res.ok) throw new Error('Image generation failed');
        return await res.blob(); // Image blob
    }

    async listDecks() {
        const res = await fetch(`${API_BASE}/decks`);
        return await res.json();
    }

    async uploadDeck(file, name, description) {
        const formData = new FormData();
        formData.append('file', file);
        if (name) formData.append('name', name);
        if (description) formData.append('description', description);

        const res = await fetch(`${API_BASE}/decks/upload`, {
            method: 'POST',
            body: formData
        });

        return await res.json();
    }

    async startSession(deckId, wordIndices = null, isWrongOnly = false) {
        const res = await fetch(`${API_BASE}/session/start`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                deck_id: deckId,
                word_indices: wordIndices,
                is_wrong_only: isWrongOnly
            })
        });

        return await res.json();
    }

    async getPrompt(sessionId) {
        const res = await fetch(`${API_BASE}/session/${sessionId}/prompt`);
        return await res.json();
    }

    async submitAnswer(sessionId, answer, hintUsed = 0) {
        const res = await fetch(`${API_BASE}/session/${sessionId}/submit`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({answer, hint_used: hintUsed})
        });

        return await res.json();
    }

    async getSummary(sessionId) {
        const res = await fetch(`${API_BASE}/session/${sessionId}/summary`);
        return await res.json();
    }
}

const api = new VocaAPI();
```

#### 3.2 Update Existing Files

**tts.js** - Replace Cloudflare Worker calls:
```javascript
// OLD
const res = await fetch(CONFIG.workerUrl, {...});

// NEW
const audioBlob = await api.getTTS(text);
const audioUrl = URL.createObjectURL(audioBlob);
// Play audioUrl...
```

**image_association.js** - Replace HuggingFace Worker:
```javascript
// OLD
const res = await fetch(CONFIG.workerUrl, {...});

// NEW
const imageBlob = await api.getImage(word);
const imageUrl = URL.createObjectURL(imageBlob);
// Display imageUrl...
```

**app.js** - Replace JS fallback with API calls:
```javascript
// OLD
async function loadWasm() {
    vocaCore = createJSFallback();
}

// NEW
let currentSessionId = null;

async function startNewSession(deckId) {
    const session = await api.startSession(deckId);
    currentSessionId = session.id;
    return session;
}

async function getNextQuestion() {
    return await api.getPrompt(currentSessionId);
}

async function submitAnswer(answer, hintUsed) {
    return await api.submitAnswer(currentSessionId, answer, hintUsed);
}

async function finishSession() {
    return await api.getSummary(currentSessionId);
}
```

**storage.js** - Simplify to use server state:
```javascript
// Keep IndexedDB only for offline caching
// Remove session/deck management (now server-side)
class VocaStorage {
    // Only cache audio/images locally
    async cacheAudio(text, blob) { ... }
    async getCachedAudio(text) { ... }
    async cacheImage(word, blob) { ... }
    async getCachedImage(word) { ... }
}
```

### Phase 4: Testing

1. **Backend API Tests**
```bash
# Test TTS
curl -X POST http://localhost:8000/api/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "hello"}' \
  --output test.mp3

# Test Deck Upload
curl -X POST http://localhost:8000/api/v1/decks/upload \
  -F "file=@../docs/words/toefl_1.csv" \
  -F "name=TOEFL 1"

# Test Session Start
curl -X POST http://localhost:8000/api/v1/session/start \
  -H "Content-Type: application/json" \
  -d '{"deck_id": 1}'
```

2. **Frontend Integration Tests**
- Open browser console
- Test API client methods
- Verify quiz flow works end-to-end

### Phase 5: Deployment

#### Local Development
```bash
# Start with Docker Compose
docker-compose up -d

# Access:
# - Backend: http://localhost:8000
# - Frontend: http://localhost:3000
# - DB: localhost:5432
```

#### Production (Railway - Recommended)

1. **Create Railway Project**
   - Visit railway.app
   - Create new project
   - Add PostgreSQL database

2. **Deploy Backend**
   - Connect GitHub repository
   - Root directory: `/backend`
   - Build command: Auto-detected
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables**
   ```
   DATABASE_URL=(auto from Railway)
   ELEVENLABS_API_KEY=your_key
   HUGGINGFACE_API_KEY=your_key
   GITHUB_TOKEN=your_token
   CORS_ORIGINS=https://yourusername.github.io
   ```

4. **Deploy Frontend**
   - Keep using GitHub Pages for now
   - Update API_BASE in api_client.js to Railway URL
   - Or use Vercel/Netlify for better performance

#### Alternative: VPS Deployment

```bash
# SSH into VPS
ssh user@your-server.com

# Clone repository
git clone https://github.com/yourusername/voca_test.git
cd voca_test

# Set up environment
cp backend/.env.example backend/.env
nano backend/.env  # Edit with your keys

# Start with Docker Compose
docker-compose up -d

# Set up nginx reverse proxy (optional)
# backend: proxy_pass http://localhost:8000
# frontend: serve from /docs
```

### Phase 6: C++ Engine Integration (Optional)

For maximum performance, integrate C++ engine via pybind11:

1. **Create bindings**
```bash
cd backend/bindings
```

Create `voca_bindings.cpp`:
```cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "../../include/voca_test/voca_test_engine.hpp"

namespace py = pybind11;

PYBIND11_MODULE(voca_engine, m) {
    py::class_<VocaTestEngine>(m, "VocaTestEngine")
        .def(py::init<>())
        .def("is_correct", &VocaTestEngine::isCorrect)
        .def("normalize", &VocaTestEngine::normalize);
}
```

Create `CMakeLists.txt`:
```cmake
cmake_minimum_required(VERSION 3.10)
project(voca_bindings)

find_package(pybind11 REQUIRED)

pybind11_add_module(voca_engine voca_bindings.cpp
    ../../src/voca_test_engine.cpp
    ../../src/voca_repository.cpp
)

target_include_directories(voca_engine PRIVATE ../../include)
```

2. **Build**
```bash
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make
cp voca_engine*.so ../../app/core/
```

3. **Verify**
```python
from app.core.voca_engine import VocaTestEngine
engine = VocaTestEngine()
# Should print: "Using C++ engine via pybind11"
```

## Migration Checklist

### Backend
- [x] FastAPI app structure
- [x] Database models
- [x] Pydantic schemas
- [x] TTS service
- [x] Image service
- [x] Session service
- [x] API routes
- [x] Docker setup
- [ ] Deploy to Railway/VPS
- [ ] Test all endpoints
- [ ] C++ bindings (optional)

### Frontend
- [ ] Create api_client.js
- [ ] Update tts.js
- [ ] Update image_association.js
- [ ] Update app.js (session management)
- [ ] Simplify storage.js
- [ ] Update API_BASE URL for production
- [ ] Test end-to-end flow
- [ ] Update service worker (cache strategy)

### Data Migration
- [ ] Export existing decks from PWA
- [ ] Upload decks to backend via API
- [ ] Verify deck/word counts match
- [ ] Test wrong word tracking

### Testing
- [ ] Unit tests for services
- [ ] Integration tests for API
- [ ] E2E tests for quiz flow
- [ ] Performance testing (TTS/Image caching)
- [ ] Mobile browser testing

### Documentation
- [x] Backend README
- [x] Migration guide
- [ ] API documentation (Swagger auto-generated)
- [ ] Update main README
- [ ] Update CLAUDE.md

## Rollback Plan

If migration fails, you can revert to the old system:

1. **Keep Cloudflare Workers deployed** - Don't delete them yet
2. **Frontend fallback** - Keep old code in separate branch
3. **Gradual migration** - Run both systems in parallel initially

## Future Enhancements

After successful migration:

1. **Authentication** - Add JWT-based user authentication
2. **User Dashboard** - Personal stats, progress tracking
3. **Social Features** - Share decks, leaderboards
4. **Mobile App** - React Native or Flutter
5. **Analytics** - Usage patterns, learning insights
6. **Advanced Features**:
   - Spaced repetition algorithm
   - AI-generated example sentences
   - Pronunciation scoring
   - Gamification

## Troubleshooting

### API Connection Errors
```javascript
// Check CORS
// Backend .env should have:
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

// Frontend should use correct API_BASE
const API_BASE = 'http://localhost:8000/api/v1'; // Dev
const API_BASE = 'https://your-api.railway.app/api/v1'; // Prod
```

### Database Issues
```bash
# Reset database
rm backend/voca.db

# Using uv
cd backend && uv run python init_db.py --sample

# Using pip
python backend/init_db.py --sample
```

### Docker Issues
```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Performance Considerations

1. **Caching**: DB caching reduces API costs significantly
2. **Connection Pooling**: SQLAlchemy handles this automatically
3. **CDN**: Use CloudFlare/Vercel for frontend static assets
4. **Redis**: Add Redis for session caching (future)
5. **Rate Limiting**: Implement for TTS/Image APIs (future)

## Security Checklist

- [x] API keys in environment variables
- [x] CORS properly configured
- [ ] Input validation (Pydantic handles this)
- [ ] SQL injection prevention (SQLAlchemy handles this)
- [ ] Rate limiting (add later)
- [ ] HTTPS in production
- [ ] Secret rotation policy

## Cost Comparison

### Before (Cloudflare Workers)
- Workers: Free tier (100k requests/day)
- Storage: Browser only (free)
- Total: $0/month

### After (FastAPI + Railway)
- Railway: $5-10/month (includes PostgreSQL)
- Or VPS: $5/month (DigitalOcean)
- Storage: Database included
- Total: $5-10/month

**Trade-off**: Small cost for multi-user support, persistent storage, and mobile readiness.

## Questions?

Refer to:
- [Backend README](backend/README.md) - Detailed API documentation
- [Plan File](.claude/plans/lucky-knitting-grove.md) - Original migration plan
- GitHub Issues - Report problems

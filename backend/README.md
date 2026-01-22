# Voca Test - FastAPI Backend

FastAPI-based backend for the Voca Test vocabulary learning application. Integrates C++ core engine via pybind11 and provides REST API for TTS, image generation, and quiz session management.

## Architecture

```
FastAPI Backend
├── API Layer (Pydantic)
├── Service Layer
│   ├── TTS Service (ElevenLabs)
│   ├── Image Service (HuggingFace)
│   └── Session Service (C++ Engine)
├── C++ Engine (pybind11)
└── Database (PostgreSQL/SQLite)
```

## Features

- **TTS API**: ElevenLabs text-to-speech with caching
- **Image Generation**: HuggingFace Stable Diffusion for association images
- **Session Management**: Quiz sessions with C++ scoring engine
- **Deck Management**: CSV upload and word management
- **Multi-user Support**: User and session isolation
- **Caching**: DB-based caching for TTS audio and images

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- C++ compiler (for pybind11 bindings, optional)

### Local Development (Python)

**Option 1: Using uv (Recommended)**
```bash
cd backend

# Install uv (한 번만)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 동기화 (자동으로 Python 설치 및 가상환경 생성)
uv sync

# 가상환경 활성화
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

**Option 2: Using pip**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Run the server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. **Access the API**
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Docker Compose (Recommended)

1. **Set up environment**
```bash
# In project root
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys
```

2. **Start all services**
```bash
docker-compose up -d
```

3. **Access services**
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432

4. **Stop services**
```bash
docker-compose down
```

## API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check

### TTS
- `POST /api/v1/tts` - Generate TTS audio
  ```json
  {
    "text": "hello"
  }
  ```

### Image
- `POST /api/v1/image` - Generate association image
  ```json
  {
    "word": "escape"
  }
  ```
- `POST /api/v1/image/github` - Commit image to GitHub
  ```json
  {
    "word": "escape",
    "image_base64": "iVBORw0KGgo..."
  }
  ```

### Session
- `POST /api/v1/session/start` - Start quiz session
  ```json
  {
    "deck_id": 1,
    "word_indices": [0, 1, 2],
    "is_wrong_only": false
  }
  ```
- `GET /api/v1/session/{session_id}/prompt` - Get current question
- `POST /api/v1/session/{session_id}/submit` - Submit answer
  ```json
  {
    "answer": "탈출하다",
    "hint_used": 0
  }
  ```
- `GET /api/v1/session/{session_id}/summary` - Get session summary
- `GET /api/v1/session/{session_id}/wrong` - Get wrong words

### Decks
- `GET /api/v1/decks` - List all decks
- `GET /api/v1/decks/{deck_id}` - Get deck with words
- `GET /api/v1/decks/{deck_id}/words` - Get deck words only
- `POST /api/v1/decks/upload` - Upload CSV deck
- `DELETE /api/v1/decks/{deck_id}` - Delete deck

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Database
DATABASE_URL=sqlite:///./voca.db
# For PostgreSQL: postgresql://user:password@localhost/vocadb

# API Keys
ELEVENLABS_API_KEY=your_key_here
HUGGINGFACE_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here

# GitHub Config
GITHUB_OWNER=your_username
GITHUB_REPO=voca_test
GITHUB_BRANCH=master

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# App
APP_NAME=Voca Test API
DEBUG=True
```

## C++ Engine Integration

The backend uses a Python fallback by default. To use the C++ engine via pybind11:

### Build pybind11 Bindings

1. **Install dependencies**
```bash
# Using uv
uv add pybind11

# Or using pip
pip install pybind11
```

2. **Build bindings**
```bash
cd backend/bindings
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make
```

3. **Copy shared library**
```bash
cp voca_engine*.so ../../app/core/
```

The application will automatically detect and use the C++ engine if available.

## Database Migration

Using Alembic for database migrations:

```bash
# Initialize Alembic (already done)
alembic init alembic

# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Testing

Run tests with pytest:

```bash
pytest tests/
```

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # API routes
│   ├── core/            # Core utilities (C++ wrapper)
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── config.py        # Settings
│   ├── database.py      # DB setup
│   └── main.py          # FastAPI app
├── bindings/            # pybind11 bindings (optional)
├── tests/               # Tests
├── alembic/             # DB migrations
├── .env.example         # Environment template
├── .gitignore
├── Dockerfile
├── requirements.txt
└── README.md
```

## Deployment

### Railway (Recommended)

1. Create Railway project
2. Add PostgreSQL service
3. Connect GitHub repository
4. Set environment variables
5. Deploy

### Docker + VPS

```bash
# Build image
docker build -t voca-backend .

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  voca-backend
```

### Render / Heroku

Follow platform-specific Python deployment guides. Ensure:
- Python version: 3.11+
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:
```bash
# Make sure you're in the backend directory
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Database Issues

```bash
# Delete database and recreate
rm voca.db
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### C++ Bindings Not Found

The app will automatically fall back to Python implementation. To verify:
```python
from app.core.voca_engine import VocaTestEngine
engine = VocaTestEngine()
# Should print: "Using C++ engine via pybind11" or "pybind11 bindings not available"
```

## Development

### Code Style

Follow PEP 8. Use formatters:
```bash
# Using uv
uv add --dev black isort
uv run black app/
uv run isort app/

# Or using pip
pip install black isort
black app/
isort app/
```

### Adding New Endpoints

1. Create schema in `app/schemas/`
2. Implement service in `app/services/`
3. Add router in `app/api/v1/`
4. Register router in `app/main.py`

## License

Same as the main project.

## Support

For issues and questions, see the main project README.

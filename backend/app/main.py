from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Voca Test API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Import and include routers
from app.api.v1 import tts, image, session, decks

app.include_router(tts.router, prefix="/api/v1", tags=["tts"])
app.include_router(image.router, prefix="/api/v1", tags=["image"])
app.include_router(session.router, prefix="/api/v1", tags=["session"])
app.include_router(decks.router, prefix="/api/v1", tags=["decks"])

# TODO - FastAPI Migration Checklist

## ✅ Completed

### Backend Implementation
- [x] Project structure created
- [x] Database models (8 tables)
- [x] Pydantic schemas (API contracts)
- [x] TTS service (ElevenLabs proxy)
- [x] Image service (HuggingFace proxy)
- [x] Session service (C++ engine wrapper)
- [x] API routes (15 endpoints)
- [x] Docker setup
- [x] Environment configuration
- [x] Documentation (4 files)
- [x] DB initialization script

### Documentation
- [x] `backend/README.md` - Setup guide
- [x] `backend/SUMMARY_KR.md` - Korean summary
- [x] `MIGRATION_GUIDE.md` - Migration steps
- [x] `QUICK_START.md` - Quick start
- [x] `backend/IMPLEMENTATION_STATUS.txt` - Status

## 🔄 In Progress

### Testing
- [ ] Test backend locally
  ```bash
  cd backend
  pip install -r requirements.txt
  python init_db.py --sample
  uvicorn app.main:app --reload
  ```
- [ ] Visit http://localhost:8000/docs
- [ ] Test each API endpoint
- [ ] Upload a CSV deck
- [ ] Complete a quiz session

## 📋 Next Steps

### Priority 1: Backend Testing & Deployment

#### Local Testing
- [ ] Install Python dependencies
- [ ] Set up environment variables
- [ ] Initialize database with sample data
- [ ] Start FastAPI server
- [ ] Test all API endpoints via Swagger
- [ ] Verify TTS API (if API key provided)
- [ ] Verify Image API (if API key provided)
- [ ] Test session flow end-to-end

#### Docker Testing
- [ ] Run `docker-compose up -d`
- [ ] Test backend at http://localhost:8000
- [ ] Test frontend at http://localhost:3000
- [ ] Verify database connectivity
- [ ] Check logs: `docker-compose logs -f`

#### Cloud Deployment (Railway)
- [ ] Create Railway account
- [ ] Create new project
- [ ] Add PostgreSQL service
- [ ] Connect GitHub repository
- [ ] Set environment variables:
  - `DATABASE_URL` (auto)
  - `ELEVENLABS_API_KEY`
  - `HUGGINGFACE_API_KEY`
  - `GITHUB_TOKEN`
  - `CORS_ORIGINS`
- [ ] Deploy backend
- [ ] Test deployed API
- [ ] Note down API URL

### Priority 2: Frontend Migration

#### Create API Client
- [ ] Create `docs/js/api_client.js`
- [ ] Define `VocaAPI` class with methods:
  - `getTTS(text)`
  - `getImage(word)`
  - `listDecks()`
  - `uploadDeck(file, name, description)`
  - `startSession(deckId, wordIndices, isWrongOnly)`
  - `getPrompt(sessionId)`
  - `submitAnswer(sessionId, answer, hintUsed)`
  - `getSummary(sessionId)`

#### Update Existing Files
- [ ] Update `docs/js/tts.js`
  - Replace Cloudflare Worker URL with API
  - Use `api.getTTS()` method
  - Handle blob response
- [ ] Update `docs/js/image_association.js`
  - Replace HuggingFace Worker URL with API
  - Use `api.getImage()` method
  - Handle blob response
- [ ] Update `docs/js/app.js`
  - Remove JS fallback
  - Use API for session management
  - Update session flow logic
- [ ] Simplify `docs/js/storage.js`
  - Keep only offline caching
  - Remove session/deck management
  - Use localStorage for last session ID

#### Configuration
- [ ] Update `API_BASE` in `api_client.js`:
  - Local: `http://localhost:8000/api/v1`
  - Production: `https://your-app.railway.app/api/v1`
- [ ] Update CORS origins in backend `.env`

### Priority 3: Data Migration

- [ ] Export existing decks from PWA
- [ ] Upload CSV files via API
- [ ] Verify word counts match
- [ ] Test quiz with migrated data
- [ ] Verify wrong word tracking

### Priority 4: Testing

#### Unit Tests
- [ ] Create `backend/tests/test_tts_service.py`
- [ ] Create `backend/tests/test_image_service.py`
- [ ] Create `backend/tests/test_session_service.py`
- [ ] Create `backend/tests/test_api.py`

#### Integration Tests
- [ ] Test full quiz flow
- [ ] Test CSV upload
- [ ] Test TTS caching
- [ ] Test image caching
- [ ] Test wrong word tracking

#### E2E Tests
- [ ] Test in Chrome
- [ ] Test in Firefox
- [ ] Test in Safari
- [ ] Test on mobile (iOS)
- [ ] Test on mobile (Android)

### Priority 5: Optional Enhancements

#### C++ Integration (Performance)
- [ ] Create `backend/bindings/voca_bindings.cpp`
- [ ] Create `backend/bindings/CMakeLists.txt`
- [ ] Build pybind11 module
- [ ] Test C++ engine
- [ ] Benchmark Python vs C++

#### Additional Features
- [ ] Add user authentication (JWT)
- [ ] Add user registration/login
- [ ] Add user dashboard
- [ ] Add statistics page
- [ ] Add spaced repetition algorithm
- [ ] Add leaderboard
- [ ] Add deck sharing

#### Mobile App (Future)
- [ ] Research React Native vs Flutter
- [ ] Set up mobile dev environment
- [ ] Create mobile app project
- [ ] Implement UI using FastAPI backend
- [ ] Test on real devices
- [ ] Publish to app stores

### Priority 6: Monitoring & Maintenance

#### Logging
- [ ] Set up structured logging
- [ ] Add request logging middleware
- [ ] Log errors to file/service

#### Monitoring
- [ ] Set up health check monitoring
- [ ] Add Sentry for error tracking
- [ ] Add analytics (optional)

#### Performance
- [ ] Add Redis for session caching (optional)
- [ ] Optimize database queries
- [ ] Add API rate limiting
- [ ] Optimize image sizes

#### Security
- [ ] Review CORS settings
- [ ] Audit dependencies
- [ ] Set up secret rotation
- [ ] Enable HTTPS
- [ ] Add input sanitization

## 📅 Timeline Estimate

### Week 1: Backend & Deployment
- Days 1-2: Local testing & fixes
- Days 3-4: Cloud deployment
- Days 5-7: API testing & documentation

### Week 2: Frontend Migration
- Days 1-3: API client & updates
- Days 4-5: Integration testing
- Days 6-7: Bug fixes & polish

### Week 3: Testing & Launch
- Days 1-3: E2E testing
- Days 4-5: User acceptance testing
- Days 6-7: Production launch

### Week 4+: Enhancements
- Optional features
- Performance optimization
- Mobile app planning

## 🚨 Critical Path

1. **Backend Testing** (Must work)
2. **Cloud Deployment** (Must be accessible)
3. **Frontend API Integration** (Must connect)
4. **E2E Testing** (Must work end-to-end)
5. **Launch** ✨

## 📝 Notes

- Keep Cloudflare Workers running until migration is complete
- Test thoroughly before decommissioning old system
- Monitor costs on Railway/cloud platform
- Back up database regularly
- Document any issues encountered

## ❓ Questions to Answer

- [ ] Do you want authentication immediately or later?
- [ ] What's your preferred cloud platform? (Railway / Render / VPS)
- [ ] Do you need mobile app soon or can it wait?
- [ ] Should we keep GitHub Pages for frontend?
- [ ] Do you want to use C++ bindings for performance?

## 🎉 Launch Criteria

Before going live:
- [ ] All API endpoints tested
- [ ] Frontend connected and working
- [ ] Data migrated successfully
- [ ] Deployed to production
- [ ] HTTPS enabled
- [ ] CORS configured correctly
- [ ] Error handling verified
- [ ] Performance acceptable
- [ ] Documentation updated
- [ ] Backup strategy in place

---

**Last Updated**: 2026-01-23
**Status**: Backend Complete, Ready for Frontend Integration

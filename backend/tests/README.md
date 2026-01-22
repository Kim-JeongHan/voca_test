# Testing Guide

Complete testing suite for the FastAPI backend using pytest and TDD principles.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_voca_engine.py      # C++ engine wrapper tests (unit)
├── test_tts_service.py      # TTS service tests (unit, mocked)
├── test_image_service.py    # Image service tests (unit, mocked)
├── test_session_service.py  # Session service tests (unit)
├── test_api.py              # API endpoint tests (integration)
└── README.md                # This file
```

## Running Tests

### Install Test Dependencies

**Using uv (Recommended):**
```bash
cd backend
uv sync
```

**Using pip:**
```bash
pip install -r requirements.txt
```

### Run All Tests

**Using uv:**
```bash
uv run pytest
```

**Using pip/venv:**
```bash
pytest
```

### Run with Coverage

**Using uv:**
```bash
uv run pytest --cov=app --cov-report=html
# View coverage report: open htmlcov/index.html
```

**Using pip/venv:**
```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test Categories

```bash
# Unit tests only (fast, no external dependencies)
pytest -m unit

# Integration tests (requires database)
pytest -m integration

# API tests
pytest -m api

# Skip external API tests
pytest -m "not external"
```

### Run Specific Test Files

```bash
# Test VocaTestEngine only
pytest tests/test_voca_engine.py

# Test services
pytest tests/test_tts_service.py tests/test_image_service.py

# Test API endpoints
pytest tests/test_api.py
```

### Verbose Output

```bash
pytest -v
pytest -vv  # Even more verbose
```

## Test Markers

Tests are organized using markers:

- `@pytest.mark.unit` - Unit tests (no external dependencies)
- `@pytest.mark.integration` - Integration tests (database required)
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.external` - Tests requiring external APIs (skip in CI)
- `@pytest.mark.slow` - Slow running tests

## Writing Tests

### Test Naming Convention

```python
# Test files: test_<module_name>.py
# Test classes: Test<ComponentName>
# Test functions: test_<behavior_being_tested>

class TestTTSService:
    def test_get_tts_audio_from_cache(self):
        """Test retrieving audio from cache."""
        pass
```

### Using Fixtures

Common fixtures available in `conftest.py`:

```python
def test_example(db_session, create_test_deck, client):
    """
    db_session: Fresh database session
    create_test_deck: Pre-populated test deck
    client: FastAPI test client
    """
    deck = create_test_deck
    response = client.get(f"/api/v1/decks/{deck.id}")
    assert response.status_code == 200
```

### Mocking External APIs

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.unit
@pytest.mark.asyncio
async def test_with_mock(db_session):
    service = TTSService(db_session)

    with patch.object(service, '_call_elevenlabs_api',
                     new_callable=AsyncMock) as mock_api:
        mock_api.return_value = b"fake_audio"

        result = await service.get_tts_audio("test")

        assert result == (b"fake_audio", "audio/mpeg")
        mock_api.assert_called_once_with("test")
```

## Test Coverage Goals

Current coverage targets:

- **Overall**: > 80%
- **Core Logic** (voca_engine, services): > 90%
- **API Routes**: > 85%
- **Models**: > 70%

### View Coverage Report

```bash
pytest --cov=app --cov-report=term-missing
```

## Continuous Integration

Tests are designed to run in CI environments:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest -m "not external" --cov=app
```

Skip external API tests in CI using markers.

## Testing Best Practices

### 1. Test Isolation

Each test should be independent:

```python
def setup_method(self):
    """Reset state before each test."""
    self.engine = VocaTestEngine()
```

### 2. Arrange-Act-Assert Pattern

```python
def test_is_correct_exact_match(self):
    # Arrange
    engine = VocaTestEngine()

    # Act
    result = engine.is_correct("escape", "escape")

    # Assert
    assert result is True
```

### 3. Test One Thing

```python
# Good: Tests one behavior
def test_normalize_removes_spaces(self):
    assert engine.normalize("hello world") == "helloworld"

# Bad: Tests multiple behaviors
def test_normalize_everything(self):
    assert engine.normalize("hello world") == "helloworld"
    assert engine.normalize("HELLO") == "hello"
    assert engine.normalize("'hello'") == "hello"
```

### 4. Use Descriptive Names

```python
# Good
def test_submit_answer_with_two_hints_marks_as_wrong(self):
    pass

# Bad
def test_hints(self):
    pass
```

### 5. Mock External Dependencies

```python
# Always mock external APIs
with patch('httpx.AsyncClient.post') as mock_post:
    mock_post.return_value.is_success = True
    # ... test logic
```

## Common Test Scenarios

### Testing Database Operations

```python
def test_create_deck(db_session):
    deck = Deck(name="Test", description="Test deck")
    db_session.add(deck)
    db_session.commit()

    assert deck.id is not None
```

### Testing API Endpoints

```python
def test_api_endpoint(client):
    response = client.post("/api/v1/endpoint", json={"key": "value"})

    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "expected"
```

### Testing Async Functions

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected
```

### Testing Error Cases

```python
def test_invalid_input_raises_error():
    engine = VocaTestEngine()

    with pytest.raises(ValueError, match="must be 1-100"):
        engine.validate_input("")
```

## Debugging Tests

### Run with Print Statements

```bash
pytest -s  # Show print output
```

### Run with PDB

```bash
pytest --pdb  # Drop into debugger on failure
```

### Run Last Failed Tests

```bash
pytest --lf  # Run only tests that failed last time
```

### Run Specific Test

```bash
pytest tests/test_api.py::TestSessionAPI::test_start_session
```

## Performance Testing

### Measure Test Duration

```bash
pytest --durations=10  # Show 10 slowest tests
```

### Profile Tests

```bash
pytest --profile  # Generate performance profile
```

## Test Data Management

### Using Faker for Test Data

```python
from faker import Faker

def test_with_faker():
    fake = Faker()
    email = fake.email()
    name = fake.name()
    # Use generated data in tests
```

### Fixtures for Common Data

```python
@pytest.fixture
def sample_words():
    return [
        {"word": "escape", "meaning": "탈출하다"},
        {"word": "abandon", "meaning": "버리다"},
    ]
```

## Troubleshooting

### Tests Fail on Import

```bash
# Ensure PYTHONPATH includes backend directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Database Errors

```bash
# In-memory SQLite is used for tests
# Each test gets a fresh database
# Check conftest.py for db_session fixture
```

### Async Test Errors

```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Mark async tests properly
@pytest.mark.asyncio
async def test_async_function():
    pass
```

## Example Test Session

**Using uv:**
```bash
# Full test workflow
cd backend

# Install dependencies
uv sync

# Run all tests with coverage
uv run pytest --cov=app --cov-report=html -v

# View results
# - Terminal: Coverage summary
# - Browser: open htmlcov/index.html

# Fix any failing tests
# Run specific test file
uv run pytest tests/test_voca_engine.py -v

# Once all pass, commit
git add tests/
git commit -m "Add comprehensive test suite"
```

**Using pip:**
```bash
cd backend
pip install -r requirements.txt
pytest --cov=app --cov-report=html -v
pytest tests/test_voca_engine.py -v
```

## Contributing Tests

When adding new features:

1. Write tests first (TDD)
2. Ensure > 80% coverage
3. Test happy path and error cases
4. Mock external dependencies
5. Use appropriate markers
6. Update this documentation if needed

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)

# Project Setup & Configuration Guide

## Quick Start

### 1. Setup Backend

```bash
python -m venv .venv
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate # macOS/Linux

pip install -r requirements.txt
```

### 2. Setup Pre-commit Hooks (Optional but Recommended)

```bash
pre-commit install
pre-commit run --all-files  # Run all checks once
```

This will automatically:
- Format Python code with Black
- Sort imports with isort
- Lint with flake8
- Format TypeScript/JavaScript with Prettier

### 3. Setup Frontend

```bash
cd frontend
npm install
```

### 4. Generate Data & Run Backend

```bash
# From project root
python scripts/rebuild_outputs.py
```

This will:
- Load `dirty_transport_dataset.csv`
- Clean and engineer features
- Train ML models
- Generate explainability reports (HTML)
- Save outputs to `results/` directory

Then start the API:

```bash
uvicorn src.transport_analysis.api:app --reload --host 0.0.0.0 --port 8000
```

The API docs will be available at: **http://localhost:8000/docs**

### 5. Run Frontend

```bash
cd frontend
npm start
```

The app will be available at: **http://localhost:4200**

---

## Development Workflow

### Code Quality Tools

#### Python
```bash
# Format code
black src/ scripts/ tests/

# Sort imports
isort src/ scripts/ tests/

# Lint code
flake8 src/ scripts/ tests/ --max-line-length=100

# Run all checks
pre-commit run --all-files
```

#### TypeScript/Angular
```bash
cd frontend

# Format code
npm run format

# Check formatting
npm run format:check

# Lint
npm run lint

# Run tests
npm test
npm run test:ci  # CI mode (no watch)
```

### Testing

#### Backend Tests
```bash
python -m pytest -q
python -m pytest -v  # Verbose
python -m pytest --cov=src tests/  # With coverage
```

#### Frontend Tests
```bash
cd frontend
npm test
npm run test:ci
```

---

## Docker Deployment

### Build and Run with Docker Compose

```bash
docker-compose up --build
```

This will:
- Build the backend Docker image
- Run backend on http://localhost:8000
- Run frontend on http://localhost:4200
- Automatically rebuild outputs on startup
- Setup health checks

### Individual Services

#### Backend Only
```bash
docker build -t transport-api .
docker run -p 8000:8000 -v $(pwd)/results:/app/results transport-api
```

#### Frontend Only
```bash
cd frontend
docker build -t transport-ui .
docker run -p 4200:4200 transport-ui
```

---

## Environment Configuration

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Key variables:
- `BACKEND_HOST`, `BACKEND_PORT`: API server configuration
- `ANGULAR_API_URL`: Frontend API endpoint
- `MODEL_WINSORIZE`: Enable/disable winsorization in feature engineering
- `CV_FOLDS`: Number of cross-validation folds

---

## API Documentation

### Swagger UI
```
GET http://localhost:8000/docs
```

### Available Endpoints

#### Health Check
```
GET /health
```

#### Data Endpoints
```
GET /data/cleaned     # Cleaned dataset
GET /data/engineered  # Engineered features dataset
```

---

## Project Structure

```
.
├── src/
│   └── transport_analysis/
│       ├── api.py                 # FastAPI application
│       ├── data_loader.py         # CSV loading
│       ├── data_cleaner.py        # Data cleaning pipeline
│       ├── feature_engineer.py    # Feature engineering
│       ├── model_builder.py       # Model training
│       ├── explainer.py           # SHAP explainability
│       └── utils.py               # Utilities
├── frontend/
│   ├── src/app/
│   │   ├── components/            # UI components
│   │   ├── api.service.ts         # Backend communication
│   │   └── models/                # TypeScript types
│   └── package.json
├── scripts/
│   ├── rebuild_outputs.py         # Main orchestration
│   ├── export_data_view.py        # Data export
│   └── ...
├── tests/
│   └── test_*.py                  # Unit tests
├── results/                        # Generated outputs
├── docker-compose.yml             # Docker orchestration
├── Dockerfile                     # Backend container
├── pyproject.toml                 # Python tool config
├── .prettierrc                    # Code formatting
├── .pre-commit-config.yaml        # Pre-commit hooks
└── .env.example                   # Environment template
```

---

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Check logs
uvicorn src.transport_analysis.api:app --reload --log-level debug
```

### Frontend won't load data
1. Ensure backend is running on configured URL
2. Check browser console for CORS errors
3. Verify `results/` directory has generated files

### Data not found errors
```bash
# Regenerate all outputs
python scripts/rebuild_outputs.py

# Check if input data exists
ls dirty_transport_dataset.csv
```

### Import errors in Python
```bash
# Reinstall package with editable mode
pip install -e .
```

---

## Next Steps

1. **Customize API**: Extend `src/transport_analysis/api.py` with new endpoints
2. **Add Models**: Implement additional ML models in `model_builder.py`
3. **UI Components**: Add new Angular components in `frontend/src/app/components/`
4. **Database Integration**: Add persistence layer (PostgreSQL, MongoDB, etc.)
5. **Logging**: Implement structured logging with Python `logging` module
6. **Authentication**: Add user authentication/authorization
7. **CI/CD**: Configure GitHub Actions in `.github/workflows/`

---

## References

- **FastAPI**: https://fastapi.tiangolo.com
- **Angular 16**: https://angular.io
- **SHAP**: https://github.com/slundberg/shap
- **scikit-learn**: https://scikit-learn.org
- **Docker**: https://docs.docker.com

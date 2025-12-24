# Contributing to Transport Analysis

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Getting Started

1. **Fork & Clone**
   ```bash
   git clone https://github.com/your-username/transport-analysis.git
   cd transport-analysis
   ```

2. **Setup Development Environment**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   cd frontend && npm install && cd ..
   ```

3. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

## Development Guidelines

### Code Style

#### Python
- Follow PEP 8
- Use Black for formatting (automatic via pre-commit)
- Use isort for imports (automatic via pre-commit)
- Max line length: 100 characters
- Add type hints where possible

```python
# Example
from typing import List, Dict
import pandas as pd

def process_data(df: pd.DataFrame, threshold: float = 0.5) -> Dict[str, List]:
    """Process transport data with given threshold."""
    pass
```

#### TypeScript/Angular
- Follow Angular style guide
- Use Prettier for formatting
- Strict mode enabled in `tsconfig.json`
- Use meaningful variable names
- Add JSDoc comments for public methods

```typescript
/**
 * Load transport data from backend.
 * @returns Observable of transport records
 */
public loadData(): Observable<TransportRecord[]> {
  return this.http.get<TransportRecord[]>('/api/data');
}
```

### Commit Messages

Use conventional commits:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples**:
```
feat(data-cleaner): add timezone-aware datetime parsing
fix(api): return correct content-type for CSV responses
docs(setup): add Docker deployment instructions
test(models): add unit tests for RandomForest trainer
```

### Branch Naming

```
feature/add-new-model
fix/api-cors-issue
docs/update-readme
refactor/extract-utility-functions
```

## Making Changes

### Backend Changes

1. Create feature branch
2. Implement changes in `src/transport_analysis/`
3. Add/update tests in `tests/`
4. Run tests and linting:
   ```bash
   python -m pytest -v
   black src/ tests/
   flake8 src/ tests/
   ```
5. Create pull request

### Frontend Changes

1. Create feature branch
2. Implement changes in `frontend/src/app/`
3. Add/update tests (`.spec.ts` files)
4. Run tests and linting:
   ```bash
   cd frontend
   npm test
   npm run format
   npm run lint
   ```
5. Create pull request

### Data Pipeline Changes

Changes to cleaning, feature engineering, or model building:
1. Update the relevant class in `src/transport_analysis/`
2. Add tests to validate behavior
3. Run `python scripts/rebuild_outputs.py` to verify end-to-end
4. Update documentation if behavior changes

## Testing

### Backend

```bash
# Run all tests
python -m pytest

# Run specific test
python -m pytest tests/test_data_cleaner.py::test_weather_normalization_and_nan_string

# Run with coverage
python -m pytest --cov=src tests/ --cov-report=html
```

**Test Coverage Target**: 80%+

### Frontend

```bash
# Run all tests
cd frontend && npm test

# Run specific test file
npm test -- --include='**/data-table.component.spec.ts'

# Run in CI mode
npm run test:ci
```

## Documentation

- Update docstrings for all functions/classes
- Keep `README.md` and `SETUP.md` in sync with changes
- Document complex algorithms with inline comments
- Add type hints and JSDoc comments

## Pull Request Process

1. **Ensure all tests pass**
   ```bash
   python -m pytest
   cd frontend && npm test
   ```

2. **Check code quality**
   ```bash
   black --check src/ scripts/ tests/
   flake8 src/ scripts/ tests/
   cd frontend && npm run format:check
   ```

3. **Update documentation** if needed

4. **Create descriptive PR title and description**
   ```
   Title: feat(models): Add XGBoost model support
   
   Description:
   - Adds XGBoost as an alternative to RandomForest
   - Includes hyperparameter tuning
   - Benchmarks show 5% improvement in R² score
   - Adds tests for model training and prediction
   ```

5. **Link related issues**
   ```
   Closes #123
   Related to #456
   ```

6. **Request review** from maintainers

7. **Address feedback** and re-request review

## Areas for Contribution

### High Priority
- [ ] Database integration (replace CSV with PostgreSQL)
- [ ] User authentication & authorization
- [ ] Advanced visualization features
- [ ] Performance optimization for large datasets
- [ ] Automated deployment pipeline

### Medium Priority
- [ ] Additional ML models (XGBoost, LightGBM, etc.)
- [ ] Real-time data ingestion
- [ ] Model comparison dashboard
- [ ] Export functionality (PDF, Excel)
- [ ] Caching layer

### Low Priority
- [ ] UI/UX improvements
- [ ] Internationalization (i18n)
- [ ] Dark mode support
- [ ] Mobile responsiveness enhancements

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: File a GitHub Issue with minimal reproducible example
- **Features**: Discuss in Issues before implementing

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for contributing!**

# Contributing to HECTOR

Thank you for your interest in contributing to HECTOR! This guide will help you get started.

---

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### Local Setup

```bash
# Clone the repository
git clone https://github.com/DanielDeshmukh/Hector.git
cd Hector

# Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API keys (GROQ_API_KEY, etc.)

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_router.py -v

# Run with coverage
python -m pytest tests/ --cov=api --cov=core --cov-report=term-missing
```

---

## Branch Workflow

We use a **branch-per-phase** workflow with review gates:

1. Create a branch from `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feat/your-feature-name
   ```

2. Make atomic commits with conventional commit messages:
   ```
   feat(scope): add new feature
   fix(scope): fix a bug
   test(scope): add tests
   docs(scope): update documentation
   refactor(scope): refactor code
   ```

3. Push and create a PR against `main`:
   ```bash
   git push origin feat/your-feature-name
   ```

4. Wait for review and CI checks to pass before merging.

---

## Code Style

### Python

- Follow PEP 8
- Use type hints where possible
- Keep functions focused and under 50 lines
- Add docstrings for public functions
- Run `ruff format` and `ruff check` before committing

### JavaScript/React

- Use functional components with hooks
- Follow ESLint configuration in `frontend/.eslintrc.js`
- Use Tailwind CSS for styling
- Keep components under 200 lines

---

## Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `test`: Adding or updating tests
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `style`: Formatting changes
- `chore`: Build process or tooling changes

### Examples

```
feat(api): add batch search endpoint
fix(router): handle edge case for empty queries
test(auth): add JWT expiration tests
docs(api): update search endpoint examples
```

---

## Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows the project's style guidelines
- [ ] All existing tests pass (`python -m pytest tests/ -v`)
- [ ] New tests are added for new features
- [ ] Documentation is updated if needed
- [ ] Commit messages follow the conventional format
- [ ] No secrets or API keys are committed
- [ ] `.env.example` is updated if new env vars are added

---

## Project Structure

```
Hector/
├── api/                # FastAPI application
│   ├── app.py          # Main app, routes, middleware
│   ├── services.py     # Business logic services
│   ├── security.py     # Auth, JWT, rate limiting
│   ├── cache.py        # TTL cache
│   └── rate_limit.py   # Rate limiting
├── core/               # Core logic
│   ├── router.py       # Query routing
│   ├── verifier.py     # Chain-of-verification
│   └── mapping.json    # IPC↔BNS mappings
├── data/               # Data layer
│   └── hybrid_retriever.py
├── utils/              # Utilities
│   ├── enhanced_ingestor.py
│   ├── legal_structure_parser.py
│   └── retry.py
├── frontend/           # React frontend
├── tests/              # Test suite
├── scripts/            # Deployment scripts
├── docs/               # Documentation
└── docker-compose.yml  # Docker config
```

---

## Reporting Issues

When reporting bugs, please include:

1. **Environment**: OS, Python version, Node.js version
2. **Steps to reproduce**: Clear steps to trigger the bug
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Logs**: Relevant error messages or stack traces

---

## License

By contributing to HECTOR, you agree that your contributions will be licensed under the MIT License.

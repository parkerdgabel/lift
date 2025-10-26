# Contributing to Lift

Thank you for your interest in contributing to Lift! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/parkerdgabel/lift.git
   cd lift
   ```

2. **Install dependencies**
   ```bash
   pip install -e ".[dev,mcp]"
   ```

3. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

4. **Run tests**
   ```bash
   pytest
   ```

## Branching Strategy

This project uses a simplified Git Flow branching strategy:

### Branches

- **`main`** - Production-ready code. All releases are tagged from this branch.
- **`develop`** - Integration branch for features. All development work merges here first.
- **`feature/*`** - Feature branches created from `develop`
- **`bugfix/*`** - Bug fix branches created from `develop`
- **`hotfix/*`** - Critical fixes created from `main` for emergency patches

### Feature Development Workflow

```bash
# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/my-new-feature

# Work on feature, commit changes
git add .
git commit -m "Add new feature"

# Push and create PR to develop
git push -u origin feature/my-new-feature
# Create PR: feature/my-new-feature -> develop
```

### Release Workflow

```bash
# Merge develop to main when ready for release
git checkout main
git pull origin main
git merge develop

# Tag the release
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin main --tags
```

### Hotfix Workflow

```bash
# Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug

# Fix bug, commit
git add .
git commit -m "Fix critical bug"

# Merge to both main and develop
git checkout main
git merge hotfix/critical-bug
git tag -a v0.1.1 -m "Hotfix v0.1.1"
git push origin main --tags

git checkout develop
git merge hotfix/critical-bug
git push origin develop
```

## Code Quality Standards

### Type Checking

All code must pass mypy strict type checking:
```bash
mypy lift
```

### Linting

All code must pass ruff linting:
```bash
ruff check .
ruff format .
```

### Testing

- Write tests for all new features and bug fixes
- Maintain or improve code coverage
- All tests must pass:
  ```bash
  pytest --cov=lift
  ```

### Security

Code is scanned with bandit for security issues:
```bash
bandit -r lift -ll
```

## Commit Message Guidelines

Follow conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Example:**
```
feat(workout): Add rest timer between sets

Implement a countdown timer that displays between sets to help
users track their rest periods.

Closes #123
```

## Pull Request Process

1. **Create a feature branch** from `develop`
2. **Make your changes** following code quality standards
3. **Write or update tests** for your changes
4. **Update documentation** if needed
5. **Ensure all CI checks pass**
6. **Create a pull request** to `develop` (not `main`)
7. **Address review feedback**

### PR Checklist

- [ ] Code passes all tests (`pytest`)
- [ ] Code passes type checking (`mypy lift`)
- [ ] Code passes linting (`ruff check .`)
- [ ] Code is formatted (`ruff format .`)
- [ ] Tests added/updated for changes
- [ ] Documentation updated if needed
- [ ] Commit messages follow convention
- [ ] PR targets `develop` branch

## CI/CD

- **CI runs on:** all pushes to `main` and `develop`, and all pull requests
- **Release workflow runs on:** version tags (`v*.*.*`)

All CI checks must pass before merging:
- Type Check (mypy)
- Lint & Format Check (ruff)
- Security Check (bandit)
- Tests (Python 3.11 & 3.12 on Ubuntu, macOS, Windows)
- Build Package

## Questions or Issues?

- **Bug reports:** Open an issue with details and reproduction steps
- **Feature requests:** Open an issue describing the feature and use case
- **Questions:** Open a discussion or issue

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to make Lift better!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

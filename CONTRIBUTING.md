# Contributing to methodology-v2

Thank you for your interest in contributing to methodology-v2!

---

## 📋 How to Contribute

### 1. Reporting Issues

- Use GitHub Issues to report bugs or suggest features
- Include as much detail as possible:
  - Version number
  - Operating system
  - Steps to reproduce
  - Expected vs actual behavior

### 2. Submitting Changes

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Follow the coding standards**
   - Run quality gates before committing
   - Update documentation as needed
5. **Submit a Pull Request**

### 3. Coding Standards

#### Code Quality

All code must pass:

```bash
# ASPICE documentation check
python3 quality_gate/doc_checker.py

# Constitution compliance check
python3 quality_gate/constitution/runner.py

# Code metrics check
python3 cli.py metrics report
```

#### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation change
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(quality-gate): add new metrics checker
fix(agent-spawner): resolve memory leak issue
docs(readme): update installation instructions
```

### 4. Documentation

- Update relevant documentation when changing functionality
- Add docstrings to new functions/classes
- Update CHANGELOG.md with your changes

### 5. Testing

- Write tests for new functionality
- Ensure all existing tests pass
- Aim for >80% test coverage

---

## 🏗️ Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/methodology-v2.git
cd methodology-v2

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Run quality gates
python3 quality_gate/unified_gate.py
```

---

## 📖 Project Structure

```
methodology-v2/
├── cli.py                 # Main CLI entry point
├── quality_gate/         # Quality assurance modules
├── enforcement/          # Enforcement framework
├── agent_*/             # Agent-related modules
├── security_*/          # Security modules
├── docs/                 # Documentation
└── tests/               # Test suite
```

---

## 🔄 Release Process

1. Version bump in `cli.py` and `__init__.py`
2. Update CHANGELOG.md
3. Create Git tag
4. Publish release

---

## 📝 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## 📞 Contact

- GitHub Issues: [https://github.com/johnnylugm-tech/methodology-v2/issues](https://github.com/johnnylugm-tech/methodology-v2/issues)
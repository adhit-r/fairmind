# 🤝 Contributing to FairMind

Thank you for your interest in contributing to FairMind! We're excited to have you join our community of developers, researchers, and AI enthusiasts working to make AI more ethical and fair.

## 🌟 Why Contribute?

- **Make AI Better**: Help build tools that make AI systems more fair and transparent
- **Learn & Grow**: Work with cutting-edge AI/ML technologies and ethical AI practices
- **Build Portfolio**: Contribute to a meaningful open-source project
- **Join Community**: Connect with like-minded developers and researchers
- **Real Impact**: Your contributions help organizations build responsible AI systems

## 🚀 Quick Start

### 1. Fork & Clone
```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/fairmind.git
cd fairmind
```

### 2. Set Up Development Environment
```bash
# Backend setup
cd backend
python -m pip install -r requirements.txt

# Frontend setup (if working on frontend)
cd ../frontend
npm install
```

### 3. Pick an Issue
- Browse our [issues](https://github.com/radhi1991/fairmind/issues)
- Look for `good first issue` labels for beginners
- Comment on an issue you'd like to work on

### 4. Create a Branch
```bash
git checkout -b feature/your-feature-name
```

## 🎯 Good First Issues

Perfect for newcomers! These issues are designed to help you get familiar with the codebase:

- [Issue #20](https://github.com/radhi1991/fairmind/issues/20) - React Dashboard for AI BOM Management
- [Issue #21](https://github.com/radhi1991/fairmind/issues/21) - Component Library for AI BOM
- [Issue #23](https://github.com/radhi1991/fairmind/issues/23) - Comprehensive API Testing Suite
- [Issue #25](https://github.com/radhi1991/fairmind/issues/25) - Documentation Suite
- [Issue #26](https://github.com/radhi1991/fairmind/issues/26) - CI/CD Pipeline Setup

## 🛠️ Development Guidelines

### Code Style

**Python (Backend)**
- Use [Black](https://black.readthedocs.io/) for code formatting
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all functions and classes

**TypeScript/React (Frontend)**
- Use [Prettier](https://prettier.io/) for code formatting
- Follow [ESLint](https://eslint.org/) rules
- Use functional components with hooks
- Write JSDoc comments for functions

### Testing

**Backend Tests**
```bash
cd backend
python -m pytest tests/
python -m pytest --cov=api tests/
```

**Frontend Tests**
```bash
cd frontend
npm test
npm run test:coverage
```

### Commit Messages

Use conventional commit format:
```
type(scope): description

feat(api): add new AI BOM endpoint
fix(frontend): resolve pagination issue
docs(readme): update installation guide
test(backend): add unit tests for fairness analysis
```

## 📁 Project Structure

```
fairmind/
├── 🎨 frontend/              # React TypeScript application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── utils/          # Utility functions
│   └── tests/              # Frontend tests
├── ⚙️ backend/               # FastAPI Python backend
│   ├── api/
│   │   ├── models/         # Pydantic data models
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   └── repositories/   # Data access layer
│   └── tests/              # Backend tests
├── 🤖 models/                # Sample AI models & metadata
├── 📚 docs/                  # Documentation
└── 🧪 tests/                 # Integration tests
```

## 🔧 Development Workflow

### 1. Issue Discussion
- Comment on the issue you want to work on
- Ask questions if anything is unclear
- Propose your approach

### 2. Development
- Create a feature branch from `dev`
- Write code following our guidelines
- Add tests for new functionality
- Update documentation as needed

### 3. Testing
- Run all tests locally
- Ensure code coverage doesn't decrease
- Test your changes manually

### 4. Pull Request
- Create a PR against the `dev` branch
- Fill out the PR template
- Link the related issue
- Request review from maintainers

### 5. Review & Merge
- Address review comments
- Make requested changes
- Once approved, your PR will be merged

## 🏷️ Issue Labels

We use labels to categorize issues and help you find the right tasks:

- `good first issue` - Perfect for newcomers
- `frontend` - React/TypeScript tasks
- `backend` - Python/FastAPI tasks
- `ai/ml` - Machine learning features
- `documentation` - Docs and guides
- `devops` - Infrastructure and deployment
- `bug` - Something isn't working
- `enhancement` - New feature or request
- `help wanted` - Extra attention needed

## 🧪 Testing Guidelines

### Backend Testing
- Unit tests for all service functions
- Integration tests for API endpoints
- Test coverage should be >80%
- Mock external dependencies

### Frontend Testing
- Unit tests for components
- Integration tests for user flows
- Test accessibility features
- Test responsive design

### AI/ML Testing
- Test fairness metrics
- Validate bias detection
- Performance benchmarking
- Edge case handling

## 📝 Documentation

When contributing, please:

- Update relevant documentation
- Add code comments for complex logic
- Include usage examples
- Update API documentation if needed

## 🐛 Bug Reports

When reporting bugs, please include:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python/Node versions)
- Screenshots if applicable

## 💡 Feature Requests

When suggesting features:

- Explain the problem you're solving
- Describe your proposed solution
- Consider implementation complexity
- Think about user impact

## 🏆 Recognition

We recognize and appreciate all contributors:

- Contributors are listed in our README
- Significant contributions get special mention
- We highlight contributors in our releases
- Community members can become maintainers

## 🆘 Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and community chat
- **Documentation**: Check our docs first
- **Code Review**: Ask questions in PR reviews

## 📄 Code of Conduct

We're committed to providing a welcoming and inclusive environment. Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## 🎉 Thank You!

Your contributions help make AI more ethical and fair. Thank you for being part of our mission to build responsible AI systems!

---

**Ready to contribute?** [Pick an issue](https://github.com/radhi1991/fairmind/issues) and get started! 🚀

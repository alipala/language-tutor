# Language Tutor API Integration Tests

This directory contains comprehensive integration tests for the Language Tutor FastAPI backend. The test suite is designed to ensure all API endpoints function correctly and maintain backward compatibility.

## 📋 Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Getting Started](#getting-started)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Configuration](#configuration)
- [CI/CD Integration](#cicd-integration)
- [Writing New Tests](#writing-new-tests)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The test suite provides:

- **Comprehensive API Coverage**: Tests for all major endpoints
- **Authentication & Security**: User management, JWT tokens, permissions
- **Business Logic Validation**: Learning plans, progress tracking, subscriptions
- **Database Integration**: MongoDB operations and data persistence
- **External Service Mocking**: Stripe, OpenAI, email services
- **Error Handling**: Edge cases and failure scenarios
- **Performance Testing**: Response times and load handling

## 🏗️ Test Structure

```
backend/tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared fixtures and configuration
├── requirements.txt            # Test dependencies
├── README.md                   # This documentation
└── integration/                # Integration test modules
    ├── __init__.py
    ├── test_auth_routes.py      # Authentication & user management
    ├── test_learning_routes.py  # Learning plans & goals
    ├── test_stripe_routes.py    # Subscriptions & payments
    └── test_progress_routes.py  # Progress tracking & analytics
```

### Test Categories

#### 🔐 Authentication Tests (`test_auth_routes.py`)
- User registration and login
- Email verification
- Password management (reset, update)
- Profile management
- Voice preferences
- Google OAuth integration
- Security validation
- Rate limiting

#### 📚 Learning Tests (`test_learning_routes.py`)
- Learning goals management
- Learning plan creation and retrieval
- Assessment data handling
- Session progress tracking
- Plan assignment and ownership
- Content generation validation

#### 💳 Subscription Tests (`test_stripe_routes.py`)
- Subscription status and limits
- Checkout session creation
- Customer portal access
- Usage tracking
- Feature access control
- Webhook handling
- Payment processing

#### 📊 Progress Tests (`test_progress_routes.py`)
- Conversation session saving
- Progress statistics
- Conversation history
- Enhanced analysis
- Achievements system
- Streak calculation

## 🚀 Getting Started

### Prerequisites

1. **Python 3.10+** installed
2. **MongoDB** running locally (default: `localhost:27017`)
3. **Git** for version control

### Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone https://github.com/alipala/language-tutor.git
   cd language-tutor/backend
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r tests/requirements.txt
   ```

3. **Start MongoDB**:
   ```bash
   # Using MongoDB service
   sudo systemctl start mongod
   
   # Or using Docker
   docker run -d -p 27017:27017 mongo:6.0
   
   # Or using Homebrew (macOS)
   brew services start mongodb-community
   ```

4. **Verify setup**:
   ```bash
   python run_tests.py --quick
   ```

## 🧪 Running Tests

### Using the Test Runner (Recommended)

The `run_tests.py` script provides a convenient interface:

```bash
# Run all tests
python run_tests.py

# Run specific test categories
python run_tests.py --auth          # Authentication tests only
python run_tests.py --learning      # Learning routes tests only
python run_tests.py --stripe        # Stripe/subscription tests only
python run_tests.py --progress      # Progress tracking tests only

# Run with coverage
python run_tests.py --coverage --coverage-fail 80

# Quick smoke tests
python run_tests.py --quick

# Verbose output with parallel execution
python run_tests.py --verbose --parallel 4

# Generate reports
python run_tests.py --html-report --junit-xml

# Run linting and security checks
python run_tests.py --lint --security
```

### Using pytest Directly

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific test file
pytest tests/integration/test_auth_routes.py -v

# Run specific test class
pytest tests/integration/test_auth_routes.py::TestUserRegistration -v

# Run specific test method
pytest tests/integration/test_auth_routes.py::TestUserRegistration::test_register_new_user_success -v

# Run with coverage
pytest tests/integration/ --cov=. --cov-report=html

# Run in parallel
pytest tests/integration/ -n 4

# Run with custom markers
pytest tests/integration/ -m "not slow"
```

### Environment Variables

The test suite automatically sets up a test environment, but you can override:

```bash
export ENVIRONMENT=test
export DATABASE_NAME=language_tutor_test
export TEST_MONGODB_URL=mongodb://localhost:27017
export OPENAI_API_KEY=test_openai_key
export STRIPE_SECRET_KEY=sk_test_123
```

## 📊 Test Categories

### Unit Tests vs Integration Tests

- **Integration Tests** (current): Test complete API endpoints with database
- **Unit Tests** (future): Test individual functions and classes in isolation

### Test Markers

Tests can be marked for selective execution:

```python
@pytest.mark.slow
def test_large_data_processing():
    # Long-running test
    pass

@pytest.mark.auth
def test_authentication_flow():
    # Authentication-related test
    pass
```

Run marked tests:
```bash
pytest -m "auth"           # Run only auth tests
pytest -m "not slow"       # Skip slow tests
pytest -m "auth and not slow"  # Auth tests that aren't slow
```

## ⚙️ Configuration

### Test Database

Tests use a separate test database (`language_tutor_test`) that is:
- Created automatically before tests
- Cleaned between test runs
- Dropped after test completion

### Fixtures

Key fixtures available in all tests:

- `client`: Async HTTP client for API requests
- `test_user`: Authenticated test user
- `premium_user`: Premium subscription user
- `auth_headers`: Authentication headers
- `clean_db`: Clean database state
- `sample_learning_plan`: Test learning plan data
- `sample_assessment_data`: Test assessment data

### Mocking

External services are mocked:
- **OpenAI API**: Mocked for learning plan generation
- **Stripe API**: Mocked for payment processing
- **Email Service**: Mocked for email sending
- **Google OAuth**: Mocked for authentication

## 🔄 CI/CD Integration

### GitHub Actions

The test suite integrates with GitHub Actions (`.github/workflows/api-tests.yml`):

- **Triggers**: Pull requests and pushes to main/develop
- **Environment**: Ubuntu with MongoDB service
- **Coverage**: Generates coverage reports
- **Artifacts**: Test reports, coverage data, security scans
- **Matrix Testing**: Multiple Python and MongoDB versions

### Workflow Jobs

1. **api-tests**: Main integration test suite
2. **test-matrix**: Cross-version compatibility testing
3. **performance-tests**: Performance benchmarks
4. **security-scan**: Security vulnerability scanning
5. **test-summary**: Results aggregation and reporting

### Branch Protection

Configure branch protection rules to require:
- All tests passing
- Minimum code coverage (70%+)
- Security scan approval
- Code review approval

## ✍️ Writing New Tests

### Test Structure

Follow this pattern for new tests:

```python
class TestNewFeature:
    """Test new feature functionality."""
    
    async def test_feature_success_case(self, client: AsyncClient, auth_headers):
        """Test successful feature operation."""
        # Arrange
        test_data = {"key": "value"}
        
        # Act
        response = await client.post("/api/new-feature", json=test_data, headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    async def test_feature_validation_error(self, client: AsyncClient, auth_headers):
        """Test feature with invalid input."""
        # Test validation and error handling
        pass
    
    async def test_feature_unauthorized(self, client: AsyncClient):
        """Test feature without authentication."""
        # Test security
        pass
```

### Best Practices

1. **Test Names**: Use descriptive names that explain what is being tested
2. **AAA Pattern**: Arrange, Act, Assert
3. **One Assertion**: Focus each test on one specific behavior
4. **Test Data**: Use fixtures for reusable test data
5. **Error Cases**: Test both success and failure scenarios
6. **Security**: Always test authentication and authorization
7. **Documentation**: Add docstrings explaining test purpose

### Adding New Test Files

1. Create new test file in `tests/integration/`
2. Follow naming convention: `test_<module>_routes.py`
3. Import required fixtures from `conftest.py`
4. Add comprehensive test coverage
5. Update this README if needed

## 🔧 Troubleshooting

### Common Issues

#### MongoDB Connection Failed
```
Error: MongoDB is not accessible
```
**Solution**: Ensure MongoDB is running:
```bash
# Check if MongoDB is running
mongosh --eval "db.adminCommand('ping')"

# Start MongoDB
sudo systemctl start mongod
# or
brew services start mongodb-community
```

#### Import Errors
```
ModuleNotFoundError: No module named 'pytest'
```
**Solution**: Install test dependencies:
```bash
pip install -r tests/requirements.txt
```

#### Test Database Issues
```
Error: Database operation failed
```
**Solution**: Clean test database:
```bash
mongosh language_tutor_test --eval "db.dropDatabase()"
```

#### Permission Errors
```
PermissionError: [Errno 13] Permission denied
```
**Solution**: Check file permissions:
```bash
chmod +x run_tests.py
```

### Debug Mode

Run tests with debug information:

```bash
# Verbose output
python run_tests.py --verbose

# Show all output (including print statements)
pytest tests/integration/ -s -v

# Debug specific test
pytest tests/integration/test_auth_routes.py::TestUserRegistration::test_register_new_user_success -s -v --pdb
```

### Performance Issues

If tests are slow:

1. **Use parallel execution**: `python run_tests.py --parallel 4`
2. **Run specific tests**: `python run_tests.py --quick`
3. **Check MongoDB performance**: Ensure MongoDB has sufficient resources
4. **Profile tests**: Use `--durations=10` to see slowest tests

### Memory Issues

For memory-related problems:

1. **Reduce parallel workers**: Lower the `-n` value
2. **Run tests in smaller batches**: Test individual modules
3. **Monitor memory usage**: Use system monitoring tools

## 📈 Coverage Goals

- **Overall Coverage**: 80%+
- **Critical Paths**: 95%+
- **New Features**: 90%+
- **Bug Fixes**: 100% of affected code

Generate coverage report:
```bash
python run_tests.py --coverage
open htmlcov/index.html  # View detailed coverage report
```

## 🤝 Contributing

When contributing new tests:

1. **Follow existing patterns** and conventions
2. **Add comprehensive coverage** for new features
3. **Test edge cases** and error conditions
4. **Update documentation** as needed
5. **Ensure tests pass** in CI/CD pipeline

## 📞 Support

For questions or issues:

1. **Check this documentation** first
2. **Review existing tests** for examples
3. **Check CI/CD logs** for detailed error information
4. **Create an issue** in the repository with:
   - Test command used
   - Full error output
   - Environment details (OS, Python version, etc.)

---

*This test suite is continuously evolving. Please keep this documentation updated as new tests and features are added.*

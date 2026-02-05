# Test Suite

Comprehensive test suite for the netdiag application with **93 tests** achieving **61% overall coverage**.

**Cross-platform support:** Tests include real ping outputs from macOS, Linux (iputils), and Windows.

## Test Philosophy

This test suite follows these principles:
- ✨ **Minimal mocking** - Use real data and pure functions when possible
- 🎯 **Fixtures over duplication** - Shared test data for consistency
- 🚀 **Fast by default** - Unit tests run in <1 second
- 🔌 **Optional integration** - Real system tests marked separately

## Running Tests

```bash
# Run all unit tests (fast, ~0.3s)
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/analysis/test_ping.py -v

# Run with coverage
pytest --cov=netdiag --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=netdiag --cov-report=html
# Then open htmlcov/index.html
```

## Test Categories

### Unit Tests (Default)
Fast tests using real data or minimal mocking:
```bash
pytest -m "not integration"
```

### Integration Tests (Optional)
Slower tests that execute real commands:
```bash
pytest -m integration
```

### Network Tests (Optional)
Tests requiring internet access:
```bash
pytest -m network
```

### Skip Slow Tests
```bash
pytest -m "not slow and not integration"
```

## Test Organization

```
tests/
├── conftest.py                  # Shared fixtures (auto-discovered)
├── fixtures/
│   ├── __init__.py
│   └── ping_samples.py          # Real outputs: macOS, Linux, Windows
├── data/
│   ├── __init__.py
│   └── test_ping.py             # Data structure validation (no mocks)
├── analysis/
│   ├── __init__.py
│   └── test_ping.py             # Analysis logic tests (pure functions)
├── probes/
│   ├── __init__.py
│   ├── test_ping.py             # Basic probe tests
│   └── test_ping_crossplatform.py  # Cross-platform parsing tests
├── test_cli.py                  # CLI tests (fixture-based mocking)
└── README.md                    # This file
```

## Coverage Summary

| Module | Coverage | Notes |
|--------|----------|-------|
| `cli.py` | **100%** | Complete CLI coverage |
| `data/ping.py` | **100%** | All data structures tested |
| `probes/ping.py` | **100%** | All probe logic tested |
| `analysis/ping.py` | **95%** | Core analysis covered |

Overall: **61%** (449 statements, 176 missing)

*Lower overall percentage due to untested modules: database, config, OS adapters, presentation*

## Cross-Platform Testing

The test suite includes real ping outputs from all supported platforms:

### Platform Samples (`tests/fixtures/ping_samples.py`)

```python
from tests.fixtures.ping_samples import (
    MACOS_SAMPLES,      # 6 scenarios
    LINUX_SAMPLES,      # 4 scenarios
    WINDOWS_SAMPLES,    # 6 scenarios
    ALL_PLATFORMS,      # Dictionary of all
)
```

### Cross-Platform Tests (`tests/probes/test_ping_crossplatform.py`)

Parametrized tests that verify:
- ✅ All platforms parse successful pings correctly
- ✅ Packet loss is detected on all platforms
- ✅ High latency diagnosis works everywhere
- ✅ Platform-specific edge cases handled (Windows `time<1ms`, macOS parentheses, etc.)

```python
@pytest.mark.parametrize("platform,samples", [
    ("macos", MACOS_SAMPLES),
    ("linux", LINUX_SAMPLES),
    ("windows", WINDOWS_SAMPLES),
])
def test_successful_ping_all_platforms(self, platform, samples):
    # Tests run for each platform automatically
```

## Test Structure

### 1. Data Layer Tests (`tests/data/`)
Pure data validation - no mocking needed:
- Dataclass creation
- Enum values
- Constant definitions
- Immutability checks

Example:
```python
def test_create_valid_metrics():
    metrics = PingMetrics(
        sent=10, received=9, loss_pct=10.0,
        rtt_min_ms=5.0, rtt_avg_ms=15.0, rtt_max_ms=25.0,
        rtt_stddev_ms=5.0, jitter=3.5, jitter_ratio=0.23
    )
    assert metrics.sent == 10
```

### 2. Analysis Layer Tests (`tests/analysis/`)
Pure function tests using fixtures:
- Signal detection
- Diagnosis inference
- Confidence scoring
- Evidence collection

Example:
```python
@pytest.fixture
def healthy_metrics():
    return PingMetrics(sent=10, received=10, loss_pct=0.0, ...)

def test_healthy_connection_signals(healthy_metrics):
    signals = build_ping_signals(healthy_metrics)
    assert not signals.high_loss
```

### 3. Probes Layer Tests (`tests/probes/`)
Minimal mocking for unit tests, real execution for integration:

**Unit Tests:**
```python
def test_successful_ping():
    mock_adapter = Mock()
    mock_adapter.execute_ping.return_value = subprocess.CompletedProcess(
        args=["ping"], returncode=0, stdout=MACOS_SUCCESS, stderr=""
    )
    record = run_ping(host="8.8.8.8", os_adapter=mock_adapter, ...)
    assert record.diagnosis.cause == DiagnosisCause.OK
```

**Integration Tests:**
```python
@pytest.mark.integration
def test_ping_localhost(real_adapter):
    record = run_ping(host="127.0.0.1", os_adapter=real_adapter, ...)
    assert record.metrics.received >= 2
```

### 4. CLI Tests (`tests/test_cli.py`)
Fixture-based mocking for clean, maintainable tests:
```python
@pytest.fixture
def mock_cmd_ping_deps():
    with patch("netdiag.cli.run_ping") as mock_run_ping, \
         patch("netdiag.cli.get_os_adapter") as mock_os_adapter, \
         ...
        yield {"run_ping": mock_run_ping, "os_adapter": mock_os_adapter}

def test_something(mock_cmd_ping_deps):
    mocks = mock_cmd_ping_deps
    mocks["run_ping"].return_value = sample_record
    # Test code is clean and focused
```

## Key Testing Patterns

### ✨ Fixtures for Shared Data
```python
@pytest.fixture
def healthy_metrics():
    """Reusable healthy connection metrics"""
    return PingMetrics(...)

def test_one(healthy_metrics):
    # Use fixture

def test_two(healthy_metrics):
    # Reuse same fixture
```

### 🎯 Real Samples for Parser Tests
```python
# tests/fixtures/ping_samples.py
MACOS_SUCCESS = """PING 8.8.8.8 ..."""
LINUX_PACKET_LOSS = """PING 8.8.8.8 ..."""

# tests/probes/test_ping.py
from tests.fixtures.ping_samples import MACOS_SUCCESS

def test_parse_macos():
    # Test with real output
```

### 🔌 Parameterized Tests
```python
@pytest.mark.parametrize("loss_pct,expected_confidence", [
    (20.0, 0.95),  # Very high loss
    (10.0, 0.85),  # Moderate loss
    (6.0, 0.70),   # Low loss
])
def test_confidence_tiers(loss_pct, expected_confidence):
    metrics = PingMetrics(loss_pct=loss_pct, ...)
    confidence = compute_confidence(metrics, DiagnosisCause.HIGH_LOSS)
    assert confidence == expected_confidence
```

### 🎭 Context Manager Mocking
```python
@pytest.fixture
def mock_main_deps():
    with patch("netdiag.cli.build_parser") as mock_parser, \
         patch("netdiag.cli.load_config") as mock_config, \
         ...
        yield {
            "parser": mock_parser,
            "config": mock_config,
        }
```

## Adding New Tests

### For Pure Functions (Preferred)
```python
def test_my_function():
    """Test with real data - no mocks needed"""
    result = my_function(real_input)
    assert result == expected_output
```

### For System Interactions
```python
def test_with_mock():
    """Test with minimal mocking"""
    mock_system = Mock()
    mock_system.method.return_value = fake_data
    result = function_under_test(mock_system)
    assert result.field == expected_value
```

### For Integration Tests
```python
@pytest.mark.integration
@pytest.mark.slow
def test_real_execution():
    """Real system test"""
    result = run_real_command()
    assert result.success
```

## Writing Good Tests

### ✅ DO
- Use descriptive test names
- Test one thing per test
- Use fixtures for shared data
- Prefer real data over mocks
- Mark slow tests appropriately

### ❌ DON'T
- Mock everything unnecessarily
- Write tests that depend on each other
- Duplicate test data
- Skip error case testing
- Write tests without docstrings

## CI/CD Usage

```bash
# Fast CI pipeline (unit tests only)
pytest -m "not integration and not network" --cov=netdiag

# Full test suite (including integration)
pytest --cov=netdiag

# Parallel execution
pytest -n auto
```

## Troubleshooting

### Tests fail on specific platform
```bash
# Check which platform-specific samples are failing
pytest tests/fixtures/ -v
```

### Coverage not showing
```bash
# Install pytest-cov
pip install pytest-cov

# Run with explicit coverage
pytest --cov=netdiag --cov-report=html
```

### Integration tests timeout
```bash
# Skip integration tests
pytest -m "not integration"

# Or increase timeout (if configured)
pytest --timeout=300
```

## Test Metrics

- **Total Tests**: 93
- **Test Files**: 6
- **Platforms Tested**: macOS, Linux (iputils), Windows
- **Ping Samples**: 16 real outputs across 3 platforms
- **Fixtures**: 5 shared (conftest.py), 16 platform samples
- **Execution Time**: ~0.16s (unit tests only)
- **Lines of Test Code**: ~1,350
- **Test to Code Ratio**: 3.0:1

### Platform Coverage

| Platform | Samples | Edge Cases |
|----------|---------|------------|
| macOS | 6 | Parenthesized time values |
| Linux (iputils) | 4 | mdev instead of stddev |
| Windows | 6 | time<1ms, decimal milliseconds |

---

*Last updated: 2024*

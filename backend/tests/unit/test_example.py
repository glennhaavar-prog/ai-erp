"""
Example unit tests for AI-ERP backend
Demonstrates testing patterns and best practices
"""
import pytest
from datetime import datetime


# Example: Testing a simple function
def add_numbers(a: int, b: int) -> int:
    """Simple function for testing example"""
    return a + b


def test_add_numbers():
    """Test that add_numbers works correctly"""
    assert add_numbers(2, 3) == 5
    assert add_numbers(-1, 1) == 0
    assert add_numbers(0, 0) == 0


# Example: Testing with parametrize (multiple test cases)
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (10, 20, 30),
    (-5, 5, 0),
    (0, 0, 0),
])
def test_add_numbers_parametrized(a, b, expected):
    """Test add_numbers with multiple inputs"""
    assert add_numbers(a, b) == expected


# Example: Testing with fixtures
@pytest.fixture
def sample_client():
    """Fixture providing sample client data"""
    return {
        "id": "test-client-123",
        "name": "Test Client AS",
        "org_number": "999999999",
        "is_demo": True
    }


def test_client_has_required_fields(sample_client):
    """Test that client fixture has required fields"""
    assert "id" in sample_client
    assert "name" in sample_client
    assert "org_number" in sample_client
    assert sample_client["is_demo"] is True


# Example: Testing exceptions
def divide(a: int, b: int) -> float:
    """Division function for testing exceptions"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def test_divide_by_zero_raises_error():
    """Test that dividing by zero raises ValueError"""
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)


def test_divide_normal():
    """Test normal division"""
    assert divide(10, 2) == 5.0
    assert divide(9, 3) == 3.0


# TODO: Add real tests for:
# - app.services.dashboard.calculate_client_statuses()
# - app.models.client.Client validation
# - app.utils.date_utils date formatting
# - app.services.ai_agent AI response parsing

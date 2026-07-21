"""
Pytest configuration for extracao_contabil project.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

Usuario = get_user_model()


@pytest.fixture
def usuario(db):
    """Create a test user."""
    return Usuario.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def usuario_admin(db):
    """Create an admin user."""
    return Usuario.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
    )


@pytest.fixture
def request_factory():
    """Django request factory."""
    return RequestFactory()

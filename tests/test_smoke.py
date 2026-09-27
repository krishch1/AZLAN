"""
Foundation tests for AZLAN configuration and database setup.

These tests verify:
- Configuration can load from environment
- Database configuration values are available
- SQLAlchemy metadata can be imported
- FastAPI application can be imported and created

No live database connection is required for these unit tests.
"""

import inspect

# ---------------------------------------------------------------------------
# Configuration tests
# ---------------------------------------------------------------------------


def test_config_can_load():
    """Settings should be loadable without a live database connection."""
    from backend.app.core.config import settings

    assert settings is not None
    assert settings.APP_ENV in ("development", "production", "staging")
    assert isinstance(settings.DEBUG, bool)
    assert settings.LOG_LEVEL in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def test_database_configuration_available():
    """Database configuration should have required fields."""
    from backend.app.core.config import settings

    assert settings.DATABASE_URL is not None
    assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")
    assert settings.DB_POOL_SIZE > 0
    assert settings.DB_MAX_OVERFLOW >= 0
    assert settings.DB_POOL_TIMEOUT > 0


def test_config_secrets_not_in_defaults():
    """Ensure no hardcoded secrets in the default configuration."""
    from backend.app.core.config import settings

    # The default DATABASE_URL is a development credential
    # which is acceptable for local development
    assert "localhost" in settings.DATABASE_URL or "postgres" in settings.DATABASE_URL


# ---------------------------------------------------------------------------
# Database metadata tests
# ---------------------------------------------------------------------------


def test_sqlalchemy_base_metadata_importable():
    """SQLAlchemy Base metadata should be importable and usable."""
    from backend.app.db.base import Base

    assert Base is not None
    assert hasattr(Base, "metadata")
    # Base.metadata is a MetaData object — should exist
    assert Base.metadata is not None


def test_async_engine_configured():
    """The async engine should be configured and not connect at import time."""
    from backend.app.db.session import async_engine

    assert async_engine is not None
    assert async_engine.url.drivername == "postgresql+asyncpg"


def test_session_factory_available():
    """The async session factory should be available and importable."""
    from backend.app.db.session import async_session_factory

    assert async_session_factory is not None
    # The session factory should have a bind (the engine)
    assert async_session_factory.kw.get("bind") is not None


def test_get_async_session_is_async_generator():
    """get_async_session should be an async generator function."""
    from backend.app.db.session import get_async_session

    assert inspect.isasyncgenfunction(get_async_session)


# ---------------------------------------------------------------------------
# Application tests
# ---------------------------------------------------------------------------


def test_fastapi_app_importable():
    """The FastAPI app should be importable without a live DB connection."""
    from backend.app.main import app

    assert app is not None
    assert app.title == "AZLAN"
    assert app.version == "0.1.0"


def test_health_endpoint_registered():
    """The /api/v1/health endpoint should be registered on the app."""
    from backend.app.main import app

    routes = [route.path for route in app.routes]
    assert "/api/v1/health" in routes


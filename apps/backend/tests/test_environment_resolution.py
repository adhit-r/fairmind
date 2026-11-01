"""The settings class and the environment field must never disagree.

Reading the class from NODE_ENV while pydantic filled Settings.environment from
ENVIRONMENT let NODE_ENV=production + ENVIRONMENT=development build a
ProductionSettings whose is_development was True. That combination skipped the
Neon auth middleware despite NEON_AUTH_ENABLED=true and switched on the dev
auto-login, so it is the case worth pinning down.
"""

import pytest

from config.settings import (
    DevelopmentSettings,
    ProductionSettings,
    get_settings,
    resolve_environment,
)

SECRET = "x" * 48


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def env(monkeypatch):
    def _set(node_env=None, environment=None):
        for name, value in (("NODE_ENV", node_env), ("ENVIRONMENT", environment)):
            if value is None:
                monkeypatch.delenv(name, raising=False)
            else:
                monkeypatch.setenv(name, value)
        monkeypatch.setenv("SECRET_KEY", SECRET)
        monkeypatch.setenv("JWT_SECRET", SECRET)

    return _set


@pytest.mark.parametrize(
    "node_env, environment, expected",
    [
        (None, None, "development"),
        ("production", None, "production"),
        (None, "production", "production"),
        ("production", "production", "production"),
        ("production", "staging", "staging"),
        # The regression: ENVIRONMENT wins, so the class matches the field.
        ("production", "development", "development"),
    ],
)
def test_resolve_environment(env, node_env, environment, expected):
    env(node_env, environment)
    assert resolve_environment() == expected


@pytest.mark.parametrize(
    "node_env, environment",
    [
        (None, None),
        ("production", None),
        (None, "production"),
        ("production", "production"),
        ("production", "staging"),
        ("production", "development"),
        ("development", "production"),
    ],
)
def test_settings_class_agrees_with_environment_field(env, node_env, environment):
    env(node_env, environment)
    settings = get_settings()

    assert settings.environment == resolve_environment()
    assert settings.is_production is (settings.environment == "production")
    assert settings.is_development is (settings.environment == "development")
    assert not (settings.is_production and settings.is_development)

    expected_cls = ProductionSettings if settings.is_production else DevelopmentSettings
    assert isinstance(settings, expected_cls)


def test_production_node_env_with_development_environment_is_not_production(env):
    """The exact combination that used to report is_development on ProductionSettings."""
    env("production", "development")
    settings = get_settings()

    assert isinstance(settings, DevelopmentSettings)
    assert settings.is_development is True
    assert settings.is_production is False


def test_production_is_never_also_development(env):
    env("production", None)
    settings = get_settings()

    assert isinstance(settings, ProductionSettings)
    assert settings.is_production is True
    assert settings.is_development is False

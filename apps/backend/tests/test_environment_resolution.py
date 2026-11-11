"""The settings class and the environment field must never disagree.

Reading the class from NODE_ENV while pydantic filled Settings.environment from
ENVIRONMENT let NODE_ENV=production + ENVIRONMENT=development build a
ProductionSettings whose is_development was True. That combination skipped the
Neon auth middleware despite NEON_AUTH_ENABLED=true and switched on the dev
auto-login, so it is the case worth pinning down.
"""

import pytest

import config.settings as settings_module
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
    # Only the variables a test sets count, not the developer's own .env.
    monkeypatch.setattr(settings_module, "_ENV_FILE", None)

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
        # Nothing set means production, so a deploy cannot forget its way into dev mode.
        (None, None, "production"),
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


@pytest.mark.parametrize("missing", ["SECRET_KEY", "JWT_SECRET"])
def test_production_refuses_to_start_without_explicit_secrets(env, monkeypatch, missing):
    env(environment="production")
    monkeypatch.delenv(missing)
    with pytest.raises(ValueError, match=missing):
        ProductionSettings(_env_file=None)


def test_development_still_starts_without_secrets(env, monkeypatch):
    env(environment="development")
    monkeypatch.delenv("SECRET_KEY")
    monkeypatch.delenv("JWT_SECRET")
    assert DevelopmentSettings(_env_file=None).secret_key


def test_env_file_is_read_when_the_process_sets_nothing(env, monkeypatch, tmp_path):
    env()
    env_file = tmp_path / ".env"
    env_file.write_text("NODE_ENV=development\n")
    monkeypatch.setattr(settings_module, "_ENV_FILE", str(env_file))
    assert resolve_environment() == "development"
    monkeypatch.setenv("ENVIRONMENT", "production")
    assert resolve_environment() == "production"


@pytest.mark.parametrize(
    "url, local",
    [
        ("postgresql://u@127.0.0.1:55440/db", True),
        ("postgresql://u@localhost/db", True),
        ("postgresql://u@[::1]:5432/db", True),
        ("postgresql://u:p@ep-x.eu-central-1.aws.neon.tech/db?sslmode=require", False),
        ("postgresql://u@10.0.0.5/db", False),
    ],
)
def test_dev_login_needs_a_local_database(env, url, local):
    from middleware.security import dev_login_email

    env(environment="development")
    dev = DevelopmentSettings(_env_file=None, database_url=url, fairmind_dev_login_email="dev@fairmind.test")
    assert dev.database_is_local is local
    assert (dev_login_email(dev) is not None) is local
    prod = ProductionSettings(_env_file=None, environment="production", database_url=url, fairmind_dev_login_email="dev@fairmind.test")
    assert dev_login_email(prod) is None

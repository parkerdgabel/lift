"""Tests for configuration service."""

import tempfile
from pathlib import Path

import pytest

from lift.core.database import DatabaseManager, reset_db_instance
from lift.core.models import MeasurementUnit, WeightUnit
from lift.services.config_service import ConfigService


@pytest.fixture
def db():
    """Create a temporary test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        reset_db_instance()
        db = DatabaseManager(str(db_path))
        db.initialize_database()
        yield db
        reset_db_instance()


def test_get_setting(db):
    """Test getting a setting value."""
    config_service = ConfigService(db)

    # Get existing setting (from defaults)
    value = config_service.get_setting("default_weight_unit")
    assert value == "lbs"

    # Get non-existent setting
    value = config_service.get_setting("nonexistent_key")
    assert value is None


def test_set_setting(db):
    """Test setting a configuration value."""
    config_service = ConfigService(db)

    # Set new setting
    setting = config_service.set_setting("test_key", "test_value", "Test description")

    assert setting.key == "test_key"
    assert setting.value == "test_value"
    assert setting.description == "Test description"

    # Verify it was saved
    value = config_service.get_setting("test_key")
    assert value == "test_value"


def test_update_setting(db):
    """Test updating an existing setting."""
    config_service = ConfigService(db)

    # Set initial value
    config_service.set_setting("test_key", "initial_value")

    # Update the value
    setting = config_service.set_setting("test_key", "updated_value")

    assert setting.value == "updated_value"

    # Verify update
    value = config_service.get_setting("test_key")
    assert value == "updated_value"


def test_get_all_settings(db):
    """Test getting all settings."""
    config_service = ConfigService(db)

    settings = config_service.get_all_settings()

    # Should include defaults
    assert isinstance(settings, dict)
    assert "default_weight_unit" in settings
    assert "default_measurement_unit" in settings
    assert "enable_rpe" in settings

    # Set a custom setting
    config_service.set_setting("custom_key", "custom_value")

    # Verify it appears in all settings
    settings = config_service.get_all_settings()
    assert "custom_key" in settings
    assert settings["custom_key"] == "custom_value"


def test_get_all_settings_detailed(db):
    """Test getting all settings with details."""
    config_service = ConfigService(db)

    settings = config_service.get_all_settings_detailed()

    assert isinstance(settings, list)
    assert len(settings) > 0

    # Verify structure
    for setting in settings:
        assert hasattr(setting, "key")
        assert hasattr(setting, "value")
        assert hasattr(setting, "description")
        assert hasattr(setting, "updated_at")


def test_delete_setting(db):
    """Test deleting a setting."""
    config_service = ConfigService(db)

    # Set a custom setting
    config_service.set_setting("to_delete", "value")

    # Verify it exists
    value = config_service.get_setting("to_delete")
    assert value == "value"

    # Delete it
    deleted = config_service.delete_setting("to_delete")
    assert deleted is True

    # Verify it's gone from database
    with db.get_connection() as conn:
        result = conn.execute("SELECT key FROM settings WHERE key = 'to_delete'").fetchone()
        assert result is None

    # Delete non-existent setting
    deleted = config_service.delete_setting("nonexistent")
    assert deleted is False


def test_reset_to_defaults(db):
    """Test resetting all settings to defaults."""
    config_service = ConfigService(db)

    # Set some custom settings
    config_service.set_setting("custom1", "value1")
    config_service.set_setting("custom2", "value2")

    # Modify a default
    config_service.set_setting("default_weight_unit", "kg")

    # Reset to defaults
    config_service.reset_to_defaults()

    # Verify defaults are restored
    value = config_service.get_setting("default_weight_unit")
    assert value == "lbs"

    # Verify custom settings are gone
    value = config_service.get_setting("custom1")
    assert value is None


def test_get_default_weight_unit(db):
    """Test getting default weight unit."""
    config_service = ConfigService(db)

    # Default should be LBS
    unit = config_service.get_default_weight_unit()
    assert unit == WeightUnit.LBS

    # Change to KG
    config_service.set_setting("default_weight_unit", "kg")
    unit = config_service.get_default_weight_unit()
    assert unit == WeightUnit.KG

    # Test case insensitivity
    config_service.set_setting("default_weight_unit", "KG")
    unit = config_service.get_default_weight_unit()
    assert unit == WeightUnit.KG


def test_get_default_measurement_unit(db):
    """Test getting default measurement unit."""
    config_service = ConfigService(db)

    # Default should be INCHES
    unit = config_service.get_default_measurement_unit()
    assert unit == MeasurementUnit.INCHES

    # Change to CM
    config_service.set_setting("default_measurement_unit", "cm")
    unit = config_service.get_default_measurement_unit()
    assert unit == MeasurementUnit.CENTIMETERS


def test_is_rpe_enabled(db):
    """Test checking if RPE is enabled."""
    config_service = ConfigService(db)

    # Default should be enabled
    enabled = config_service.is_rpe_enabled()
    assert enabled is True

    # Disable it
    config_service.set_setting("enable_rpe", "false")
    enabled = config_service.is_rpe_enabled()
    assert enabled is False

    # Test various true values
    for value in ["true", "True", "TRUE", "1", "yes"]:
        config_service.set_setting("enable_rpe", value)
        assert config_service.is_rpe_enabled() is True

    # Test various false values
    for value in ["false", "False", "FALSE", "0", "no"]:
        config_service.set_setting("enable_rpe", value)
        assert config_service.is_rpe_enabled() is False


def test_is_tempo_enabled(db):
    """Test checking if tempo tracking is enabled."""
    config_service = ConfigService(db)

    # Default should be disabled
    enabled = config_service.is_tempo_enabled()
    assert enabled is False

    # Enable it
    config_service.set_setting("enable_tempo", "true")
    enabled = config_service.is_tempo_enabled()
    assert enabled is True


def test_get_rest_timer_default(db):
    """Test getting default rest timer."""
    config_service = ConfigService(db)

    # Default should be 90 seconds
    timer = config_service.get_rest_timer_default()
    assert timer == 90

    # Change it
    config_service.set_setting("rest_timer_default", "120")
    timer = config_service.get_rest_timer_default()
    assert timer == 120

    # Test invalid value (should return default)
    config_service.set_setting("rest_timer_default", "invalid")
    timer = config_service.get_rest_timer_default()
    assert timer == 90


def test_is_auto_pr_detection_enabled(db):
    """Test checking if auto PR detection is enabled."""
    config_service = ConfigService(db)

    # Default should be enabled
    enabled = config_service.is_auto_pr_detection_enabled()
    assert enabled is True

    # Disable it
    config_service.set_setting("auto_detect_pr", "false")
    enabled = config_service.is_auto_pr_detection_enabled()
    assert enabled is False


def test_settings_persistence(db):
    """Test that settings persist across service instances."""
    config_service1 = ConfigService(db)

    # Set a value
    config_service1.set_setting("persist_test", "persisted_value")

    # Create new service instance
    config_service2 = ConfigService(db)

    # Verify value persisted
    value = config_service2.get_setting("persist_test")
    assert value == "persisted_value"


def test_setting_without_description(db):
    """Test setting a value without description."""
    config_service = ConfigService(db)

    # Set without description
    setting = config_service.set_setting("no_desc", "value")

    assert setting.key == "no_desc"
    assert setting.value == "value"
    assert setting.description is None


def test_update_setting_with_new_description(db):
    """Test updating a setting and adding description."""
    config_service = ConfigService(db)

    # Set without description
    config_service.set_setting("test", "value")

    # Update with description
    setting = config_service.set_setting("test", "new_value", "New description")

    assert setting.value == "new_value"
    assert setting.description == "New description"

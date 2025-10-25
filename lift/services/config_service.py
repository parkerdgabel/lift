"""Service for managing application configuration and settings."""

from datetime import datetime

from lift.core.database import DatabaseManager
from lift.core.models import MeasurementUnit, Setting, WeightUnit


class ConfigService:
    """Service for managing application configuration settings."""

    # Default settings
    DEFAULT_SETTINGS = {
        "default_weight_unit": "lbs",
        "default_measurement_unit": "in",
        "enable_rpe": "true",
        "enable_tempo": "false",
        "rest_timer_default": "90",
        "auto_detect_pr": "true",
        "database_path": "~/.lift/lift.duckdb",
    }

    def __init__(self, db: DatabaseManager) -> None:
        """
        Initialize the configuration service.

        Args:
            db: Database manager instance
        """
        self.db = db

    def get_setting(self, key: str) -> str | None:
        """
        Get a configuration setting value.

        Args:
            key: Setting key to retrieve

        Returns:
            Setting value or None if not found
        """
        with self.db.get_connection() as conn:
            result = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()

            if result:
                return result[0]

            # Return default if exists
            return self.DEFAULT_SETTINGS.get(key)

    def set_setting(self, key: str, value: str, description: str | None = None) -> Setting:
        """
        Set a configuration setting value.

        Creates the setting if it doesn't exist, updates if it does.

        Args:
            key: Setting key
            value: Setting value
            description: Optional description of the setting

        Returns:
            Updated Setting object
        """
        with self.db.get_connection() as conn:
            # Check if setting exists
            existing = conn.execute("SELECT key FROM settings WHERE key = ?", (key,)).fetchone()

            now = datetime.now()

            if existing:
                # Update existing setting
                if description:
                    conn.execute(
                        "UPDATE settings SET value = ?, description = ?, updated_at = ? WHERE key = ?",
                        (value, description, now, key),
                    )
                else:
                    conn.execute(
                        "UPDATE settings SET value = ?, updated_at = ? WHERE key = ?",
                        (value, now, key),
                    )
            else:
                # Insert new setting
                conn.execute(
                    "INSERT INTO settings (key, value, description, updated_at) VALUES (?, ?, ?, ?)",
                    (key, value, description, now),
                )

            # Fetch and return the setting
            result = conn.execute(
                "SELECT key, value, description, updated_at FROM settings WHERE key = ?",
                (key,),
            ).fetchone()

            return Setting(
                key=result[0],
                value=result[1],
                description=result[2],
                updated_at=result[3],
            )

    def get_all_settings(self) -> dict[str, str]:
        """
        Get all configuration settings as a dictionary.

        Returns:
            Dictionary mapping setting keys to values
        """
        with self.db.get_connection() as conn:
            results = conn.execute("SELECT key, value FROM settings ORDER BY key").fetchall()

            settings = {row[0]: row[1] for row in results}

            # Add any defaults that aren't in the database
            for key, value in self.DEFAULT_SETTINGS.items():
                if key not in settings:
                    settings[key] = value

            return settings

    def get_all_settings_detailed(self) -> list[Setting]:
        """
        Get all configuration settings with full details.

        Returns:
            List of Setting objects
        """
        with self.db.get_connection() as conn:
            results = conn.execute(
                "SELECT key, value, description, updated_at FROM settings ORDER BY key"
            ).fetchall()

            settings = [
                Setting(
                    key=row[0],
                    value=row[1],
                    description=row[2],
                    updated_at=row[3],
                )
                for row in results
            ]

            return settings

    def delete_setting(self, key: str) -> bool:
        """
        Delete a configuration setting.

        Args:
            key: Setting key to delete

        Returns:
            True if setting was deleted, False if it didn't exist
        """
        with self.db.get_connection() as conn:
            # Check if setting exists
            existing = conn.execute("SELECT key FROM settings WHERE key = ?", (key,)).fetchone()

            if not existing:
                return False

            # Delete the setting
            conn.execute("DELETE FROM settings WHERE key = ?", (key,))
            return True

    def reset_to_defaults(self) -> None:
        """
        Reset all settings to their default values.

        This will delete all custom settings and restore defaults.
        """
        with self.db.get_connection() as conn:
            # Delete all settings
            conn.execute("DELETE FROM settings")

            # Insert defaults
            now = datetime.now()
            for key, value in self.DEFAULT_SETTINGS.items():
                # Get description from schema defaults
                descriptions = {
                    "default_weight_unit": "Default weight unit (lbs or kg)",
                    "default_measurement_unit": "Default measurement unit for body (in or cm)",
                    "enable_rpe": "Enable RPE tracking",
                    "enable_tempo": "Enable tempo tracking",
                    "rest_timer_default": "Default rest timer in seconds",
                    "auto_detect_pr": "Automatically detect and save personal records",
                    "database_path": "Path to database file",
                }

                conn.execute(
                    "INSERT INTO settings (key, value, description, updated_at) VALUES (?, ?, ?, ?)",
                    (key, value, descriptions.get(key), now),
                )

    def get_default_weight_unit(self) -> WeightUnit:
        """
        Get the default weight unit from settings.

        Returns:
            WeightUnit enum value
        """
        value = self.get_setting("default_weight_unit")
        if value and value.lower() == "kg":
            return WeightUnit.KG
        return WeightUnit.LBS

    def get_default_measurement_unit(self) -> MeasurementUnit:
        """
        Get the default measurement unit from settings.

        Returns:
            MeasurementUnit enum value
        """
        value = self.get_setting("default_measurement_unit")
        if value and value.lower() == "cm":
            return MeasurementUnit.CENTIMETERS
        return MeasurementUnit.INCHES

    def is_rpe_enabled(self) -> bool:
        """
        Check if RPE tracking is enabled.

        Returns:
            True if RPE is enabled, False otherwise
        """
        value = self.get_setting("enable_rpe")
        return value is not None and value.lower() in ["true", "1", "yes"]

    def is_tempo_enabled(self) -> bool:
        """
        Check if tempo tracking is enabled.

        Returns:
            True if tempo is enabled, False otherwise
        """
        value = self.get_setting("enable_tempo")
        return value is not None and value.lower() in ["true", "1", "yes"]

    def get_rest_timer_default(self) -> int:
        """
        Get the default rest timer duration in seconds.

        Returns:
            Rest timer duration in seconds
        """
        value = self.get_setting("rest_timer_default")
        try:
            return int(value) if value else 90
        except (ValueError, TypeError):
            return 90

    def is_auto_pr_detection_enabled(self) -> bool:
        """
        Check if automatic PR detection is enabled.

        Returns:
            True if auto PR detection is enabled, False otherwise
        """
        value = self.get_setting("auto_detect_pr")
        return value is not None and value.lower() in ["true", "1", "yes"]

"""Database connection and management using DuckDB."""

import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import duckdb


class DatabaseManager:
    """Manages DuckDB database connection and operations."""

    def __init__(self, db_path: str | None = None) -> None:
        """
        Initialize database manager.

        Args:
            db_path: Path to database file. If None, uses default ~/.lift/lift.duckdb
        """
        if db_path is None:
            db_path = self._get_default_db_path()

        self.db_path = Path(db_path).expanduser()
        self._ensure_db_directory()
        self._connection: duckdb.DuckDBPyConnection | None = None

    def _get_default_db_path(self) -> str:
        """Get the default database path from environment or use ~/.lift/lift.duckdb."""
        default_path = os.environ.get("LIFT_DB_PATH", "~/.lift/lift.duckdb")
        return default_path

    def _ensure_db_directory(self) -> None:
        """Ensure the database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """
        Context manager for database connections.

        Yields:
            DuckDB connection object

        Example:
            >>> with db.get_connection() as conn:
            ...     result = conn.execute("SELECT * FROM exercises").fetchall()
        """
        conn = duckdb.connect(str(self.db_path))
        try:
            yield conn
        finally:
            conn.close()

    def execute(self, query: str, parameters: tuple | None = None) -> list:
        """
        Execute a query and return results.

        Args:
            query: SQL query to execute
            parameters: Optional parameters for the query

        Returns:
            List of results
        """
        with self.get_connection() as conn:
            if parameters:
                result = conn.execute(query, parameters).fetchall()
            else:
                result = conn.execute(query).fetchall()
            return result

    def execute_many(self, query: str, parameters: list[tuple]) -> None:
        """
        Execute a query with multiple parameter sets.

        Args:
            query: SQL query to execute
            parameters: List of parameter tuples
        """
        with self.get_connection() as conn:
            conn.executemany(query, parameters)

    def initialize_database(self) -> None:
        """
        Initialize database with schema if it doesn't exist.

        This will create all tables, indexes, and views defined in schema.sql.
        """
        schema_path = Path(__file__).parent / "schema.sql"

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        with open(schema_path) as f:
            schema_sql = f.read()

        with self.get_connection() as conn:
            # Execute the entire schema
            conn.execute(schema_sql)

            # Verify key tables exist
            tables = conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
            ).fetchall()

            expected_tables = {
                "exercises",
                "programs",
                "program_workouts",
                "program_exercises",
                "workouts",
                "sets",
                "personal_records",
                "body_measurements",
                "settings",
            }

            existing_tables = {table[0] for table in tables}

            if not expected_tables.issubset(existing_tables):
                missing = expected_tables - existing_tables
                raise RuntimeError(f"Failed to create tables: {missing}")

    def database_exists(self) -> bool:
        """Check if the database file exists and is initialized."""
        if not self.db_path.exists():
            return False

        # Check if key tables exist
        try:
            with self.get_connection() as conn:
                result = conn.execute(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'exercises'"
                ).fetchone()
                return result[0] > 0
        except Exception:
            return False

    def get_table_count(self, table_name: str) -> int:
        """
        Get the number of rows in a table.

        Args:
            table_name: Name of the table

        Returns:
            Row count
        """
        result = self.execute(f"SELECT COUNT(*) FROM {table_name}")  # nosec B608  # table_name from schema
        return result[0][0] if result else 0

    def vacuum(self) -> None:
        """Optimize database file size."""
        with self.get_connection() as conn:
            conn.execute("VACUUM")

    def backup(self, backup_path: str) -> None:
        """
        Create a backup of the database.

        Args:
            backup_path: Path where backup should be created
        """
        backup_path_obj = Path(backup_path).expanduser()
        backup_path_obj.parent.mkdir(parents=True, exist_ok=True)

        with self.get_connection() as conn:
            conn.execute(f"EXPORT DATABASE '{backup_path_obj}' (FORMAT PARQUET)")

    def restore(self, backup_path: str) -> None:
        """
        Restore database from a backup.

        Args:
            backup_path: Path to backup directory
        """
        backup_path_obj = Path(backup_path).expanduser()

        if not backup_path_obj.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        with self.get_connection() as conn:
            conn.execute(f"IMPORT DATABASE '{backup_path_obj}'")

    def get_database_info(self) -> dict:
        """
        Get information about the database.

        Returns:
            Dictionary with database information
        """
        with self.get_connection() as conn:
            # Get all tables
            tables = conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main' ORDER BY table_name"
            ).fetchall()

            table_info = {}
            for table in tables:
                table_name = table[0]
                count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]  # nosec B608  # table_name from schema
                table_info[table_name] = count

            return {
                "database_path": str(self.db_path),
                "database_size_mb": self.db_path.stat().st_size / (1024 * 1024),
                "tables": table_info,
            }


# Global database instance
_db_instance: DatabaseManager | None = None


def get_db(db_path: str | None = None) -> DatabaseManager:
    """
    Get or create the global database instance.

    Args:
        db_path: Optional database path. If None, uses default.

    Returns:
        DatabaseManager instance
    """
    global _db_instance

    if _db_instance is None:
        _db_instance = DatabaseManager(db_path)

    return _db_instance


def reset_db_instance() -> None:
    """Reset the global database instance. Useful for testing."""
    global _db_instance
    _db_instance = None

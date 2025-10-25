"""Service for importing data into the LIFT database."""

import csv
import json
from pathlib import Path

from lift.core.database import DatabaseManager


class ImportService:
    """Service for importing workout data from various formats."""

    def __init__(self, db: DatabaseManager) -> None:
        """
        Initialize the import service.

        Args:
            db: Database manager instance
        """
        self.db = db

    def import_from_csv(self, table_name: str, file_path: str) -> int:
        """
        Import data from CSV file into a table.

        Args:
            table_name: Name of the table to import into
            file_path: Path to CSV file

        Returns:
            Number of rows imported

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If table doesn't exist or data is invalid
        """
        file_path_obj = Path(file_path).expanduser()

        if not file_path_obj.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        with self.db.get_connection() as conn:
            # Verify table exists
            tables = conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main' AND table_name = ?",
                (table_name,),
            ).fetchall()

            if not tables:
                raise ValueError(f"Table '{table_name}' does not exist")

            # Get column information
            columns_info = conn.execute(
                "SELECT column_name, data_type FROM information_schema.columns "
                f"WHERE table_name = '{table_name}' ORDER BY ordinal_position"
            ).fetchall()

            column_names = [col[0] for col in columns_info]

            # Read CSV file
            with open(file_path_obj, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                csv_headers = reader.fieldnames

                if not csv_headers:
                    raise ValueError("CSV file has no headers")

                # Validate headers match table columns (subset is OK)
                for header in csv_headers:
                    if header not in column_names:
                        raise ValueError(
                            f"CSV header '{header}' does not match any column in table '{table_name}'"
                        )

                # Prepare data for import
                rows_data = []
                for row in reader:
                    # Convert empty strings to None
                    processed_row = {}
                    for key, value in row.items():
                        if value == "" or value is None:
                            processed_row[key] = None
                        else:
                            processed_row[key] = value
                    rows_data.append(processed_row)

                if not rows_data:
                    return 0

                # Validate data
                if not self.validate_import_data(rows_data, table_name):
                    raise ValueError("Data validation failed")

                # Build INSERT query
                insert_columns = list(csv_headers)
                placeholders = ", ".join(["?" for _ in insert_columns])
                columns_str = ", ".join(insert_columns)

                insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

                # Insert data
                for row_dict in rows_data:
                    values = tuple(row_dict.get(col) for col in insert_columns)
                    conn.execute(insert_query, values)

                return len(rows_data)

    def import_from_json(self, file_path: str) -> dict[str, int]:
        """
        Import data from JSON file.

        Supports both single-table and full-database exports.

        Args:
            file_path: Path to JSON file

        Returns:
            Dictionary mapping table names to imported row counts

        Raises:
            FileNotFoundError: If JSON file doesn't exist
            ValueError: If JSON format is invalid
        """
        file_path_obj = Path(file_path).expanduser()

        if not file_path_obj.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        with open(file_path_obj, encoding="utf-8") as f:
            data = json.load(f)

        import_summary = {}

        # Check if this is a full database export or single table
        if isinstance(data, dict) and "tables" in data:
            # Full database export
            for table_name, table_data in data["tables"].items():
                if not table_data:
                    import_summary[table_name] = 0
                    continue

                if not self.validate_import_data(table_data, table_name):
                    raise ValueError(f"Data validation failed for table '{table_name}'")

                count = self._import_table_data(table_name, table_data)
                import_summary[table_name] = count

        elif isinstance(data, list):
            # Single table data - need to detect which table
            # This is tricky without metadata, so we'll require table name separately
            raise ValueError(
                "Single table JSON import requires using import_from_csv or "
                "specifying table name explicitly"
            )
        else:
            raise ValueError("Invalid JSON format")

        return import_summary

    def _import_table_data(self, table_name: str, data: list[dict]) -> int:
        """
        Import data into a specific table.

        Args:
            table_name: Name of the table
            data: List of row dictionaries

        Returns:
            Number of rows imported
        """
        if not data:
            return 0

        with self.db.get_connection() as conn:
            # Get all columns in the data
            all_columns = set()
            for row in data:
                all_columns.update(row.keys())

            insert_columns = list(all_columns)
            placeholders = ", ".join(["?" for _ in insert_columns])
            columns_str = ", ".join(insert_columns)

            insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

            # Insert each row
            for row_dict in data:
                values = tuple(row_dict.get(col) for col in insert_columns)
                conn.execute(insert_query, values)

        return len(data)

    def validate_import_data(self, data: list[dict], table_name: str) -> bool:
        """
        Validate data before importing.

        Args:
            data: List of row dictionaries to validate
            table_name: Target table name

        Returns:
            True if validation passes, False otherwise
        """
        if not data:
            return True

        try:
            with self.db.get_connection() as conn:
                # Verify table exists
                tables = conn.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'main' AND table_name = ?",
                    (table_name,),
                ).fetchall()

                if not tables:
                    return False

                # Get column information
                columns_info = conn.execute(
                    "SELECT column_name, data_type, is_nullable FROM information_schema.columns "
                    f"WHERE table_name = '{table_name}'"
                ).fetchall()

                valid_columns = {
                    col[0]: {"type": col[1], "nullable": col[2]} for col in columns_info
                }

                # Validate each row
                for row in data:
                    # Check that all columns in the row exist in the table
                    for column in row.keys():
                        if column not in valid_columns:
                            # Allow extra columns (they'll be ignored)
                            pass

                    # Check required columns (NOT NULL) have values
                    for col_name, col_info in valid_columns.items():
                        if col_info["nullable"] == "NO" and col_name not in row:
                            # Check if column has a default value or is auto-increment
                            if col_name.lower() in ["id", "created_at", "updated_at"]:
                                continue  # These usually have defaults
                            # Missing required column
                            return False

                return True

        except Exception:
            return False

    def import_exercises_from_json(self, file_path: str) -> int:
        """
        Specialized import handler for exercise data.

        Args:
            file_path: Path to JSON file containing exercises

        Returns:
            Number of exercises imported

        Raises:
            FileNotFoundError: If JSON file doesn't exist
            ValueError: If data format is invalid
        """
        file_path_obj = Path(file_path).expanduser()

        if not file_path_obj.exists():
            raise FileNotFoundError(f"Exercise file not found: {file_path}")

        with open(file_path_obj, encoding="utf-8") as f:
            exercises = json.load(f)

        if not isinstance(exercises, list):
            raise ValueError("Exercise JSON must be a list of exercise objects")

        # Validate required fields
        required_fields = ["name", "category", "primary_muscle", "equipment"]
        for exercise in exercises:
            for field in required_fields:
                if field not in exercise:
                    raise ValueError(f"Exercise missing required field: {field}")

        # Validate data
        if not self.validate_import_data(exercises, "exercises"):
            raise ValueError("Exercise data validation failed")

        with self.db.get_connection() as conn:
            imported = 0
            for exercise in exercises:
                # Handle secondary_muscles as JSON array
                if "secondary_muscles" in exercise and isinstance(
                    exercise["secondary_muscles"], list
                ):
                    exercise["secondary_muscles"] = json.dumps(exercise["secondary_muscles"])

                # Build INSERT query
                columns = list(exercise.keys())
                placeholders = ", ".join(["?" for _ in columns])
                columns_str = ", ".join(columns)

                insert_query = (
                    f"INSERT OR IGNORE INTO exercises ({columns_str}) VALUES ({placeholders})"
                )

                values = tuple(exercise.get(col) for col in columns)
                conn.execute(insert_query, values)
                imported += 1

        return imported

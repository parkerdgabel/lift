"""Service for exporting data from the LIFT database."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from lift.core.database import DatabaseManager


class ExportService:
    """Service for exporting workout data in various formats."""

    def __init__(self, db: DatabaseManager) -> None:
        """
        Initialize the export service.

        Args:
            db: Database manager instance
        """
        self.db = db

    def export_to_csv(self, table_name: str, output_path: str) -> None:
        """
        Export a specific table to CSV format.

        Args:
            table_name: Name of the table to export
            output_path: Path where CSV file should be saved

        Raises:
            ValueError: If table doesn't exist
            IOError: If file cannot be written
        """
        output_path_obj = Path(output_path).expanduser()
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        with self.db.get_connection() as conn:
            # Verify table exists
            tables = conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main' AND table_name = ?",
                (table_name,),
            ).fetchall()

            if not tables:
                raise ValueError(f"Table '{table_name}' does not exist")

            # Get all data from the table
            result = conn.execute(f"SELECT * FROM {table_name}").fetchall()

            if not result:
                # Empty table, just create headers
                columns = conn.execute(
                    f"SELECT column_name FROM information_schema.columns "
                    f"WHERE table_name = '{table_name}' ORDER BY ordinal_position"
                ).fetchall()
                headers = [col[0] for col in columns]

                with open(output_path_obj, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                return

            # Get column names
            headers = list(result[0].keys()) if hasattr(result[0], "keys") else []
            if not headers:
                # Fallback: get from information_schema
                columns = conn.execute(
                    f"SELECT column_name FROM information_schema.columns "
                    f"WHERE table_name = '{table_name}' ORDER BY ordinal_position"
                ).fetchall()
                headers = [col[0] for col in columns]

            # Write to CSV
            with open(output_path_obj, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

                for row in result:
                    # Convert row to list, handling various types
                    if hasattr(row, "_asdict"):
                        row_data = list(row._asdict().values())
                    else:
                        row_data = list(row)

                    # Convert timestamps to ISO format
                    processed_row = []
                    for value in row_data:
                        if isinstance(value, datetime):
                            processed_row.append(value.isoformat())
                        elif value is None:
                            processed_row.append("")
                        else:
                            processed_row.append(str(value))

                    writer.writerow(processed_row)

    def export_all_to_csv(self, output_dir: str) -> dict[str, int]:
        """
        Export all tables to separate CSV files.

        Args:
            output_dir: Directory where CSV files should be saved

        Returns:
            Dictionary mapping table names to row counts
        """
        output_dir_obj = Path(output_dir).expanduser()
        output_dir_obj.mkdir(parents=True, exist_ok=True)

        with self.db.get_connection() as conn:
            # Get all table names
            tables = conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main' AND table_type = 'BASE TABLE' "
                "ORDER BY table_name"
            ).fetchall()

        export_summary = {}

        for table_tuple in tables:
            table_name = table_tuple[0]
            output_path = output_dir_obj / f"{table_name}.csv"
            self.export_to_csv(table_name, str(output_path))

            # Get row count
            count = self.db.get_table_count(table_name)
            export_summary[table_name] = count

        return export_summary

    def export_to_json(self, table_name: str, output_path: str) -> None:
        """
        Export a specific table to JSON format.

        Args:
            table_name: Name of the table to export
            output_path: Path where JSON file should be saved

        Raises:
            ValueError: If table doesn't exist
            IOError: If file cannot be written
        """
        output_path_obj = Path(output_path).expanduser()
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        with self.db.get_connection() as conn:
            # Verify table exists
            tables = conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main' AND table_name = ?",
                (table_name,),
            ).fetchall()

            if not tables:
                raise ValueError(f"Table '{table_name}' does not exist")

            # Get all data from the table
            result = conn.execute(f"SELECT * FROM {table_name}").fetchall()

            # Convert to list of dictionaries
            data = []
            for row in result:
                if hasattr(row, "_asdict"):
                    row_dict = dict(row._asdict())
                else:
                    # Fallback: get column names
                    columns = conn.execute(
                        f"SELECT column_name FROM information_schema.columns "
                        f"WHERE table_name = '{table_name}' ORDER BY ordinal_position"
                    ).fetchall()
                    headers = [col[0] for col in columns]
                    row_dict = dict(zip(headers, row))

                # Convert timestamps to ISO format
                processed_dict = {}
                for key, value in row_dict.items():
                    if isinstance(value, datetime):
                        processed_dict[key] = value.isoformat()
                    else:
                        processed_dict[key] = value

                data.append(processed_dict)

        # Write to JSON
        with open(output_path_obj, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def export_all_to_json(self, output_path: str) -> dict[str, int]:
        """
        Export entire database to a single JSON file.

        Args:
            output_path: Path where JSON file should be saved

        Returns:
            Dictionary mapping table names to row counts
        """
        output_path_obj = Path(output_path).expanduser()
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        with self.db.get_connection() as conn:
            # Get all table names
            tables = conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main' AND table_type = 'BASE TABLE' "
                "ORDER BY table_name"
            ).fetchall()

            database_export = {
                "export_date": datetime.now().isoformat(),
                "tables": {},
            }

            export_summary = {}

            for table_tuple in tables:
                table_name = table_tuple[0]

                # Get all data from the table
                result = conn.execute(f"SELECT * FROM {table_name}").fetchall()

                # Convert to list of dictionaries
                data = []
                for row in result:
                    if hasattr(row, "_asdict"):
                        row_dict = dict(row._asdict())
                    else:
                        # Fallback: get column names
                        columns = conn.execute(
                            f"SELECT column_name FROM information_schema.columns "
                            f"WHERE table_name = '{table_name}' ORDER BY ordinal_position"
                        ).fetchall()
                        headers = [col[0] for col in columns]
                        row_dict = dict(zip(headers, row))

                    # Convert timestamps to ISO format
                    processed_dict = {}
                    for key, value in row_dict.items():
                        if isinstance(value, datetime):
                            processed_dict[key] = value.isoformat()
                        else:
                            processed_dict[key] = value

                    data.append(processed_dict)

                database_export["tables"][table_name] = data
                export_summary[table_name] = len(data)

        # Write to JSON
        with open(output_path_obj, "w", encoding="utf-8") as f:
            json.dump(database_export, f, indent=2, ensure_ascii=False)

        return export_summary

    def export_workout_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        output_path: str = "workout_history.json",
    ) -> int:
        """
        Export workout data for a specific date range.

        Args:
            start_date: Start date for export (inclusive). None means no start limit.
            end_date: End date for export (inclusive). None means no end limit.
            output_path: Path where JSON file should be saved

        Returns:
            Number of workouts exported
        """
        output_path_obj = Path(output_path).expanduser()
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Build query with date filters
        where_clauses = []
        params = []

        if start_date:
            where_clauses.append("w.date >= ?")
            params.append(start_date)

        if end_date:
            where_clauses.append("w.date <= ?")
            params.append(end_date)

        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        query = f"""
        SELECT
            w.*,
            pw.name as program_workout_name
        FROM workouts w
        LEFT JOIN program_workouts pw ON w.program_workout_id = pw.id
        {where_clause}
        ORDER BY w.date DESC
        """

        with self.db.get_connection() as conn:
            workouts = conn.execute(query, params if params else None).fetchall()

            workout_data = []
            for workout in workouts:
                workout_dict = dict(workout._asdict()) if hasattr(workout, "_asdict") else {}

                # Get sets for this workout
                sets = conn.execute(
                    """
                    SELECT
                        s.*,
                        e.name as exercise_name,
                        e.primary_muscle
                    FROM sets s
                    JOIN exercises e ON s.exercise_id = e.id
                    WHERE s.workout_id = ?
                    ORDER BY s.set_number
                    """,
                    (workout_dict.get("id", workout[0]),),
                ).fetchall()

                # Convert workout data
                processed_workout = {}
                for key, value in workout_dict.items():
                    if isinstance(value, datetime):
                        processed_workout[key] = value.isoformat()
                    else:
                        processed_workout[key] = value

                # Convert sets data
                processed_sets = []
                for set_row in sets:
                    set_dict = dict(set_row._asdict()) if hasattr(set_row, "_asdict") else {}
                    processed_set = {}
                    for key, value in set_dict.items():
                        if isinstance(value, datetime):
                            processed_set[key] = value.isoformat()
                        else:
                            processed_set[key] = value
                    processed_sets.append(processed_set)

                processed_workout["sets"] = processed_sets
                workout_data.append(processed_workout)

        export_data = {
            "export_date": datetime.now().isoformat(),
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "workout_count": len(workout_data),
            "workouts": workout_data,
        }

        # Write to JSON
        with open(output_path_obj, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return len(workout_data)

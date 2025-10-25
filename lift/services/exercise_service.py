"""Service layer for exercise management."""

import json
from pathlib import Path

from lift.core.database import DatabaseManager, get_db
from lift.core.models import Exercise, ExerciseCreate


class ExerciseService:
    """Service for managing exercises."""

    def __init__(self, db: DatabaseManager | None = None) -> None:
        """
        Initialize the exercise service.

        Args:
            db: DatabaseManager instance. If None, uses the global instance.
        """
        self.db = db or get_db()

    def get_all(
        self,
        category: str | None = None,
        muscle: str | None = None,
        equipment: str | None = None,
    ) -> list[Exercise]:
        """
        Get all exercises with optional filters.

        Args:
            category: Filter by category (Push, Pull, Legs, Core)
            muscle: Filter by primary muscle
            equipment: Filter by equipment type

        Returns:
            List of Exercise objects
        """
        query = "SELECT * FROM exercises WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if muscle:
            query += " AND primary_muscle = ?"
            params.append(muscle)

        if equipment:
            query += " AND equipment = ?"
            params.append(equipment)

        query += " ORDER BY name"

        with self.db.get_connection() as conn:
            results = conn.execute(query, params).fetchall()
            return [self._row_to_exercise(row) for row in results]

    def search(self, query: str) -> list[Exercise]:
        """
        Search exercises by name.

        Args:
            query: Search string (case-insensitive)

        Returns:
            List of matching Exercise objects
        """
        sql = """
            SELECT * FROM exercises
            WHERE LOWER(name) LIKE LOWER(?)
            ORDER BY name
        """
        search_param = f"%{query}%"

        with self.db.get_connection() as conn:
            results = conn.execute(sql, [search_param]).fetchall()
            return [self._row_to_exercise(row) for row in results]

    def get_by_id(self, exercise_id: int) -> Exercise | None:
        """
        Get an exercise by ID.

        Args:
            exercise_id: Exercise ID

        Returns:
            Exercise object or None if not found
        """
        sql = "SELECT * FROM exercises WHERE id = ?"

        with self.db.get_connection() as conn:
            result = conn.execute(sql, [exercise_id]).fetchone()
            return self._row_to_exercise(result) if result else None

    def get_by_name(self, name: str) -> Exercise | None:
        """
        Get an exercise by exact name (case-insensitive).

        Args:
            name: Exercise name

        Returns:
            Exercise object or None if not found
        """
        sql = "SELECT * FROM exercises WHERE LOWER(name) = LOWER(?)"

        with self.db.get_connection() as conn:
            result = conn.execute(sql, [name]).fetchone()
            return self._row_to_exercise(result) if result else None

    def create(self, exercise: ExerciseCreate) -> Exercise:
        """
        Create a new exercise.

        Args:
            exercise: ExerciseCreate object

        Returns:
            Created Exercise object

        Raises:
            ValueError: If an exercise with the same name already exists
        """
        # Check if exercise already exists
        existing = self.get_by_name(exercise.name)
        if existing:
            raise ValueError(f"Exercise '{exercise.name}' already exists")

        # Convert secondary_muscles list to JSON string
        secondary_muscles_json = json.dumps([muscle.value for muscle in exercise.secondary_muscles])

        sql = """
            INSERT INTO exercises (
                name, category, primary_muscle, secondary_muscles,
                equipment, movement_type, is_custom, instructions, video_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            exercise.name,
            exercise.category.value,
            exercise.primary_muscle.value,
            secondary_muscles_json,
            exercise.equipment.value,
            exercise.movement_type.value,
            exercise.is_custom,
            exercise.instructions,
            exercise.video_url,
        )

        with self.db.get_connection() as conn:
            conn.execute(sql, params)

        # Retrieve the created exercise
        created = self.get_by_name(exercise.name)
        if not created:
            raise RuntimeError("Failed to create exercise")

        return created

    def delete(self, exercise_id: int) -> bool:
        """
        Delete an exercise by ID.

        Args:
            exercise_id: Exercise ID

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If trying to delete a non-custom exercise
        """
        # Check if exercise exists and is custom
        exercise = self.get_by_id(exercise_id)
        if not exercise:
            return False

        if not exercise.is_custom:
            raise ValueError(
                "Cannot delete built-in exercises. Only custom exercises can be deleted."
            )

        sql = "DELETE FROM exercises WHERE id = ?"

        with self.db.get_connection() as conn:
            conn.execute(sql, [exercise_id])

        return True

    def load_seed_exercises(self, force: bool = False) -> int:
        """
        Load seed exercises from JSON file.

        Args:
            force: If True, reload even if exercises already exist

        Returns:
            Number of exercises loaded

        Raises:
            FileNotFoundError: If exercises.json not found
        """
        # Check if exercises already exist
        if not force:
            existing_count = self.db.get_table_count("exercises")
            if existing_count > 0:
                return 0  # Skip loading if exercises already exist

        # Load exercises from JSON file
        json_path = Path(__file__).parent.parent / "data" / "exercises.json"

        if not json_path.exists():
            raise FileNotFoundError(f"Exercises data file not found: {json_path}")

        with open(json_path) as f:
            exercises_data = json.load(f)

        loaded_count = 0
        for exercise_data in exercises_data:
            try:
                # Create ExerciseCreate object from JSON data
                exercise = ExerciseCreate(**exercise_data)

                # Skip if already exists
                if self.get_by_name(exercise.name):
                    continue

                self.create(exercise)
                loaded_count += 1
            except Exception as e:
                # Log error but continue loading other exercises
                print(f"Warning: Failed to load exercise '{exercise_data.get('name')}': {e}")
                continue

        return loaded_count

    def _row_to_exercise(self, row: tuple) -> Exercise:
        """
        Convert a database row tuple to an Exercise object.

        Args:
            row: Database row tuple

        Returns:
            Exercise object
        """
        # Parse secondary_muscles from JSON string
        secondary_muscles = []
        if row[4]:  # secondary_muscles column (index 4)
            try:
                secondary_muscles = json.loads(row[4])
            except json.JSONDecodeError:
                secondary_muscles = []

        return Exercise(
            id=row[0],  # id
            name=row[1],  # name
            category=row[2],  # category
            primary_muscle=row[3],  # primary_muscle
            secondary_muscles=secondary_muscles,  # secondary_muscles (parsed from JSON)
            equipment=row[5],  # equipment
            movement_type=row[6] if row[6] else "Compound",  # movement_type
            is_custom=bool(row[7]),  # is_custom
            instructions=row[8],  # instructions
            video_url=row[9],  # video_url
            created_at=row[10],  # created_at
        )

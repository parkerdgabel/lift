"""Program management service for creating and managing training programs."""

import json
from pathlib import Path

from lift.core.database import DatabaseManager, get_db
from lift.core.models import (
    Program,
    ProgramCreate,
    ProgramExercise,
    ProgramExerciseCreate,
    ProgramWorkout,
    ProgramWorkoutCreate,
)


class ProgramService:
    """Service for managing training programs, workouts, and exercises."""

    def __init__(self, db: DatabaseManager | None = None) -> None:
        """
        Initialize program service.

        Args:
            db: Database manager instance. If None, uses global instance.
        """
        self.db = db or get_db()

    def create_program(self, program: ProgramCreate) -> Program:
        """
        Create a new training program.

        Args:
            program: Program data to create

        Returns:
            Created program with ID

        Raises:
            ValueError: If program name already exists
        """
        # Check if program with this name exists
        existing = self.get_program_by_name(program.name)
        if existing:
            raise ValueError(f"Program with name '{program.name}' already exists")

        query = """
            INSERT INTO programs (name, description, split_type, days_per_week, duration_weeks)
            VALUES (?, ?, ?, ?, ?)
            RETURNING id, name, description, split_type, days_per_week, duration_weeks,
                      is_active, created_at, updated_at
        """

        with self.db.get_connection() as conn:
            result = conn.execute(
                query,
                (
                    program.name,
                    program.description,
                    program.split_type.value,
                    program.days_per_week,
                    program.duration_weeks,
                ),
            ).fetchone()

            if not result:
                raise RuntimeError("Failed to create program - no result returned")

            return Program(
                id=result[0],
                name=result[1],
                description=result[2],
                split_type=result[3],
                days_per_week=result[4],
                duration_weeks=result[5],
                is_active=result[6],
                created_at=result[7],
                updated_at=result[8],
            )

    def get_all_programs(self) -> list[Program]:
        """
        Get all training programs.

        Returns:
            List of all programs
        """
        query = """
            SELECT id, name, description, split_type, days_per_week, duration_weeks,
                   is_active, created_at, updated_at
            FROM programs
            ORDER BY is_active DESC, created_at DESC
        """

        with self.db.get_connection() as conn:
            results = conn.execute(query).fetchall()

            return [
                Program(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    split_type=row[3],
                    days_per_week=row[4],
                    duration_weeks=row[5],
                    is_active=row[6],
                    created_at=row[7],
                    updated_at=row[8],
                )
                for row in results
            ]

    def get_program(self, id: int) -> Program | None:
        """
        Get a program by ID.

        Args:
            id: Program ID

        Returns:
            Program if found, None otherwise
        """
        query = """
            SELECT id, name, description, split_type, days_per_week, duration_weeks,
                   is_active, created_at, updated_at
            FROM programs
            WHERE id = ?
        """

        with self.db.get_connection() as conn:
            result = conn.execute(query, (id,)).fetchone()

            if not result:
                return None

            return Program(
                id=result[0],
                name=result[1],
                description=result[2],
                split_type=result[3],
                days_per_week=result[4],
                duration_weeks=result[5],
                is_active=result[6],
                created_at=result[7],
                updated_at=result[8],
            )

    def get_program_by_name(self, name: str) -> Program | None:
        """
        Get a program by name.

        Args:
            name: Program name

        Returns:
            Program if found, None otherwise
        """
        query = """
            SELECT id, name, description, split_type, days_per_week, duration_weeks,
                   is_active, created_at, updated_at
            FROM programs
            WHERE name = ?
        """

        with self.db.get_connection() as conn:
            result = conn.execute(query, (name,)).fetchone()

            if not result:
                return None

            return Program(
                id=result[0],
                name=result[1],
                description=result[2],
                split_type=result[3],
                days_per_week=result[4],
                duration_weeks=result[5],
                is_active=result[6],
                created_at=result[7],
                updated_at=result[8],
            )

    def update_program(self, id: int, updates: dict) -> Program:
        """
        Update a program.

        Args:
            id: Program ID
            updates: Dictionary of fields to update

        Returns:
            Updated program

        Raises:
            ValueError: If program not found
        """
        program = self.get_program(id)
        if not program:
            raise ValueError(f"Program with ID {id} not found")

        # Build dynamic update query
        allowed_fields = {
            "name",
            "description",
            "split_type",
            "days_per_week",
            "duration_weeks",
        }
        update_fields = {k: v for k, v in updates.items() if k in allowed_fields}

        if not update_fields:
            return program

        set_clause = ", ".join(f"{k} = ?" for k in update_fields)
        query = f"""
            UPDATE programs
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            RETURNING id, name, description, split_type, days_per_week, duration_weeks,
                      is_active, created_at, updated_at
        """  # nosec B608  # set_clause built from validated update_fields keys

        values = list(update_fields.values()) + [id]

        with self.db.get_connection() as conn:
            result = conn.execute(query, values).fetchone()

            if not result:
                raise RuntimeError(f"Failed to update program {id} - no result returned")

            return Program(
                id=result[0],
                name=result[1],
                description=result[2],
                split_type=result[3],
                days_per_week=result[4],
                duration_weeks=result[5],
                is_active=result[6],
                created_at=result[7],
                updated_at=result[8],
            )

    def delete_program(self, id: int) -> bool:
        """
        Delete a program (cascades to workouts and exercises).

        Args:
            id: Program ID

        Returns:
            True if deleted, False if not found
        """
        query = "DELETE FROM programs WHERE id = ?"

        with self.db.get_connection() as conn:
            result = conn.execute(query, (id,))
            return result.fetchone() is not None

    def activate_program(self, id: int) -> Program:
        """
        Activate a program (deactivates all others).

        Args:
            id: Program ID to activate

        Returns:
            Activated program

        Raises:
            ValueError: If program not found
        """
        program = self.get_program(id)
        if not program:
            raise ValueError(f"Program with ID {id} not found")

        with self.db.get_connection() as conn:
            # Deactivate all programs
            conn.execute("UPDATE programs SET is_active = FALSE")

            # Activate the specified program
            # Note: DuckDB has issues with RETURNING clause when foreign keys reference the row
            conn.execute(
                """
                UPDATE programs
                SET is_active = TRUE, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (id,),
            )

            # Fetch the updated program
            result = conn.execute(
                """
                SELECT id, name, description, split_type, days_per_week, duration_weeks,
                       is_active, created_at, updated_at
                FROM programs
                WHERE id = ?
                """,
                (id,),
            ).fetchone()

            if not result:
                raise RuntimeError(f"Failed to activate program {id} - no result returned")

            return Program(
                id=result[0],
                name=result[1],
                description=result[2],
                split_type=result[3],
                days_per_week=result[4],
                duration_weeks=result[5],
                is_active=result[6],
                created_at=result[7],
                updated_at=result[8],
            )

    def get_active_program(self) -> Program | None:
        """
        Get the currently active program.

        Returns:
            Active program if found, None otherwise
        """
        query = """
            SELECT id, name, description, split_type, days_per_week, duration_weeks,
                   is_active, created_at, updated_at
            FROM programs
            WHERE is_active = TRUE
            LIMIT 1
        """

        with self.db.get_connection() as conn:
            result = conn.execute(query).fetchone()

            if not result:
                return None

            return Program(
                id=result[0],
                name=result[1],
                description=result[2],
                split_type=result[3],
                days_per_week=result[4],
                duration_weeks=result[5],
                is_active=result[6],
                created_at=result[7],
                updated_at=result[8],
            )

    def get_next_workout_in_program(self, program_id: int) -> ProgramWorkout | None:
        """
        Get the next workout to perform in a program based on last workout done.

        Args:
            program_id: Program ID

        Returns:
            Next workout in rotation, or None if no workouts in program

        Logic:
            1. Find last workout from this program
            2. Get next workout by day_number order
            3. Cycle back to first if at the end
            4. Return first workout if none completed yet
        """
        # Query last workout done from this program
        query = """
            SELECT pw.id, pw.day_number
            FROM workouts w
            JOIN program_workouts pw ON w.program_workout_id = pw.id
            WHERE pw.program_id = ?
            ORDER BY w.date DESC
            LIMIT 1
        """

        with self.db.get_connection() as conn:
            last_result = conn.execute(query, (program_id,)).fetchone()

            # Get all workouts in program ordered by day_number
            workouts = self.get_program_workouts(program_id)

            if not workouts:
                return None

            if not last_result:
                # No previous workout, return first
                return workouts[0]

            last_workout_id = last_result[0]

            # Find next workout in sequence
            for i, workout in enumerate(workouts):
                if workout.id == last_workout_id:
                    # Return next, or cycle to first
                    return workouts[(i + 1) % len(workouts)]

            # Fallback to first workout
            return workouts[0]

    def get_workout_position_in_program(self, workout_id: int, program_id: int) -> tuple[int, int]:
        """
        Get position of a workout within its program.

        Args:
            workout_id: Program workout ID
            program_id: Program ID

        Returns:
            Tuple of (position, total) e.g., (3, 6) means "Day 3 of 6"
        """
        workouts = self.get_program_workouts(program_id)

        for i, workout in enumerate(workouts, 1):
            if workout.id == workout_id:
                return (i, len(workouts))

        return (1, len(workouts))

    def add_workout_to_program(
        self, program_id: int, workout: ProgramWorkoutCreate
    ) -> ProgramWorkout:
        """
        Add a workout to a program.

        Args:
            program_id: Program ID
            workout: Workout data to create

        Returns:
            Created workout

        Raises:
            ValueError: If program not found
        """
        program = self.get_program(program_id)
        if not program:
            raise ValueError(f"Program with ID {program_id} not found")

        query = """
            INSERT INTO program_workouts (program_id, name, day_number, description, estimated_duration_minutes)
            VALUES (?, ?, ?, ?, ?)
            RETURNING id, program_id, name, day_number, description, estimated_duration_minutes
        """

        with self.db.get_connection() as conn:
            result = conn.execute(
                query,
                (
                    program_id,
                    workout.name,
                    workout.day_number,
                    workout.description,
                    workout.estimated_duration_minutes,
                ),
            ).fetchone()

            if not result:
                raise RuntimeError(
                    f"Failed to add workout to program {program_id} - no result returned"
                )

            return ProgramWorkout(
                id=result[0],
                program_id=result[1],
                name=result[2],
                day_number=result[3],
                description=result[4],
                estimated_duration_minutes=result[5],
            )

    def add_exercise_to_workout(
        self, workout_id: int, exercise: ProgramExerciseCreate
    ) -> ProgramExercise:
        """
        Add an exercise to a workout.

        Args:
            workout_id: Workout ID
            exercise: Exercise data to create

        Returns:
            Created exercise

        Raises:
            ValueError: If workout not found or exercise_id invalid
        """
        # Verify workout exists
        workout_query = "SELECT id FROM program_workouts WHERE id = ?"
        with self.db.get_connection() as conn:
            workout_result = conn.execute(workout_query, (workout_id,)).fetchone()
            if not workout_result:
                raise ValueError(f"Workout with ID {workout_id} not found")

            # Verify exercise exists
            exercise_query = "SELECT id FROM exercises WHERE id = ?"
            exercise_result = conn.execute(exercise_query, (exercise.exercise_id,)).fetchone()
            if not exercise_result:
                raise ValueError(f"Exercise with ID {exercise.exercise_id} not found")

            # Insert program exercise
            query = """
                INSERT INTO program_exercises (
                    program_workout_id, exercise_id, order_number, target_sets,
                    target_reps_min, target_reps_max, target_rpe, rest_seconds,
                    tempo, notes, is_superset, superset_group
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id, program_workout_id, exercise_id, order_number, target_sets,
                          target_reps_min, target_reps_max, target_rpe, rest_seconds,
                          tempo, notes, is_superset, superset_group
            """

            result = conn.execute(
                query,
                (
                    workout_id,
                    exercise.exercise_id,
                    exercise.order_number,
                    exercise.target_sets,
                    exercise.target_reps_min,
                    exercise.target_reps_max,
                    exercise.target_rpe,
                    exercise.rest_seconds,
                    exercise.tempo,
                    exercise.notes,
                    exercise.is_superset,
                    exercise.superset_group,
                ),
            ).fetchone()

            if not result:
                raise RuntimeError(
                    f"Failed to add exercise to workout {workout_id} - no result returned"
                )

            return ProgramExercise(
                id=result[0],
                program_workout_id=result[1],
                exercise_id=result[2],
                order_number=result[3],
                target_sets=result[4],
                target_reps_min=result[5],
                target_reps_max=result[6],
                target_rpe=result[7],
                rest_seconds=result[8],
                tempo=result[9],
                notes=result[10],
                is_superset=result[11],
                superset_group=result[12],
            )

    def get_program_workouts(self, program_id: int) -> list[ProgramWorkout]:
        """
        Get all workouts for a program.

        Args:
            program_id: Program ID

        Returns:
            List of workouts
        """
        query = """
            SELECT id, program_id, name, day_number, description, estimated_duration_minutes
            FROM program_workouts
            WHERE program_id = ?
            ORDER BY day_number, id
        """

        with self.db.get_connection() as conn:
            results = conn.execute(query, (program_id,)).fetchall()

            return [
                ProgramWorkout(
                    id=row[0],
                    program_id=row[1],
                    name=row[2],
                    day_number=row[3],
                    description=row[4],
                    estimated_duration_minutes=row[5],
                )
                for row in results
            ]

    def get_workout_exercises(self, workout_id: int) -> list[dict]:
        """
        Get all exercises for a workout with exercise details.

        Args:
            workout_id: Workout ID

        Returns:
            List of dictionaries containing program exercise and exercise details
        """
        query = """
            SELECT
                pe.id, pe.program_workout_id, pe.exercise_id, pe.order_number,
                pe.target_sets, pe.target_reps_min, pe.target_reps_max, pe.target_rpe,
                pe.rest_seconds, pe.tempo, pe.notes, pe.is_superset, pe.superset_group,
                e.name, e.category, e.primary_muscle, e.equipment
            FROM program_exercises pe
            JOIN exercises e ON pe.exercise_id = e.id
            WHERE pe.program_workout_id = ?
            ORDER BY pe.order_number
        """

        with self.db.get_connection() as conn:
            results = conn.execute(query, (workout_id,)).fetchall()

            return [
                {
                    "program_exercise": ProgramExercise(
                        id=row[0],
                        program_workout_id=row[1],
                        exercise_id=row[2],
                        order_number=row[3],
                        target_sets=row[4],
                        target_reps_min=row[5],
                        target_reps_max=row[6],
                        target_rpe=row[7],
                        rest_seconds=row[8],
                        tempo=row[9],
                        notes=row[10],
                        is_superset=row[11],
                        superset_group=row[12],
                    ),
                    "exercise_name": row[13],
                    "exercise_category": row[14],
                    "exercise_primary_muscle": row[15],
                    "exercise_equipment": row[16],
                }
                for row in results
            ]

    def clone_program(self, id: int, new_name: str) -> Program:
        """
        Clone an existing program with all its workouts and exercises.

        Args:
            id: Program ID to clone
            new_name: Name for the new program

        Returns:
            Cloned program

        Raises:
            ValueError: If program not found or new name already exists
        """
        # Get original program
        original = self.get_program(id)
        if not original:
            raise ValueError(f"Program with ID {id} not found")

        # Check if new name exists
        if self.get_program_by_name(new_name):
            raise ValueError(f"Program with name '{new_name}' already exists")

        with self.db.get_connection() as conn:
            # Create new program
            new_program_result = conn.execute(
                """
                INSERT INTO programs (name, description, split_type, days_per_week, duration_weeks)
                VALUES (?, ?, ?, ?, ?)
                RETURNING id, name, description, split_type, days_per_week, duration_weeks,
                          is_active, created_at, updated_at
            """,
                (
                    new_name,
                    original.description,
                    original.split_type.value,
                    original.days_per_week,
                    original.duration_weeks,
                ),
            ).fetchone()

            if not new_program_result:
                raise RuntimeError(f"Failed to clone program {id} - no result returned")

            new_program_id = new_program_result[0]

            # Get original workouts
            workouts = self.get_program_workouts(id)

            # Clone each workout and its exercises
            for workout in workouts:
                # Create new workout
                new_workout_result = conn.execute(
                    """
                    INSERT INTO program_workouts (program_id, name, day_number, description, estimated_duration_minutes)
                    VALUES (?, ?, ?, ?, ?)
                    RETURNING id
                """,
                    (
                        new_program_id,
                        workout.name,
                        workout.day_number,
                        workout.description,
                        workout.estimated_duration_minutes,
                    ),
                ).fetchone()

                if not new_workout_result:
                    raise RuntimeError(f"Failed to clone workout {workout.id} - no result returned")

                new_workout_id = new_workout_result[0]

                # Get original exercises
                exercises = self.get_workout_exercises(workout.id)

                # Clone each exercise
                for exercise_data in exercises:
                    pe = exercise_data["program_exercise"]
                    conn.execute(
                        """
                        INSERT INTO program_exercises (
                            program_workout_id, exercise_id, order_number, target_sets,
                            target_reps_min, target_reps_max, target_rpe, rest_seconds,
                            tempo, notes, is_superset, superset_group
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            new_workout_id,
                            pe.exercise_id,
                            pe.order_number,
                            pe.target_sets,
                            pe.target_reps_min,
                            pe.target_reps_max,
                            pe.target_rpe,
                            pe.rest_seconds,
                            pe.tempo,
                            pe.notes,
                            pe.is_superset,
                            pe.superset_group,
                        ),
                    )

            return Program(
                id=new_program_result[0],
                name=new_program_result[1],
                description=new_program_result[2],
                split_type=new_program_result[3],
                days_per_week=new_program_result[4],
                duration_weeks=new_program_result[5],
                is_active=new_program_result[6],
                created_at=new_program_result[7],
                updated_at=new_program_result[8],
            )

    def load_seed_programs(self, programs_file: str | None = None) -> int:
        """
        Load sample programs from JSON file.

        Args:
            programs_file: Path to programs JSON file. If None, uses default.

        Returns:
            Number of programs loaded

        Raises:
            FileNotFoundError: If programs file not found
            ValueError: If JSON is invalid
        """
        if programs_file is None:
            programs_file = str(Path(__file__).parent.parent / "data" / "programs.json")

        programs_path = Path(programs_file)
        if not programs_path.exists():
            raise FileNotFoundError(f"Programs file not found: {programs_file}")

        with open(programs_path) as f:
            data = json.load(f)

        programs_loaded = 0

        for program_data in data.get("programs", []):
            # Check if program already exists
            existing = self.get_program_by_name(program_data["name"])
            if existing:
                continue

            # Create program
            program = self.create_program(
                ProgramCreate(
                    name=program_data["name"],
                    description=program_data.get("description"),
                    split_type=program_data["split_type"],
                    days_per_week=program_data["days_per_week"],
                    duration_weeks=program_data.get("duration_weeks"),
                )
            )
            programs_loaded += 1

            # Add workouts
            for workout_data in program_data.get("workouts", []):
                workout = self.add_workout_to_program(
                    program.id,
                    ProgramWorkoutCreate(
                        program_id=program.id,
                        name=workout_data["name"],
                        day_number=workout_data.get("day_number"),
                        description=workout_data.get("description"),
                        estimated_duration_minutes=workout_data.get("estimated_duration_minutes"),
                    ),
                )

                # Add exercises
                for exercise_data in workout_data.get("exercises", []):
                    # Find exercise by name
                    with self.db.get_connection() as conn:
                        exercise_result = conn.execute(
                            "SELECT id FROM exercises WHERE name = ?",
                            (exercise_data["exercise_name"],),
                        ).fetchone()

                        if exercise_result:
                            self.add_exercise_to_workout(
                                workout.id,
                                ProgramExerciseCreate(
                                    program_workout_id=workout.id,
                                    exercise_id=exercise_result[0],
                                    order_number=exercise_data["order_number"],
                                    target_sets=exercise_data["target_sets"],
                                    target_reps_min=exercise_data["target_reps_min"],
                                    target_reps_max=exercise_data["target_reps_max"],
                                    target_rpe=exercise_data.get("target_rpe"),
                                    rest_seconds=exercise_data.get("rest_seconds"),
                                    tempo=exercise_data.get("tempo"),
                                    notes=exercise_data.get("notes"),
                                    is_superset=exercise_data.get("is_superset", False),
                                    superset_group=exercise_data.get("superset_group"),
                                ),
                            )

        return programs_loaded

"""Calculations for strength training metrics and progressive overload."""

from decimal import Decimal


# ============================================================================
# 1RM CALCULATIONS
# ============================================================================


def calculate_1rm_epley(weight: Decimal, reps: int) -> Decimal:
    """
    Calculate estimated 1RM using Epley formula.

    Formula: 1RM = weight × (1 + reps/30)
    Most commonly used formula, works well for 1-10 reps.

    Args:
        weight: Weight lifted
        reps: Number of reps performed

    Returns:
        Estimated 1RM
    """
    if reps == 1:
        return weight
    return weight * (1 + Decimal(reps) / Decimal(30))


def calculate_1rm_brzycki(weight: Decimal, reps: int) -> Decimal:
    """
    Calculate estimated 1RM using Brzycki formula.

    Formula: 1RM = weight × (36 / (37 - reps))
    More conservative than Epley, works well for higher reps.

    Args:
        weight: Weight lifted
        reps: Number of reps performed

    Returns:
        Estimated 1RM
    """
    if reps == 1:
        return weight
    if reps >= 37:
        # Formula breaks down for very high reps
        return calculate_1rm_epley(weight, reps)
    return weight * (Decimal(36) / (Decimal(37) - Decimal(reps)))


def calculate_1rm_lander(weight: Decimal, reps: int) -> Decimal:
    """
    Calculate estimated 1RM using Lander formula.

    Formula: 1RM = (100 × weight) / (101.3 - 2.67123 × reps)
    Good for moderate rep ranges (5-15).

    Args:
        weight: Weight lifted
        reps: Number of reps performed

    Returns:
        Estimated 1RM
    """
    if reps == 1:
        return weight
    denominator = Decimal("101.3") - Decimal("2.67123") * Decimal(reps)
    if denominator <= 0:
        return calculate_1rm_epley(weight, reps)
    return (Decimal(100) * weight) / denominator


def calculate_1rm_lombardi(weight: Decimal, reps: int) -> Decimal:
    """
    Calculate estimated 1RM using Lombardi formula.

    Formula: 1RM = weight × reps^0.1
    Works well for lower rep ranges.

    Args:
        weight: Weight lifted
        reps: Number of reps performed

    Returns:
        Estimated 1RM
    """
    if reps == 1:
        return weight
    # Convert to float for power operation, then back to Decimal
    multiplier = float(reps) ** 0.1
    return weight * Decimal(str(multiplier))


def calculate_1rm_mayhew(weight: Decimal, reps: int) -> Decimal:
    """
    Calculate estimated 1RM using Mayhew formula.

    Formula: 1RM = (100 × weight) / (52.2 + 41.9 × e^(-0.055 × reps))
    Research-backed formula, works well across rep ranges.

    Args:
        weight: Weight lifted
        reps: Number of reps performed

    Returns:
        Estimated 1RM
    """
    if reps == 1:
        return weight
    import math

    denominator = 52.2 + 41.9 * math.exp(-0.055 * reps)
    return (Decimal(100) * weight) / Decimal(str(denominator))


def calculate_1rm_wathan(weight: Decimal, reps: int) -> Decimal:
    """
    Calculate estimated 1RM using Wathan formula.

    Formula: 1RM = (100 × weight) / (48.8 + 53.8 × e^(-0.075 × reps))
    Similar to Mayhew, good for higher reps.

    Args:
        weight: Weight lifted
        reps: Number of reps performed

    Returns:
        Estimated 1RM
    """
    if reps == 1:
        return weight
    import math

    denominator = 48.8 + 53.8 * math.exp(-0.075 * reps)
    return (Decimal(100) * weight) / Decimal(str(denominator))


def calculate_1rm_average(weight: Decimal, reps: int) -> Decimal:
    """
    Calculate estimated 1RM using average of multiple formulas.

    This is generally the most accurate approach as it balances
    the strengths of different formulas.

    Args:
        weight: Weight lifted
        reps: Number of reps performed

    Returns:
        Average estimated 1RM from multiple formulas
    """
    if reps == 1:
        return weight

    formulas = [
        calculate_1rm_epley(weight, reps),
        calculate_1rm_brzycki(weight, reps),
        calculate_1rm_lander(weight, reps),
        calculate_1rm_lombardi(weight, reps),
        calculate_1rm_mayhew(weight, reps),
        calculate_1rm_wathan(weight, reps),
    ]

    return sum(formulas) / Decimal(len(formulas))


# Default 1RM calculation (using average for best accuracy)
calculate_1rm = calculate_1rm_average


# ============================================================================
# REP MAX CALCULATIONS
# ============================================================================


def calculate_n_rm(one_rm: Decimal, target_reps: int) -> Decimal:
    """
    Calculate expected weight for a target rep max based on 1RM.

    Uses inverted Epley formula.

    Args:
        one_rm: Estimated or actual 1RM
        target_reps: Target number of reps

    Returns:
        Expected weight for target reps
    """
    if target_reps == 1:
        return one_rm
    return one_rm / (1 + Decimal(target_reps) / Decimal(30))


def calculate_percentage_of_1rm(one_rm: Decimal, percentage: Decimal) -> Decimal:
    """
    Calculate weight for a given percentage of 1RM.

    Args:
        one_rm: Estimated or actual 1RM
        percentage: Percentage (e.g., 85 for 85%)

    Returns:
        Weight for percentage
    """
    return one_rm * (percentage / Decimal(100))


# ============================================================================
# VOLUME CALCULATIONS
# ============================================================================


def calculate_volume_load(weight: Decimal, reps: int, sets: int = 1) -> Decimal:
    """
    Calculate total volume load.

    Volume = weight × reps × sets

    Args:
        weight: Weight per set
        reps: Reps per set
        sets: Number of sets

    Returns:
        Total volume load
    """
    return weight * Decimal(reps) * Decimal(sets)


def calculate_tonnage(sets_data: list[tuple[Decimal, int]]) -> Decimal:
    """
    Calculate total tonnage from multiple sets.

    Args:
        sets_data: List of (weight, reps) tuples

    Returns:
        Total tonnage
    """
    return sum(weight * Decimal(reps) for weight, reps in sets_data)


# ============================================================================
# PROGRESSIVE OVERLOAD RECOMMENDATIONS
# ============================================================================


def suggest_next_weight(
    recent_sets: list[dict],
    min_increase: Decimal = Decimal("2.5"),
    max_increase: Decimal = Decimal("10"),
) -> Decimal:
    """
    Suggest next weight based on recent performance.

    Algorithm:
    - If last sets were RPE 6-7: increase by max
    - If last sets were RPE 7.5-8.5: increase by mid-range
    - If last sets were RPE 9+: maintain or small increase
    - If reps increased significantly: increase weight

    Args:
        recent_sets: List of recent set data with weight, reps, rpe
        min_increase: Minimum weight increase
        max_increase: Maximum weight increase

    Returns:
        Suggested next weight
    """
    if not recent_sets:
        raise ValueError("No sets provided")

    # Get most recent working sets
    working_sets = [s for s in recent_sets if s.get("set_type") == "working"]
    if not working_sets:
        working_sets = recent_sets

    last_set = working_sets[-1]
    last_weight = last_set["weight"]
    last_reps = last_set["reps"]
    last_rpe = last_set.get("rpe", Decimal("8"))

    # Calculate average RPE of recent sets
    avg_rpe = sum(s.get("rpe", Decimal("8")) for s in working_sets[-3:]) / Decimal(
        len(working_sets[-3:])
    )

    # Decision logic
    if avg_rpe < Decimal("7.5"):
        # Too easy, significant increase
        increase = max_increase
    elif avg_rpe < Decimal("8.5"):
        # Good difficulty, moderate increase
        increase = (min_increase + max_increase) / Decimal(2)
    elif avg_rpe < Decimal("9.5"):
        # High RPE, small increase or maintain
        increase = min_increase
    else:
        # Very high RPE, maintain weight
        increase = Decimal(0)

    # Check if reps increased significantly (hit top of range)
    if len(working_sets) >= 2:
        prev_reps = working_sets[-2]["reps"]
        if last_reps >= prev_reps + 2:
            # Reps increased, justify weight increase
            increase = max(increase, min_increase)

    return last_weight + increase


def suggest_next_reps(
    recent_sets: list[dict], target_reps_min: int = 6, target_reps_max: int = 12
) -> int:
    """
    Suggest next rep target based on recent performance.

    Args:
        recent_sets: List of recent set data
        target_reps_min: Minimum target reps
        target_reps_max: Maximum target reps

    Returns:
        Suggested rep target
    """
    if not recent_sets:
        return target_reps_min

    last_set = recent_sets[-1]
    last_reps = last_set["reps"]
    last_rpe = last_set.get("rpe", Decimal("8"))

    # If hit max reps easily, suggest weight increase instead
    if last_reps >= target_reps_max and last_rpe < Decimal("9"):
        return target_reps_min  # Start fresh at lower reps with higher weight

    # If struggling at low reps, maintain
    if last_reps <= target_reps_min and last_rpe > Decimal("9"):
        return target_reps_min

    # Otherwise, aim for progression
    if last_rpe < Decimal("8"):
        return min(last_reps + 2, target_reps_max)
    return min(last_reps + 1, target_reps_max)


def calculate_fatigue_index(recent_workouts: list[dict]) -> float:
    """
    Calculate fatigue index based on recent training.

    Considers:
    - Workout frequency
    - Average RPE
    - Volume trends

    Args:
        recent_workouts: List of recent workout data with date, volume, avg_rpe

    Returns:
        Fatigue index (0.0 = fresh, 1.0 = high fatigue)
    """
    if not recent_workouts:
        return 0.0

    # Calculate average RPE
    avg_rpe = sum(float(w.get("avg_rpe", 8.0)) for w in recent_workouts) / len(recent_workouts)
    rpe_factor = (avg_rpe - 6.0) / 4.0  # Normalize 6-10 to 0-1

    # Calculate frequency (workouts per week)
    if len(recent_workouts) >= 7:
        frequency = len(recent_workouts) / 7.0
        frequency_factor = min(frequency / 6.0, 1.0)  # 6+ workouts/week = high
    else:
        frequency_factor = 0.3

    # Calculate volume trend (increasing volume = more fatigue)
    if len(recent_workouts) >= 3:
        recent_volume = sum(float(w.get("total_volume", 0)) for w in recent_workouts[-2:])
        older_volume = sum(float(w.get("total_volume", 0)) for w in recent_workouts[-4:-2])
        if older_volume > 0:
            volume_ratio = recent_volume / older_volume
            volume_factor = min((volume_ratio - 0.8) / 0.4, 1.0)  # 1.2x+ = high
            volume_factor = max(volume_factor, 0.0)
        else:
            volume_factor = 0.0
    else:
        volume_factor = 0.0

    # Weighted average
    fatigue_index = 0.4 * rpe_factor + 0.3 * frequency_factor + 0.3 * volume_factor
    return max(0.0, min(fatigue_index, 1.0))


def suggest_deload(weeks_since_deload: int, fatigue: float) -> bool:
    """
    Suggest whether a deload week is needed.

    Recommendation based on:
    - Time since last deload
    - Current fatigue level

    Args:
        weeks_since_deload: Weeks since last deload
        fatigue: Current fatigue index (0.0-1.0)

    Returns:
        True if deload is recommended
    """
    # Automatic deload after 6-8 weeks
    if weeks_since_deload >= 8:
        return True

    # Earlier deload if high fatigue
    if weeks_since_deload >= 4 and fatigue >= 0.8:
        return True

    # Critical fatigue requires immediate deload
    if fatigue >= 0.9:
        return True

    return False


# ============================================================================
# INTENSITY CALCULATIONS
# ============================================================================


def calculate_relative_intensity(weight: Decimal, one_rm: Decimal) -> Decimal:
    """
    Calculate relative intensity as percentage of 1RM.

    Args:
        weight: Weight used
        one_rm: Estimated or actual 1RM

    Returns:
        Percentage of 1RM
    """
    if one_rm == 0:
        return Decimal(0)
    return (weight / one_rm) * Decimal(100)


def estimate_reps_at_weight(one_rm: Decimal, weight: Decimal) -> int:
    """
    Estimate how many reps can be performed at a given weight.

    Uses inverted Epley formula.

    Args:
        one_rm: Estimated or actual 1RM
        weight: Weight to estimate reps for

    Returns:
        Estimated reps to failure
    """
    if weight >= one_rm:
        return 1
    if weight == 0:
        return 0

    # Inverted Epley: reps = 30 × ((1RM / weight) - 1)
    reps = 30 * ((one_rm / weight) - 1)
    return max(1, int(reps))


def rpe_to_rir(rpe: Decimal) -> int:
    """
    Convert RPE (Rate of Perceived Exertion) to RIR (Reps in Reserve).

    Args:
        rpe: RPE value (6.0-10.0)

    Returns:
        Estimated reps in reserve
    """
    # RPE 10 = 0 RIR, RPE 9.5 = 0-1 RIR, RPE 9 = 1 RIR, etc.
    if rpe >= Decimal("10"):
        return 0
    if rpe >= Decimal("9.5") or rpe >= Decimal("9"):
        return 1
    if rpe >= Decimal("8.5") or rpe >= Decimal("8"):
        return 2
    if rpe >= Decimal("7.5") or rpe >= Decimal("7"):
        return 3
    return 4


def rir_to_rpe(rir: int) -> Decimal:
    """
    Convert RIR (Reps in Reserve) to RPE.

    Args:
        rir: Reps in reserve

    Returns:
        RPE value
    """
    rir_to_rpe_map = {
        0: Decimal("10"),
        1: Decimal("9"),
        2: Decimal("8"),
        3: Decimal("7"),
        4: Decimal("6.5"),
    }
    return rir_to_rpe_map.get(rir, Decimal("6"))

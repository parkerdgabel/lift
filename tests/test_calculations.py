"""Tests for calculation utilities."""

from decimal import Decimal

from lift.utils.calculations import (
    calculate_1rm_average,
    calculate_1rm_brzycki,
    calculate_1rm_epley,
    calculate_n_rm,
    calculate_percentage_of_1rm,
    calculate_relative_intensity,
    calculate_tonnage,
    calculate_volume_load,
    estimate_reps_at_weight,
    rir_to_rpe,
    rpe_to_rir,
)


class TestOneRMCalculations:
    """Test 1RM calculation formulas."""

    def test_calculate_1rm_epley_single_rep(self):
        """Test Epley formula with single rep."""
        result = calculate_1rm_epley(Decimal("315"), 1)
        assert result == Decimal("315")

    def test_calculate_1rm_epley_multiple_reps(self):
        """Test Epley formula with multiple reps."""
        # 225 lbs × 5 reps
        # Formula: 225 × (1 + 5/30) = 225 × 1.1667 = 262.5
        result = calculate_1rm_epley(Decimal("225"), 5)
        expected = Decimal("225") * (1 + Decimal("5") / Decimal("30"))
        assert result == expected

    def test_calculate_1rm_epley_high_reps(self):
        """Test Epley formula with high reps."""
        # 185 lbs × 10 reps
        # Formula: 185 × (1 + 10/30) = 185 × 1.3333 = 246.67
        result = calculate_1rm_epley(Decimal("185"), 10)
        expected = Decimal("185") * (1 + Decimal("10") / Decimal("30"))
        assert result == expected

    def test_calculate_1rm_brzycki_single_rep(self):
        """Test Brzycki formula with single rep."""
        result = calculate_1rm_brzycki(Decimal("315"), 1)
        assert result == Decimal("315")

    def test_calculate_1rm_brzycki_multiple_reps(self):
        """Test Brzycki formula with multiple reps."""
        # 225 lbs × 5 reps
        # Formula: 225 × (36 / (37 - 5)) = 225 × (36 / 32) = 253.125
        result = calculate_1rm_brzycki(Decimal("225"), 5)
        assert result == Decimal("253.125")

    def test_calculate_1rm_brzycki_high_reps(self):
        """Test Brzycki formula falls back to Epley for very high reps."""
        # Should fall back to Epley for 37+ reps
        result = calculate_1rm_brzycki(Decimal("100"), 40)
        expected = calculate_1rm_epley(Decimal("100"), 40)
        assert result == expected

    def test_calculate_1rm_average(self):
        """Test average 1RM calculation."""
        # Average should be between different formulas
        result = calculate_1rm_average(Decimal("225"), 5)

        # Should be a reasonable estimate
        assert result > Decimal("250")
        assert result < Decimal("280")


class TestVolumeCalculations:
    """Test volume and tonnage calculations."""

    def test_calculate_volume_load_single_set(self):
        """Test volume calculation for single set."""
        result = calculate_volume_load(Decimal("185"), 10, 1)
        assert result == Decimal("1850")

    def test_calculate_volume_load_multiple_sets(self):
        """Test volume calculation for multiple sets."""
        result = calculate_volume_load(Decimal("185"), 10, 3)
        assert result == Decimal("5550")

    def test_calculate_tonnage(self):
        """Test tonnage calculation from multiple sets."""
        sets_data = [
            (Decimal("185"), 10),
            (Decimal("185"), 10),
            (Decimal("185"), 8),
        ]

        result = calculate_tonnage(sets_data)
        # 1850 + 1850 + 1480 = 5180
        assert result == Decimal("5180")

    def test_calculate_tonnage_varying_weights(self):
        """Test tonnage with varying weights."""
        sets_data = [
            (Decimal("135"), 12),
            (Decimal("185"), 10),
            (Decimal("225"), 8),
            (Decimal("245"), 6),
        ]

        result = calculate_tonnage(sets_data)
        # 1620 + 1850 + 1800 + 1470 = 6740
        assert result == Decimal("6740")

    def test_calculate_tonnage_empty(self):
        """Test tonnage with no sets."""
        result = calculate_tonnage([])
        assert result == Decimal("0")


class TestIntensityCalculations:
    """Test intensity and relative strength calculations."""

    def test_calculate_relative_intensity(self):
        """Test relative intensity calculation."""
        # 185 lbs with 225 1RM
        result = calculate_relative_intensity(Decimal("185"), Decimal("225"))
        expected = (Decimal("185") / Decimal("225")) * Decimal("100")
        assert result == expected

    def test_calculate_relative_intensity_zero_1rm(self):
        """Test relative intensity with zero 1RM."""
        result = calculate_relative_intensity(Decimal("185"), Decimal("0"))
        assert result == Decimal("0")

    def test_estimate_reps_at_weight(self):
        """Test estimating reps at a given weight."""
        # With 225 1RM, how many reps at 185?
        result = estimate_reps_at_weight(Decimal("225"), Decimal("185"))

        # Should be around 6-8 reps
        assert result >= 6
        assert result <= 8

    def test_estimate_reps_at_weight_max(self):
        """Test estimating reps at max weight."""
        result = estimate_reps_at_weight(Decimal("225"), Decimal("225"))
        assert result == 1

    def test_estimate_reps_at_weight_over_max(self):
        """Test estimating reps above max weight."""
        result = estimate_reps_at_weight(Decimal("225"), Decimal("250"))
        assert result == 1


class TestRepMaxCalculations:
    """Test rep max calculations."""

    def test_calculate_n_rm_single_rep(self):
        """Test calculating 1RM from 1RM."""
        result = calculate_n_rm(Decimal("225"), 1)
        assert result == Decimal("225")

    def test_calculate_n_rm_multiple_reps(self):
        """Test calculating weight for target reps."""
        # With 225 1RM, what should 5RM be?
        result = calculate_n_rm(Decimal("225"), 5)

        # Using inverse Epley: 225 / (1 + 5/30) = 225 / 1.1667 ≈ 192.86
        expected = Decimal("225") / (1 + Decimal("5") / Decimal("30"))
        assert result == expected

    def test_calculate_percentage_of_1rm(self):
        """Test calculating weight from percentage."""
        result = calculate_percentage_of_1rm(Decimal("300"), Decimal("80"))
        assert result == Decimal("240")

    def test_calculate_percentage_of_1rm_100_percent(self):
        """Test calculating 100% of 1RM."""
        result = calculate_percentage_of_1rm(Decimal("315"), Decimal("100"))
        assert result == Decimal("315")


class TestRPEConversions:
    """Test RPE and RIR conversions."""

    def test_rpe_to_rir_maximum(self):
        """Test converting max RPE to RIR."""
        assert rpe_to_rir(Decimal("10")) == 0

    def test_rpe_to_rir_high(self):
        """Test converting high RPE to RIR."""
        assert rpe_to_rir(Decimal("9.5")) == 1
        assert rpe_to_rir(Decimal("9")) == 1

    def test_rpe_to_rir_moderate(self):
        """Test converting moderate RPE to RIR."""
        assert rpe_to_rir(Decimal("8.5")) == 2
        assert rpe_to_rir(Decimal("8")) == 2

    def test_rpe_to_rir_low(self):
        """Test converting low RPE to RIR."""
        assert rpe_to_rir(Decimal("7.5")) == 3
        assert rpe_to_rir(Decimal("7")) == 3
        assert rpe_to_rir(Decimal("6")) == 4

    def test_rir_to_rpe_zero(self):
        """Test converting 0 RIR to RPE."""
        assert rir_to_rpe(0) == Decimal("10")

    def test_rir_to_rpe_one(self):
        """Test converting 1 RIR to RPE."""
        assert rir_to_rpe(1) == Decimal("9")

    def test_rir_to_rpe_multiple(self):
        """Test converting various RIR to RPE."""
        assert rir_to_rpe(2) == Decimal("8")
        assert rir_to_rpe(3) == Decimal("7")
        assert rir_to_rpe(4) == Decimal("6.5")

    def test_rir_to_rpe_high(self):
        """Test converting high RIR to RPE."""
        # Should default to 6 for high RIR
        result = rir_to_rpe(10)
        assert result == Decimal("6")


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_weight(self):
        """Test calculations with zero weight."""
        result = calculate_volume_load(Decimal("0"), 10, 1)
        assert result == Decimal("0")

    def test_zero_reps(self):
        """Test calculations with zero reps."""
        # Note: In practice, reps should be >= 1 based on model validation
        # But testing the calculation function itself
        result = calculate_volume_load(Decimal("185"), 0, 1)
        assert result == Decimal("0")

    def test_high_rep_range(self):
        """Test 1RM calculation with very high reps."""
        # 100 lbs × 20 reps - should still give reasonable estimate
        result = calculate_1rm_epley(Decimal("100"), 20)

        # Formula: 100 × (1 + 20/30) = 100 × 1.6667 = 166.67
        expected = Decimal("100") * (1 + Decimal("20") / Decimal("30"))
        assert result == expected

    def test_decimal_precision(self):
        """Test that decimal precision is maintained."""
        result = calculate_1rm_epley(Decimal("225.5"), 5)

        # Should maintain decimal precision
        assert isinstance(result, Decimal)
        assert result == Decimal("225.5") * (1 + Decimal("5") / Decimal("30"))

    def test_large_weights(self):
        """Test calculations with large weights."""
        result = calculate_volume_load(Decimal("1000"), 5, 3)
        assert result == Decimal("15000")

    def test_fractional_weights(self):
        """Test calculations with fractional weights."""
        result = calculate_volume_load(Decimal("52.5"), 10, 1)
        assert result == Decimal("525.0")

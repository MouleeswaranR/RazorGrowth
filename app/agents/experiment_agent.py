import random
from app.schemas.agent_outputs import ExperimentMetricsOutput


class ExperimentAgent:
    """Configures randomized test cohorts and outputs structured experiment measurement metrics."""

    def split_cohort(
        self,
        audience: list[dict],
        treatment_ratio: float = 0.8,
    ) -> tuple[list[dict], list[dict]]:
        """Splits target audience cohort into treatment and control test groups."""
        shuffled = list(audience)
        random.shuffle(shuffled)
        split_point = max(1, int(len(shuffled) * treatment_ratio))
        return shuffled[:split_point], shuffled[split_point:]

    def calculate_experiment_metrics(
        self,
        treatment_conversions: int,
        treatment_total: int,
        control_conversions: int,
        control_total: int,
        average_order_value: float = 2850.0,
    ) -> ExperimentMetricsOutput:
        """Computes statistical conversion lift, absolute pp difference, and normalized incremental financial ROI."""
        treatment_rate = treatment_conversions / max(1, treatment_total)
        control_rate = control_conversions / max(1, control_total)

        absolute_diff = (treatment_rate - control_rate) * 100.0

        if control_rate > 0:
            relative_lift = ((treatment_rate - control_rate) / control_rate) * 100.0
            relative_lift_display = f"{relative_lift:+0.1f}%"
            rel_lift_val = round(relative_lift, 2)
        else:
            rel_lift_val = None
            relative_lift_display = "N/A (control = 0%)"

        expected_control_orders_in_treatment = treatment_total * control_rate
        incremental_orders = int(round(treatment_conversions - expected_control_orders_in_treatment))
        incremental_revenue = round(incremental_orders * average_order_value, 2)

        if control_rate == 0 and treatment_conversions > 0:
            status_note = (
                f"Treatment generated {treatment_conversions} conversions vs 0 in control group. "
                f"Relative percentage lift is N/A because baseline control conversion is 0.0%."
            )
        elif incremental_orders > 0:
            status_note = f"Treatment generated +{incremental_orders} incremental orders (+₹{incremental_revenue:,.0f} GMV lift)"
        elif incremental_orders < 0:
            status_note = f"Treatment underperformed counterfactual baseline by {abs(incremental_orders)} orders (-₹{abs(incremental_revenue):,.0f})"
        else:
            status_note = "Treatment performed in parity with control baseline (0 incremental orders)"

        return ExperimentMetricsOutput(
            treatment_conversion_rate=round(treatment_rate, 4),
            control_conversion_rate=round(control_rate, 4),
            conversion_lift_percentage=rel_lift_val,
            relative_lift_display=relative_lift_display,
            absolute_difference_percentage=round(absolute_diff, 2),
            treatment_total_count=treatment_total,
            control_total_count=control_total,
            treatment_orders_count=treatment_conversions,
            control_orders_count=control_conversions,
            incremental_orders_count=incremental_orders,
            incremental_revenue_inr=incremental_revenue,
            status_note=status_note,
        )

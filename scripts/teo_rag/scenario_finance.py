"""Derive what-if poultry KPI from baseline rabbit block (documented heuristics)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PoultryDerivation:
    output_tons_year: int
    capex_bln_rub: float
    npv_thousand_rub: int
    irr_pct: float
    payback_months: int
    revenue_delta_bln_rub: float
    investment_delta_bln_rub: float
    method: str
    assumptions: dict


def derive_poultry_from_rabbit(
    *,
    rabbit_output_t: int = 7000,
    rabbit_capex_bln: float = 12.0,
    rabbit_npv_ths: int = 2_779_519,
    rabbit_irr_pct: float = 15.19,
    rabbit_payback_mo: int = 84,
    poultry_output_t: int = 12_000,
    capex_marginal_per_1000t_bln: float = 1.0,
    margin_factor: float = 0.85,
    irr_uplift_pct: float = 3.3,
    revenue_per_1000t_bln: float = 0.52,
) -> PoultryDerivation:
    """
    Heuristic extrapolation (not full DCF):
    - CAPEX = rabbit CAPEX + marginal per extra 1000t (default +5 млрд → 17)
    - NPV scales with output vs rabbit, discounted by margin_factor
    """
    npv_per_t = rabbit_npv_ths / max(rabbit_output_t, 1)
    npv = int(poultry_output_t * npv_per_t * margin_factor)
    extra_t = max(poultry_output_t - rabbit_output_t, 0)
    capex = round(rabbit_capex_bln + (extra_t / 1000) * capex_marginal_per_1000t_bln, 1)
    irr = round(rabbit_irr_pct + irr_uplift_pct, 2)
    payback = int(rabbit_payback_mo * (rabbit_irr_pct / irr) * 1.1)
    rev_delta = round((poultry_output_t - rabbit_output_t) * revenue_per_1000t_bln / 1000, 1)
    inv_delta = round(capex - rabbit_capex_bln, 1)

    return PoultryDerivation(
        output_tons_year=poultry_output_t,
        capex_bln_rub=capex,
        npv_thousand_rub=npv,
        irr_pct=irr,
        payback_months=payback,
        revenue_delta_bln_rub=rev_delta,
        investment_delta_bln_rub=inv_delta,
        method="heuristic_from_baseline_rabbit",
        assumptions={
            "rabbit_output_t": rabbit_output_t,
            "rabbit_capex_bln": rabbit_capex_bln,
            "rabbit_npv_ths": rabbit_npv_ths,
            "margin_factor": margin_factor,
            "capex_marginal_per_1000t_bln": capex_marginal_per_1000t_bln,
            "irr_uplift_pct": irr_uplift_pct,
            "revenue_per_1000t_bln": revenue_per_1000t_bln,
        },
    )

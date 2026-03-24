"""Default measurement layout: parameter names, types, descriptions."""

from __future__ import annotations

from core.models import LimitDefinition, ParameterType

# Rows from spec §8: (temp_param, pressure_param, description, turbo_req, na_req)
# turbo_req / na_req: True = required, False = not applicable, None = optional
_LAYOUT_ROWS: list[tuple[str | None, str | None, str, bool | None, bool | None]] = [
    ("T0", "P0", "Air inlet before Filter", True, True),
    ("T1", "P1", "Air inlet after filter", True, True),
    ("T2_L1", "P2_L1", "Air inlet Before Turbo", True, False),
    ("T2_I1", "P2_I1", "Air inlet After Intercooler", True, False),
    ("T2_E1", "P2_E1", "Air inlet at manifold after EGR mixing", True, True),
    ("T_ARF1", "P_ARF1", "Exhaust EGR before EGR cooler", True, False),
    ("T_ARF2", "P_ARF2", "Exhaust EGR after EGR cooler", True, False),
    ("T3_Z1", "P3_Z1", "Exhaust temperature cylinder 1", True, True),
    ("T3_Z2", "P3_Z2", "Exhaust temperature cylinder 2", True, True),
    ("T3_Z3", "P3_Z3", "Exhaust temperature cylinder 3", True, True),
    ("T3_Z4", "P3_Z4", "Exhaust temperature cylinder 4", True, True),
    ("T3_A1", "P3_A1", "Before Turbo Charger", True, False),
    ("T4_A1", "P4_A1", "After Turbo Charger", True, True),
    ("TKAT_V", "PKAT_V", "Before Catalytic converter", None, None),
    ("TKAT_N", "PKAT_N", "After Catalytic converter", None, None),
    ("TDPF_V", "PDPF_V", "Before Particulate filter", None, None),
    ("TDPF_N", "PDPF_N", "After Particulate filter", None, None),
    ("TW_R", "PW_R", "Coolant Return from engine", True, True),
    ("TW_Z", "PW_Z", "Coolant Inlet to engine", True, True),
    ("TKR_R", "PKR_R", "Fuel Inlet to engine", True, True),
    ("TKR_Z", "PKR_Z", "Fuel Return from engine", True, True),
    ("TOEL", "POEL", "Lube oil", True, True),
    ("Lambda", None, "Lambdameter", None, None),
    ("CDM", None, "Indicom Signal", True, True),
    (None, "PZ_MAX1", "Combustion Pressure cylinder 1", None, None),
    (None, "PZ_MAX2", "Combustion Pressure cylinder 2", None, None),
    (None, "PZ_MAX3", "Combustion Pressure cylinder 3", None, None),
    (None, "PZ_MAX4", "Combustion Pressure cylinder 4", True, True),
    (None, "EGR_CO2", "EGR CO2 value inlet manifold", None, None),
]


def _unit_for(ptype: ParameterType) -> str:
    if ptype == ParameterType.TEMPERATURE:
        return "°C"
    if ptype == ParameterType.PRESSURE:
        return "mbar"
    return ""


def default_limit_definitions(engine_na: bool) -> list[LimitDefinition]:
    """
    Build default limit rows for an engine profile (NA vs Turbo).

    Args:
        engine_na: If True, skip turbo-only / EGR-only parameters.

    Returns:
        List of LimitDefinition with is_required set from matrix.
    """
    out: list[LimitDefinition] = []
    for t_name, p_name, desc, turbo_req, na_req in _LAYOUT_ROWS:
        names: list[tuple[str, ParameterType]] = []
        if t_name:
            if t_name == "Lambda":
                pt = ParameterType.EMISSION
            elif t_name == "CDM":
                pt = ParameterType.OTHER
            else:
                pt = ParameterType.TEMPERATURE
            names.append((t_name, pt))
        if p_name:
            if p_name == "EGR_CO2":
                pt = ParameterType.EMISSION
            elif p_name.startswith("PZ_MAX"):
                pt = ParameterType.COMBUSTION
            else:
                pt = ParameterType.PRESSURE
            names.append((p_name, pt))

        for param_name, ptype in names:
            if engine_na:
                if na_req is False:
                    continue
                req = bool(na_req) if na_req is not None else False
            else:
                if turbo_req is False:
                    continue
                req = bool(turbo_req) if turbo_req is not None else False

            out.append(
                LimitDefinition(
                    parameter_name=param_name,
                    parameter_type=ptype,
                    description=desc,
                    unit=_unit_for(ptype),
                    is_required=req,
                )
            )
    return out


def all_standard_parameter_names() -> list[str]:
    """All unique standard names (for column detection)."""
    seen: set[str] = set()
    order: list[str] = []
    for t_name, p_name, _, _, _ in _LAYOUT_ROWS:
        for n in (t_name, p_name):
            if n and n not in seen:
                seen.add(n)
                order.append(n)
    return order

"""Domain models for Bosch Plausibility Check Tool."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class EngineType(Enum):
    """Default engine type presets (optional)."""

    TURBO_4CYL = "Turbo 4-Cylinder"
    NA_4CYL = "NA 4-Cylinder"
    TURBO_6CYL = "Turbo 6-Cylinder"
    NA_6CYL = "NA 6-Cylinder"


class ParameterType(Enum):
    """Parameter classification."""

    TEMPERATURE = "Temperature"
    PRESSURE = "Pressure"
    EMISSION = "Emission"
    COMBUSTION = "Combustion"
    OTHER = "Other"
    SET = "Set"


class Status(Enum):
    """Legacy single-value status."""

    OK = "OK"
    WARNING = "WARNING"
    FAIL = "FAIL"
    NO_DATA = "NO_DATA"


def parameter_type_from_string(s: str) -> "ParameterType":
    s = (s or "").strip().lower()
    mapping = {
        "temperature": ParameterType.TEMPERATURE,
        "temp": ParameterType.TEMPERATURE,
        "pressure": ParameterType.PRESSURE,
        "press": ParameterType.PRESSURE,
        "emission": ParameterType.EMISSION,
        "emissions": ParameterType.EMISSION,
        "combustion": ParameterType.COMBUSTION,
        "set": ParameterType.SET,
        "other": ParameterType.OTHER,
    }
    for k, v in mapping.items():
        if k in s or s == k:
            return v
    for p in ParameterType:
        if p.value.lower() == s:
            return p
    return ParameterType.OTHER


@dataclass
class LimitDefinition:
    """Single parameter limit row (profile editor / DB)."""

    parameter_name: str
    parameter_type: ParameterType
    description: str
    unit: str = ""
    lower_limit: Optional[float] = None
    upper_limit: Optional[float] = None
    warning_pct: float = 10.0
    root_cause: str = ""
    corrective_action: str = ""
    is_required: bool = False
    is_enabled: bool = True
    category: str = ""


@dataclass
class MeasurementResult:
    """One row of plausibility analysis output."""

    parameter_name: str
    description: str
    measured_value: Optional[float]
    value_min: Optional[float] = None
    value_max: Optional[float] = None
    value_avg: Optional[float] = None
    value_type: str = "instant"
    status: str = "NO_DATA"
    lower_limit: Optional[float] = None
    upper_limit: Optional[float] = None
    deviation_pct: Optional[float] = None
    root_cause: str = ""
    corrective_action: str = ""
    timestamp: Optional[str] = None
    category: str = ""
    param_type: str = ""
    unit: str = ""
    num_runs: int = 0


@dataclass
class Project:
    """Test project."""

    id: Optional[int] = None
    name: str = ""
    engine_type: EngineType = EngineType.TURBO_4CYL
    engine_type_name: str = ""
    engine_code: str = ""
    engine_variant: str = ""
    test_bed_id: str = ""
    customer_oem: str = ""
    emission_norm: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True

    def engine_type_key(self) -> str:
        """Key for limit_profiles.engine_type."""
        if self.engine_type_name and str(self.engine_type_name).strip():
            return str(self.engine_type_name).strip()
        return self.engine_type.value


@dataclass
class UploadSession:
    """One PUMA file upload session."""

    id: Optional[int] = None
    project_id: int = 0
    file_name: str = ""
    file_path: Optional[str] = None
    upload_date: Optional[datetime] = None
    record_count: int = 0
    pass_count: int = 0
    warn_count: int = 0
    fail_count: int = 0


@dataclass
class ParsedRow:
    """One row from PUMA import with optional multi-value columns."""

    timestamp: Optional[str] = None
    values: dict[str, Optional[float]] = field(default_factory=dict)

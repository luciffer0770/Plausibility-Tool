"""Domain models for PRÜF."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class EngineType(Enum):
    """Supported engine types for limit profiles."""

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


class Status(Enum):
    """Plausibility status for a measurement."""

    OK = "OK"
    WARNING = "WARNING"
    FAIL = "FAIL"
    NO_DATA = "NO_DATA"


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
    status: Status = Status.NO_DATA
    lower_limit: Optional[float] = None
    upper_limit: Optional[float] = None
    deviation_pct: Optional[float] = None
    root_cause: str = ""
    corrective_action: str = ""
    timestamp: Optional[str] = None


@dataclass
class Project:
    """Test project."""

    id: Optional[int] = None
    name: str = ""
    engine_type: EngineType = EngineType.TURBO_4CYL
    engine_variant: str = ""
    test_bed_id: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True


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

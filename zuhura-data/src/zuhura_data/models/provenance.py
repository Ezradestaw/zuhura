"""
Zuhura Planetary Digital Twin - Provenance & Scientific Quality Framework
Implements a strict finite state machine for data product validation
and tracks full processing history, inputs, parameters, and cryptographic hashes.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class ValidationStatus(str, Enum):
    DISCOVERED = "discovered"
    DOWNLOADED = "downloaded"
    CHECKSUM_VERIFIED = "checksum_verified"
    METADATA_VALIDATED = "metadata_validated"
    SCIENTIFICALLY_VALIDATED = "scientifically_validated"
    PROCESSED = "processed"
    DERIVED = "derived"


# Allowed state transitions (forward progress or re-evaluation)
ALLOWED_TRANSITIONS: Dict[ValidationStatus, List[ValidationStatus]] = {
    ValidationStatus.DISCOVERED: [ValidationStatus.DOWNLOADED],
    ValidationStatus.DOWNLOADED: [ValidationStatus.CHECKSUM_VERIFIED],
    ValidationStatus.CHECKSUM_VERIFIED: [ValidationStatus.METADATA_VALIDATED],
    ValidationStatus.METADATA_VALIDATED: [ValidationStatus.SCIENTIFICALLY_VALIDATED],
    ValidationStatus.SCIENTIFICALLY_VALIDATED: [ValidationStatus.PROCESSED, ValidationStatus.DERIVED],
    ValidationStatus.PROCESSED: [ValidationStatus.DERIVED, ValidationStatus.SCIENTIFICALLY_VALIDATED],
    ValidationStatus.DERIVED: [ValidationStatus.SCIENTIFICALLY_VALIDATED],
}


class FileProvenance(BaseModel):
    """File reference with cryptographic hash and byte size."""
    path: str
    sha256: str
    size_bytes: Optional[int] = None
    role: Optional[str] = None  # e.g. "input_raw", "output_cog", "browse_image"


class ProcessingStep(BaseModel):
    """
    Detailed provenance record for an individual processing step.
    """
    step_id: str
    step_name: str
    software: str
    version: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    parameters: Dict[str, Any] = Field(default_factory=dict)
    input_files: List[FileProvenance] = Field(default_factory=list)
    output_files: List[FileProvenance] = Field(default_factory=list)
    scientific_assumptions: Optional[str] = None
    operator: Optional[str] = "Zuhura Planetary Automated Pipeline"


class ProvenanceHistory(BaseModel):
    """
    Lifecycle tracking and validation state machine for a scientific product.
    """
    current_status: ValidationStatus = ValidationStatus.DISCOVERED
    status_log: List[Dict[str, Any]] = Field(default_factory=list)
    steps: List[ProcessingStep] = Field(default_factory=list)

    def transition_to(self, new_status: ValidationStatus, reason: str) -> None:
        """
        Transition to a new validation status, enforcing state machine rules.
        """
        if new_status == self.current_status:
            return  # No-op

        allowed = ALLOWED_TRANSITIONS.get(self.current_status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Invalid state transition: Cannot transition from '{self.current_status.value}' "
                f"directly to '{new_status.value}'. Allowed next states: {[s.value for s in allowed]}"
            )

        self.current_status = new_status
        self.status_log.append({
            "status": new_status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason
        })

    def record_step(self, step: ProcessingStep) -> None:
        """Append an executed processing step to provenance history."""
        self.steps.append(step)

"""
Reproducibility records for computed results.
Generates deterministic hashes, tracking manifests, and audit trails for scientific queries.
"""

import hashlib
import json
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from zuhura.provenance.taxonomy import ScientificProvenanceRecord


class ComputationManifest(BaseModel):
    """Immutable record of an executed scientific computation."""
    computation_id: str
    run_timestamp_utc: float = Field(default_factory=time.time)
    algorithm_name: str
    algorithm_version: str
    input_parameters_hash: str
    input_parameters: Dict[str, Any]
    output_summary_hash: str
    execution_duration_ms: float
    provenance: ScientificProvenanceRecord


def generate_computation_hash(data: Dict[str, Any]) -> str:
    """Computes deterministic SHA-256 hash of JSON-serializable parameters."""
    normalized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def create_computation_manifest(
    algorithm_name: str,
    algorithm_version: str,
    inputs: Dict[str, Any],
    outputs: Dict[str, Any],
    duration_ms: float,
    provenance: ScientificProvenanceRecord
) -> ComputationManifest:
    """Builds a verified computation manifest."""
    in_hash = generate_computation_hash(inputs)
    out_hash = generate_computation_hash(outputs)
    comp_id = f"COMP_{algorithm_name.upper()}_{in_hash[:8]}"
    return ComputationManifest(
        computation_id=comp_id,
        algorithm_name=algorithm_name,
        algorithm_version=algorithm_version,
        input_parameters_hash=in_hash,
        input_parameters=inputs,
        output_summary_hash=out_hash,
        execution_duration_ms=round(duration_ms, 2),
        provenance=provenance
    )

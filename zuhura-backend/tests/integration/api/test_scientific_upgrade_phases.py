"""
Zuhura Backend - Integration Tests for Next-Generation Scientific Upgrade (Phases 2-8)
Tests centralized provenance, InSight multi-model reconciliation, terramechanics rover simulation,
modular CV pinpoint pipeline, research question decomposition, and Prometheus metrics.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from zuhura.api.main import app
from zuhura.provenance.taxonomy import (
    EpistemicClassification,
    ProvenanceFactory,
    ScientificProvenanceRecord,
)
from zuhura.navigation.mobility_model import (
    ROVER_SPECIFICATIONS,
    assess_terramechanics,
    compute_energy_consumption,
    evaluate_mobility_feasibility,
)
from zuhura.pinpoint.cv_pipeline import visual_pipeline, BENCHMARK_GROUND_TRUTH
from zuhura.pinpoint.engine import LocationPinpointEngine
from zuhura.ai.research_agent import (
    decompose_research_question,
    search_literature,
    run_comparative_geological_analysis,
)


@pytest.mark.asyncio
async def test_scientific_truth_provenance():
    """Validates epistemic classification and provenance factory records."""
    mola_prov = ProvenanceFactory.create_mola_elevation_provenance()
    assert mola_prov.classification == EpistemicClassification.MEASURED
    assert mola_prov.vertical_datum == "MARS_AREOID_MOLA_MEG128 (Equipotential Zero Elevation)"
    assert mola_prov.validation_status == "VALIDATED"
    assert len(mola_prov.scientific_references) >= 1

    insight_prov = ProvenanceFactory.create_insight_interior_provenance("samuel_2023_basal_molten")
    assert insight_prov.classification == EpistemicClassification.DERIVED
    assert "Nature" in insight_prov.scientific_references[0].journal


@pytest.mark.asyncio
async def test_advanced_terramechanics_and_energy():
    """Validates Bekker soil slip, mechanical energy work, and feasibility breakdown."""
    perseverance = ROVER_SPECIFICATIONS["rover_perseverance"]
    
    # 1. Terramechanics at gentle slope
    gentle_terramech = assess_terramechanics(slope_deg=5.0, roughness_tri=1.2, vehicle=perseverance)
    assert gentle_terramech.estimated_wheel_slip_pct < 25.0
    assert gentle_terramech.soil_shear_risk == "LOW"

    # 2. Terramechanics at steep slope
    steep_terramech = assess_terramechanics(slope_deg=28.0, roughness_tri=5.0, vehicle=perseverance)
    assert steep_terramech.estimated_wheel_slip_pct > 40.0
    assert steep_terramech.soil_shear_risk in ("MODERATE", "CRITICAL")

    # 3. Energy consumption
    energy = compute_energy_consumption(
        distance_km=2.0,
        elevation_gain_m=50.0,
        mean_slope_deg=6.0,
        duration_hours=16.0,
        vehicle=perseverance
    )
    assert energy.total_energy_wh > 0.0
    assert energy.mechanical_drive_energy_wh > 0.0

    # 4. Feasibility
    feasibility = evaluate_mobility_feasibility(
        max_slope_deg=12.0,
        terramechanics=gentle_terramech,
        energy=energy,
        vehicle=perseverance,
        duration_sols=4.0
    )
    assert feasibility.geometric_feasible is True
    assert feasibility.engineering_feasible is True
    assert feasibility.mission_feasible is True


@pytest.mark.asyncio
async def test_cv_pipeline_and_benchmark():
    """Validates multi-scale CV pipeline, ground truth dataset, and conclusive calibration."""
    engine = LocationPinpointEngine()
    benchmark_res = engine.run_benchmark_evaluation()
    assert benchmark_res["status"] == "BENCHMARK_COMPLETE"
    assert benchmark_res["benchmark_samples_count"] >= 5
    assert benchmark_res["top1_accuracy_pct"] >= 50.0
    assert benchmark_res["median_latency_ms"] < 200.0


@pytest.mark.asyncio
async def test_research_question_decomposition_and_literature():
    """Validates question decomposition and planetary literature retrieval."""
    plan = decompose_research_question(
        research_question="Compare Jezero Crater and Gale Crater sedimentary facings",
        target_feature_names=["Jezero Crater", "Gale Crater"]
    )
    assert len(plan.decomposed_sub_hypotheses) >= 3
    assert any("MOLA" in inst for inst in plan.required_instruments)
    assert len(plan.recommended_literature) >= 1

    # Comparative analysis
    comp = run_comparative_geological_analysis("Jezero Crater", "Gale Crater")
    assert comp["status"] == "COMPLETED"
    assert "areoid_elevation_m" in comp["feature_a"]
    assert "comparative_deltas" in comp
    assert "[MEASURED]" in comp["scientific_synthesis"]


@pytest.mark.asyncio
async def test_prometheus_metrics_endpoint():
    """Validates Prometheus /metrics output format."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Generate some traffic
        await client.get("/api/v1/health")
        
        # Scrape metrics
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        content = resp.text
        assert "zuhura_uptime_seconds" in content
        assert "zuhura_http_requests_total" in content
        assert "# TYPE zuhura_uptime_seconds gauge" in content

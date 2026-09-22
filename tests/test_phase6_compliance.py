"""Phase 6: SIH26164 compliance engine tests."""
from ecdat.compliance import get_summary, get_requirements, REQUIREMENTS, IMPLEMENTED, PARTIALLY_IMPLEMENTED, NOT_IMPLEMENTED

VALID_STATUSES = {IMPLEMENTED, PARTIALLY_IMPLEMENTED, NOT_IMPLEMENTED}

def test_all_requirements_have_valid_status():
    for req in REQUIREMENTS:
        assert req["status"] in VALID_STATUSES, f"{req['id']} has invalid status"

def test_all_requirements_have_required_fields():
    required = {"id", "requirement", "status", "implementation", "modules", "apis", "tests"}
    for req in REQUIREMENTS:
        missing = required - req.keys()
        assert not missing, f"{req['id']} missing fields: {missing}"

def test_requirement_ids_unique():
    ids = [req["id"] for req in REQUIREMENTS]
    assert len(ids) == len(set(ids))

def test_summary_counts_match_requirements():
    summary = get_summary()
    manual = sum(1 for r in REQUIREMENTS if r["status"] == IMPLEMENTED)
    assert summary["implemented"] == manual

def test_summary_total_matches():
    summary = get_summary()
    assert summary["total"] == len(REQUIREMENTS)
    assert summary["total"] == summary["implemented"] + summary["partially_implemented"] + summary["not_implemented"]

def test_all_twelve_sih_requirements_covered():
    """Ensure every official SIH26164 requirement has an entry."""
    assert len(REQUIREMENTS) >= 12

def test_no_fake_100_percent():
    """Not all requirements should be IMPLEMENTED (hardware active-use is PARTIAL)."""
    summary = get_summary()
    assert summary["implemented"] < summary["total"]

def test_get_requirements_returns_list():
    reqs = get_requirements()
    assert isinstance(reqs, list)
    assert len(reqs) == len(REQUIREMENTS)

def test_cbom_requirement_present():
    ids = {r["id"] for r in REQUIREMENTS}
    assert "SIH-09" in ids

def test_mosca_requirement_present():
    ids = {r["id"] for r in REQUIREMENTS}
    assert "SIH-06" in ids

import importlib.util
from pathlib import Path


def load_daemon():
    path = Path(__file__).resolve().parents[1] / "scripts" / "atlas_swarm_daemon.py"
    spec = importlib.util.spec_from_file_location("atlas_swarm_daemon", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_swarm_gate_zero_responded_goes_failed():
    daemon = load_daemon()

    target, gate = daemon._completion_target_for_swarm_summary(
        {"perspectives_responded": 0, "evidence_gate": {"verified_findings": 3}}
    )

    assert target == daemon.FAILED
    assert gate["passed"] is False
    assert gate["reason"] == "no_perspectives_responded"


def test_swarm_gate_responded_without_verified_findings_goes_failed():
    daemon = load_daemon()

    target, gate = daemon._completion_target_for_swarm_summary(
        {"perspectives_responded": 5, "evidence_gate": {"verified_findings": 0}}
    )

    assert target == daemon.FAILED
    assert gate["passed"] is False
    assert gate["reason"] == "no_verified_findings"


def test_swarm_gate_verified_findings_goes_done():
    daemon = load_daemon()

    target, gate = daemon._completion_target_for_swarm_summary(
        {"perspectives_responded": 1, "evidence_gate": {"verified_findings": 1}}
    )

    assert target == daemon.DONE
    assert gate["passed"] is True
    assert gate["reason"] == "verified_findings_present"


def test_execute_target_requires_tracker_success():
    daemon = load_daemon()

    assert daemon._completion_target_for_execute_success(True) == daemon.DONE
    assert daemon._completion_target_for_execute_success(False) == daemon.FAILED

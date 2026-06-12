import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_production_ready.py"


def test_production_validation_script_passes_local_contracts():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--skip-network-freshness",
            "--division-id",
            "2355",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS source-lens brand" in result.stdout
    assert "PASS source dropdown" in result.stdout
    assert "PASS division map payload vote-split" in result.stdout
    assert "PASS division map payload party-split" in result.stdout
    assert "PASS division map payload gender-split" in result.stdout
    assert "PASS division map payload rebel-split" in result.stdout
    assert "PASS global feasibility UK adapter" in result.stdout
    assert "VALIDATION PASS" in result.stdout

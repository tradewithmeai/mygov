from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "update-data.yml"


def test_data_refresh_workflow_runs_update_at_3am_and_validation_after_delay():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "YourGov Data Refresh" in workflow
    assert "workflow_dispatch:" in workflow
    assert "contents: write" in workflow
    assert "0 3 * * *" in workflow
    assert "sleep 900" in workflow

    update_index = workflow.index("scripts/update_publicwhip_data.py")
    delay_index = workflow.index("sleep 900")
    validation_index = workflow.index("scripts/validate_production_ready.py")
    commit_index = workflow.index("git commit -m")

    assert update_index < delay_index < validation_index < commit_index
    assert "--skip-network-freshness" not in workflow


def test_data_refresh_workflow_commits_only_the_seed_database_after_validation():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "git add mygov.db" in workflow
    assert "git diff --quiet -- mygov.db" in workflow
    assert "chore: refresh parliamentary data" in workflow
    assert "concurrency:" in workflow

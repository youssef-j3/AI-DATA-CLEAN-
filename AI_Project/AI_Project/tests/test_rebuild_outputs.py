import os
import subprocess


def test_rebuild_creates_artifacts(tmp_path, monkeypatch):
    # run the rebuild script
    res = subprocess.run(["python", "scripts/rebuild_outputs.py"], capture_output=True, text=True)
    print(res.stdout)
    # check model artifact and explainability report
    assert os.path.exists("results/model_RandomForest.pkl")
    assert os.path.exists("results/model_explainability_report.html")

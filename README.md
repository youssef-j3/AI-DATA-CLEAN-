# Transport Analysis Project 🚍

![CI](https://github.com/<OWNER>/<REPO>/actions/workflows/ci.yml/badge.svg)

Short instructions to reproduce outputs and run tests.

## Setup

- Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Rebuild outputs 🔁

Run the provided script to clean previous outputs, run cleaning/feature engineering, train the model, and generate explainability report:

```bash
python scripts/rebuild_outputs.py
```

Outputs will be saved in the `results/` directory and `model_explainability_report.html`.

## Flags and Data Quality

- `delay_computed`: indicates the delay value was computed from parsed times.
- `delay_flagged`: indicates the computed delay was implausible and was clamped or marked for review.

Inspect `results/cleaned_transport_data.csv` and `results/engineered_transport_data.csv` for processed data.

## Tests ✅

Run the test suite with:

```bash
python -m pytest -q
```

Continuous Integration is set up via GitHub Actions in `.github/workflows/python-tests.yml`.

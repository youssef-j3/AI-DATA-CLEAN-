# Slide 1 - Summary

**Project vs Proposal — Key Differences**

- Core proposal items implemented (features, winsorization, multi-model, explainability).
- Added time-series CV, per-model temporal holdout test, and full-sample SHAP exports.
- Deliverables: final report PDF, exec summary PDF, multi-model explainability HTML.

---

# Slide 2 - Actionable Items

- Recommendation: validate on larger dataset and run temporal holdout in production.
- Next steps: causal analysis, deploy model artifact + monitoring.

---

# Slide 3 - Where to find things

- Feature engineering: `src/transport_analysis/feature_engineer.py`
- Models: `src/transport_analysis/model_builder.py`
- Explainability: `src/transport_analysis/explainer.py` and `results/model_explainability_report.html`
- Rebuild: `scripts/rebuild_outputs.py`
- Change-log: `docs/change_log.md`

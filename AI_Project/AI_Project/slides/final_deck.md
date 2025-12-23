# Slide 1 - Title

**Transport Delay Analysis**

- Author: Project
- Date: December 2025

---

# Slide 2 - Objectives

- Predict delays and understand drivers
- Implement robust pipeline and explainability

---

# Slide 3 - Data & Cleaning

- Source: dirty_transport_dataset.csv
- Key cleaning steps: timestamp parsing, delay calc, imputation

---

# Slide 4 - Feature Engineering

- Weather severity, route frequency, day_type
- Winsorization applied to `delay_minutes` and `passenger_count`

---

# Slide 5 - Modeling

- Models: RandomForest, LinearRegression
- Cross-validation performance (R²)

---

# Slide 6 - Explainability

- SHAP summaries and fallback importances
- Multi-model report: results/model_explainability_report.html

---

# Slide 7 - CV Comparison

- Cross-validation boxplot included: results/cv_comparison_boxplot.png

---

# Slide 8 - Conclusions & Next Steps

- Validate on larger data
- Temporal CV and causal analysis

---

# Slide 9 - Repro Steps

```bash
python scripts/rebuild_outputs.py
```

---

# End

*Slides are in Markdown — convert to PPTX with pandoc or present via Reveal.js.*

---

# Executive Summary

- Objective: predict transport delay and explain drivers.
- Key results: RandomForest best R²; LinearRegression useful for interpretability.
- Top predictors: scheduled time, route frequency, weather severity.
- Policy note: winsorization used to reduce extreme outlier influence (1%/99%).

Speaker notes:

- Use this slide to present 2-3 actionable recommendations: further validation on larger data, add temporal CV, and explore causal analysis.

# Model Card: Section Demand Quantile Forecaster

## 1. Model Overview

The Section Demand Forecaster provides probabilistic course enrollment forecasts for upcoming academic terms (e.g., Fall 2026, Spring 2027, Summer 2027) within the University Faculty Workload & Course Assignment Balancing System.

Rather than predicting a single point estimate, the forecaster trains three separate **LightGBM Quantile Regressors** to estimate:
- **P10 ($\alpha = 0.10$)**: Conservative scenario / lower bound (90% chance enrollment meets or exceeds this level).
- **P50 ($\alpha = 0.50$)**: Median expected demand (primary baseline for section count planning).
- **P90 ($\alpha = 0.90$)**: High-demand stress scenario (used for risk mitigation and reserve capacity).

Monotonicity ($P_{10} \le P_{50} \le P_{90}$) is strictly enforced via sorting per row at inference time. Section demand is converted via:
$$\text{n\_sections} = \lceil P_{50} / \text{section\_cap} \rceil$$
$$\text{p90\_risk\_sections} = \lceil P_{90} / \text{section\_cap} \rceil$$

---

## 2. Training Data

- **Source File**: `/data/seed/enrollment_history.json`
- **Total Records**: 360 observations (40 courses across 9 historical terms).
- **Data SHA-256**: `43fe30340ea0ee778f58e23abf9469cf2db4a8de8f9137c92cf5175d1ce7d7b9`
- **Time Split**:
  - **Train**: Terms 1 through 7 (`2023-Fall` through `2025-Fall`), 280 records.
  - **Validation**: Terms 8 and 9 (`2026-Spring` and `2026-Summer`), 80 records.
  - **Leakage Prevention**: Strictly time-ordered split. Lookback context only incorporates records with `term_index < target_term_index`.

---

## 3. Features

The model uses 10 lightweight, CPU-efficient numerical and encoded features:

| Feature Name | Type | Description |
| :--- | :--- | :--- |
| `credits` | float32 | Course credit hours (1–4) |
| `is_lab` | float32 | Binary indicator (1.0 = course includes laboratory section, 0.0 otherwise) |
| `is_elective` | float32 | Binary indicator derived from course numbering (1.0 if code $\ge$ 300, 0.0 otherwise) |
| `level_enc` | float32 | Curricular level (0 = undergraduate, 1 = graduate, 2 = doctoral) |
| `lag1_enrolled` | float32 | Enrollment count from the immediate previous term for the course (0.0 if first observed) |
| `lag2_enrolled` | float32 | Enrollment count from 2 terms prior |
| `rolling3_mean` | float32 | Moving average enrollment over the most recent 3 terms |
| `term_index_norm` | float32 | Target term index scaled by 12.0 for trend modeling |
| `season_enc` | float32 | Ordinal season encoding (Summer = 0, Spring = 1, Fall = 2) |
| `prereq_cohort_size` | float32 | Prerequisite cohort size proxy (lag-1 enrollment) |

---

## 4. Hyperparameters & Compute Budget Constraints

Complies with the system compute budget rules (strictly CPU-only, RAM budget $\le$ 512 MB):

| Parameter | Value | Rationale |
| :--- | :--- | :--- |
| Framework | LightGBM 4.7.0 | Fast, lightweight gradient boosting on CPU |
| `objective` | `quantile` | Quantile regression loss |
| `alpha` | 0.1, 0.5, 0.9 | P10, P50, and P90 models |
| `n_jobs` | 1 | Single-threaded execution for strict budget control |
| `num_leaves` | 15 | Constrained tree complexity ($\le 15$) |
| `n_estimators` | 150 | Constrained boosting iterations ($\le 300$) |
| `learning_rate` | 0.05 | Stable convergence |
| `random_state` | 42 | Deterministic, reproducible training |
| `min_child_samples` | 5 | Suited for small departmental course history |

---

## 5. Evaluation Metrics

Evaluated on held-out validation terms (`2026-Spring` and `2026-Summer`):

| Model / Baseline | MAE | RMSE | WAPE (%) | P10–P90 Interval Coverage |
| :--- | :--- | :--- | :--- | :--- |
| **LightGBM Quantile** | **4.34** | **5.98** | **11.0%** | **70.0%** |
| Seasonal Naive | 4.51 | 5.74 | — | N/A (point forecast) |
| 3-Term Moving Average | 12.05 | 14.51 | — | N/A (point forecast) |

- **MAE Improvement**: LightGBM achieves lower median error (4.34) than seasonal-naive (4.51) and significantly outperforms the 3-term moving average (12.05).
- **Interval Coverage**: 70.0% of actual enrollments fall within the predicted $[P_{10}, P_{90}]$ band on the validation set.

---

## 6. Model Artifacts

All models are serialized in human-readable native LightGBM text or JSON format (no `pickle` or `joblib`):

| Artifact File | Size | Format | Description |
| :--- | :--- | :--- | :--- |
| `ml/artifacts/forecast_p10.txt` | 228 KB | Native LightGBM text | 10th percentile model |
| `ml/artifacts/forecast_p50.txt` | 226 KB | Native LightGBM text | 50th percentile (median) model |
| `ml/artifacts/forecast_p90.txt` | 226 KB | Native LightGBM text | 90th percentile model |
| `ml/artifacts/feature_config.json` | < 1 KB | JSON | Feature names, encodings, default section capacity |
| `ml/artifacts/metrics.json` | ~ 1 KB | JSON | Evaluation metrics, data hash, library versions |
| `ml/artifacts/precomputed_forecasts.json` | 28 KB | JSON | Precomputed quantiles for Fall 2026, Spring 2027, Summer 2027 |

All files remain well under the 5 MB per-file threshold.

---

## 7. Operational Modes & Inference Pipeline

The backend server **never trains** models. It operates in two configurable modes via `FORECAST_MODE`:
1. `FORECAST_MODE=model`:
   - Loads `.txt` model boosters and computes predictions on demand.
   - Requires artifact files; returns HTTP 503 if artifacts are absent.
2. `FORECAST_MODE=precomputed` (Zero-LightGBM Low-RAM Fallback):
   - Reads `precomputed_forecasts.json` directly.
   - **Does not import `lightgbm`**, conserving RAM for 512 MB constrained deployments.

---

## 8. Retraining Workflow

To retrain the forecaster when new historical enrollment data is added:

1. **Update historical data** in `data/seed/enrollment_history.json`.
2. **Run offline training**:
   ```bash
   make train
   # or: python ml/scripts/train.py
   ```
   *(Finishes in < 1 second on CPU).*
3. **Run validation tests**:
   ```bash
   make test
   # or: pytest ml/tests backend/tests
   ```
4. **Inspect metrics**:
   Check `ml/artifacts/metrics.json` for degradation.
5. **Commit artifacts**:
   Commit the updated files in `/ml/artifacts/` alongside any schema or data modifications.

---

## 9. Limitations

- **Small Sample per Course**: Courses with few historical offerings rely primarily on course-level and credit features until more term history is accumulated.
- **Fixed Curriculum Assumption**: Newly introduced courses without historical codes receive generic lag values (0.0) and depend on category/level encodings.
- **Exogenous Shocks**: Does not model sudden changes in major degree requirements or university-wide enrollment spikes without updated history.

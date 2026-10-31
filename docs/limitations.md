# Technical Boundaries & System Limitations

This document details the intentional design trade-offs, theoretical boundaries, and operational constraints of the University Faculty Workload & Course Assignment Balancing System.

---

## 1. Storage & Persistence: GitHub Gist Constraints

The system uses private GitHub Gists as an external zero-infrastructure persistence layer (`STORE_BACKEND=gist`).

### 1.1 Single-Writer Architecture & Lack of Distributed Locks
- **Limitation**: GitHub Gists operate via standard REST API endpoints (`PATCH /gists/{gist_id}`). Gists provide neither ACID database transactions, table-level locking, nor row-level concurrency primitives.
- **System Consequence**: The backend application must run as a **single-writer service** with exactly one worker process (`--workers 1`). Concurrent writes from multiple worker processes or multiple horizontal replicas would cause split-brain revision conflicts and lost updates.
- **Mitigation**: The repository layer implements optimistic concurrency caching via GitHub revision SHA comparison. If an unexpected out-of-band edit occurs on GitHub, subsequent updates fail gracefully with concurrency warnings.

### 1.2 GitHub API Rate Limiting
- **Limitation**: GitHub enforces a strict rate limit of **5,000 authenticated requests per hour** for Personal Access Tokens (PAT).
- **System Consequence**: High-frequency polling directly to the Gist API could exhaust the quota in large multi-user environments.
- **Mitigation**: The backend repository layer implements an in-memory TTL write-through cache. Repeated read requests for faculty, course, and section definitions are served in $< 1\text{ ms}$ from memory without invoking external GitHub API calls.

### 1.3 Payload Size Thresholds
- **Limitation**: While Gist files support several megabytes, large files degrade API response times.
- **System Consequence**: Total departmental data across all active terms is targeted at $< 10\text{ MB}$. Audit logs are kept structured and periodically archived to prevent JSON bloat.

---

## 2. Demand Forecasting: Quantile Uncertainty & Data Limits

### 2.1 Small Training Sample Size
- **Limitation**: The historical training set ([`data/seed/enrollment_history.json`](file:///e:/AI%20project/data/seed/enrollment_history.json)) comprises 360 observations across 40 courses over 9 academic terms.
- **System Consequence**: Machine learning models trained on modest datasets cannot reliably capture non-linear macroeconomic shocks, sudden shifts in university-wide general education requirements, or unprecedented degree program launches.
- **Mitigation**: Rather than attempting point forecasts with false precision, the model outputs **quantile intervals ($P_{10}, P_{50}, P_{90}$)**. Planners are presented with uncertainty bands rather than single numbers.

### 2.2 Quantile Spread & Planning Trade-Offs
- **Limitation**: In small elective courses (e.g., 400-level specialty seminars), student enrollment fluctuates widely (e.g., $P_{10}=12$ vs. $P_{90}=34$).
- **System Consequence**: Basing section creation solely on $P_{90}$ risks creating under-enrolled sections that may be canceled, wasting faculty load commitments. Conversely, relying strictly on $P_{10}$ risks course waitlists and delayed student graduation.
- **Recommendation**: Department chairs should plan baseline faculty assignments using **$P_{50}$ (median)** and utilize the UI's **P90 Surge Stress Mode** to identify vulnerable bottleneck courses where adjunct capacity may be required.

---

## 3. Mathematical Optimization: Fairness Sensitivity to Weights

The Google OR-Tools CP-SAT optimizer optimizes a composite integer objective function:
$$\max \quad w_1 \sum_{(f,s)} \text{fit}_{fs} \cdot x_{fs} \;-\; w_2 \cdot \text{fairness\_penalty} \;-\; w_3 \cdot \text{pref\_miss} \;+\; w_4 \cdot \text{continuity}$$

### 3.1 Trade-Off Between Expertise Fit ($w_1$) and Workload Fairness ($w_2$)
- **Limitation**: There is no mathematically "universal" optimum that simultaneously maximizes instructor qualification and guarantees perfectly equal teaching hours across all faculty.
- **Weight Sensitivity**:
  - **High $w_1$ ($w_1 \gg w_2$)**: The solver prioritizes assigning sections to instructors with the absolute highest domain expertise. In departments with specialized professors, this produces severe workload skew (elevated Gini index), overloading star researchers while leaving generalists under-assigned.
  - **High $w_2$ ($w_2 \gg w_1$)**: The solver forces teaching hours to be strictly identical across all faculty of equal rank. To achieve this, it will assign instructors to courses where their expertise fit is mediocre, reducing overall educational quality.
- **Default Guidance**: The system defaults to balanced weights ($w_1=100, w_2=50, w_3=20, w_4=15$). Administrators can adjust these sliders interactively in the Optimizer panel based on departmental priorities.

### 3.2 Time-Limit Truncation
- **Limitation**: Under complex, heavily constrained schedules (e.g., 50+ sections with overlapping timeslot conflicts and preparation limits), integer programming is NP-hard.
- **System Consequence**: In local runs or cloud environments, the solver enforces a configurable time limit (default: **20 seconds**). While CP-SAT routinely proves optimality within 0.5s on benchmark scenarios, on extremely constrained problem instances it may return a provably feasible but sub-optimal integer solution upon time-limit expiration.

---

## 4. Compute & Hardware Budget: 512 MB RAM & CPU-Only

### 4.1 Strict Memory Envelope
- **Limitation**: The production environment operates strictly without GPU acceleration and within a **512 MB RAM budget**.
- **System Consequence**: Deep learning frameworks (PyTorch, TensorFlow), large transformer embedding models, and unconstrained distributed solvers cannot be utilized.
- **Mitigation**:
  - TF-IDF and keyword-based syllabus matching replace heavy language embeddings.
  - Setting `FORECAST_MODE=precomputed` drops LightGBM from runtime memory, reducing resident memory to $< 95\text{ MB}$.
  - OR-Tools CP-SAT is constrained to `num_workers=1`.
  - Domain pre-filtering (Step 1 in CP-SAT) eliminates invalid (faculty, section) variable combinations before integer modeling, reducing variable counts by up to 56%.

### 4.2 Background Job Single Execution
- **Limitation**: Running multiple optimization solves simultaneously would double memory usage and violate the 512 MB budget.
- **Mitigation**: The backend enforces a strict **single active optimization job policy**. Triggering `POST /api/v1/assign/run` while a solve is already executing returns HTTP `409 Conflict`.

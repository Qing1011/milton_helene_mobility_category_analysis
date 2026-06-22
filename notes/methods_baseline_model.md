# Methods — Counterfactual baseline mobility model

This documents the baseline ("business-as-usual") model used to generate the counterfactual mobility against
which hurricane disruption is measured, at both the **regional** and **local** scales. The local unit is
**Helene = cluster, Milton = county** for the primary (Milton clustering is appendix-only). The model applies
identically to Helene and Milton, to clusters and counties alike, and to the 100-mi npj package (`npj/notebook/00…`).

## 1. Role of the model

The model is a **counterfactual generator, not an explanatory model.** It is trained **only on pre-hurricane
data** to learn the normal mobility rhythm, then **forecasts what mobility would have been during the storm
window in the absence of the storm**. The hurricane's effect is read off the **deviation of observed mobility
from this forecast** — not from the model's own coefficients.

## 2. Specification

For each unit (region, or local cluster) and each flow type (within / inflow / outflow), the daily flow
$M_t$ is modelled as a **regression on calendar dummies with AR(1) errors** — the **"calendar-AR(1) baseline"**, *not* a seasonal ARIMA —
fit on the log scale:

$$\log(1+M_t)\;=\;c+\sum_{d=1}^{6}\beta_d\,\mathrm{DOW}_{d,t}+\sum_{m\in\{8,9,10\}}\gamma_m\,\mathrm{MON}_{m,t}+\delta\,\mathrm{YEAR2024}_t+\eta_t$$

$$\eta_t=\phi\,\eta_{t-1}+\varepsilon_t,\qquad \varepsilon_t\sim\mathcal N(0,\sigma^2)$$

Fit via the `statsmodels` **`SARIMAX` state-space routine** (the estimator, not the model name), with `order=(1,0,0)`, `seasonal_order=(0,0,0,0)`, `trend="c"`, with the
calendar dummies passed as exogenous regressors. **There is no seasonal, MA, or integration term** — weekly/monthly/annual
seasonality is captured by the exogenous dummies, and the only stochastic time-series dynamics is AR(1).
Predictions are back-transformed as $\hat M_t=\exp(\widehat{\log(1+M_t)})-1$.

**Exogenous design matrix `X` (10 dummies + intercept):**

| Group | Dummies | Reference (omitted) |
|---|---|---|
| Day-of-week | `dow_1`…`dow_6` | Monday (`dayofweek=0`) |
| Month | `mon08`, `mon09`, `mon10` | July |
| Year | `year_2024` | 2023 |
| (Intercept) | `trend="c"` | — |

Month dummies are hardcoded to Aug/Sep/Oct, consistent with the Jul–Oct analysis window (July is the baseline
month); the year dummy contrasts the two years of training data (2024 vs 2023).

## 3. Estimation window

Trained on **2023 Jul–Oct + 2024 Jul through 7 days before landfall** (a hurricane-adaptive training cut so no
storm-affected days enter the fit). The fitted model is then used to forecast the landing window, and the
forecast serves as the counterfactual.

## 4. Interpreting the components

Because the response is `log(1+M)`, each coefficient is approximately a **proportional effect**:
$e^{\beta}-1$ ≈ % change in mobility.

- **Intercept $c$** — log-mobility of the reference cell (a Monday in July 2023).
- **Day-of-week $\beta_d$** — each weekday relative to Monday; captures the weekly rhythm.
- **Month $\gamma_m$** — Aug/Sep/Oct level shifts vs July; within-season drift.
- **Year $\delta$** — 2024 vs 2023 overall level; year-over-year growth/decline that calibrates the 2024
  counterfactual to the correct level.
- **AR(1) $\phi$** — short-run persistence of residual deviations ($|\phi|<1$; near 1 = slow decay,
  near 0 = fast mean-reversion). A **nuisance term** that de-correlates residuals so prediction intervals are
  honest — not a scientific quantity.
- **$\sigma^2$** — residual variance; sets the width of the 95% prediction interval.

Forecast behaviour: for multi-day-ahead prediction the AR(1) contribution decays as $\phi^{h}\to0$, so a few
days into the storm window the counterfactual is essentially the calendar-regression mean, with the prediction
interval widening with horizon.

## 5. Specification rationale

- **Calendar dummies instead of a seasonal ARIMA(P,D,Q,7):** mobility seasonality is deterministic and
  calendar-driven (weekday patterns, school calendar, annual cycle), so fixed dummies capture it more stably
  and interpretably than a stochastic seasonal term, and avoid overfitting small/noisy units.
- **AR(1) errors:** daily residuals are autocorrelated; AR(1) absorbs that so coefficient standard errors and
  prediction intervals are not overconfident.
- **`log1p` transform:** mobility is positive and right-skewed; logs make effects multiplicative and stabilize
  variance; `log1p` tolerates zero-flow days.
- **`d=0`, `trend="c"`:** after removing calendar effects the series is mean-stationary, so no differencing is
  needed — the dummies supply the mean structure.

## 6. From baseline to disruption metrics

The hurricane effect is the relative deviation of observed from counterfactual:

$$rd_t=\frac{M_t-\hat M_t}{\hat M_t}\times100\%$$

- **Largest drop** — most negative $rd_t$ in the landing week $[t_\text{landing},\,t_\text{landing}+6]$
  (within & inflow).
- **Outflow surge** — most positive $rd_t$ in $[t_\text{landing}-3,\,t_\text{landing}+6]$ (evacuation window).
- **Recovery time** — days from landfall to the zero-crossing of a **Theil–Sen robust line** fit to the
  post-trough monotonic recovery segment of the smoothed $rd_t$. The trough is the most negative smoothed
  $rd_t$ within a **10-day post-landfall search window** (`trough_search_days=10`; updated 2026-06-22 from 7 —
  a 7-day window left-censored the trough of the most severely disrupted on-track units, pinning it to the
  window edge and dropping 17 Helene-inflow clusters to NaN; 10 d captures the true trough, stable across
  8–14 d). Theil–Sen is the recovery *estimator*, not the baseline model.

All scientific quantities derive from $rd_t$ (the residuals), never from the baseline coefficients.

## 7. Implementation

`notebook/recovery_function_v2.py`: `prepare_time_series_with_exog()` (builds `X`, log-transforms),
`fit_arimax_model()` (fits the calendar-AR(1) baseline via the SARIMAX routine), `get_predictions_and_ci()` (forecast + 95% CI). Baselines are fit once and
saved to CSV; metric notebooks read the saved baselines and never re-fit (see `npj/notebook/PLAN.md`,
"compute once, plot many"). Same spec used by `regional_baseline.ipynb`, `local_baseline.ipynb`, and the npj
`00`-series notebooks (`00` regional; `00d`/`00e` Helene clusters [primary]; `00b`/`00c` Milton clusters
[appendix]; Milton primary stays per-county via `milton_100mi/`), so the regional aggregate, Helene clusters, and
Milton counties are all produced identically and stay comparable.

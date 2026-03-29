#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
recovery_function_v2.py

Based on recovery_function.py by Qing Yao (qy2290@columbia.edu)

Changes from v1:
- Fixed fit_arimax_model: X_train now correctly filtered by boolean NaN mask.
  Was: X_train = X_train_0.loc[mask.index]  (returns ALL rows, not filtered)
  Now: X_train = X_train_0[mask]            (applies same boolean filter as y_train)
  This fix resolves SARIMA failures for inflow counties with zero-flow days.
"""
import pandas as pd
import numpy as np
import h5py
from datetime import datetime, timedelta
import sys

from statsmodels.tsa.statespace.sarimax import SARIMAX

from matplotlib.colors import TwoSlopeNorm, LogNorm
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates


def prepare_time_series_with_exog(flow_y, dates_all):
    """
    Prepare time series data with exogenous variables for ARIMAX modeling.

    Parameters:
    -----------
    flow_y : array-like
        Daily flow values
    dates_all : pd.DatetimeIndex
        Date index for the flow data

    Returns:
    --------
    y_log : pd.Series
        Log-transformed time series with full daily index (gaps as NaN)
    X : pd.DataFrame
        Exogenous variables (day of week, month, year dummies)
    """
    # Create raw series
    y_raw = pd.Series(flow_y, index=dates_all)
    y_raw = y_raw.sort_index()

    # Build full daily index and keep the gap as NaN (no interpolation)
    full_idx = pd.date_range(y_raw.index.min(), y_raw.index.max(), freq="D")
    y = y_raw.reindex(full_idx)
    y.index.freq = "D"

    # Exogenous dummies over the full index
    dow = pd.get_dummies(pd.Series(y.index.dayofweek, index=y.index),
                         prefix="dow", drop_first=True)
    year = pd.get_dummies(pd.Series(y.index.year, index=y.index),
                          prefix="year", drop_first=True)

    months = y.index.month
    X_month = pd.DataFrame({
        "mon08": (months == 8).astype(float),
        "mon09": (months == 9).astype(float),
        "mon10": (months == 10).astype(float),
    }, index=y.index)

    X = pd.concat([dow, X_month, year], axis=1)
    X = X.astype(float)

    # Log transform
    y_log = np.log1p(y)

    return y_log, y, X


def fit_arimax_model(y_log, X, order=(1,0,0), seasonal_order=(0,0,0,0),
                     train_2024_end="2024-08-31"):
    """
    Fit an ARIMAX model on training data from specific date ranges.

    Parameters:
    -----------
    y_log : pd.Series
        Log-transformed time series with DatetimeIndex
    X : pd.DataFrame
        Exogenous variables with DatetimeIndex
    order : tuple, optional
        ARIMA order (p, d, q). Default is (1, 0, 0)
    seasonal_order : tuple, optional
        Seasonal ARIMA order (P, D, Q, s). Default is (0, 0, 0, 0)
    train_2024_end : str, optional
        End date for the 2024 training window (inclusive).
        Default is "2024-08-31".  For Helene set this to a date
        before the hurricane impact (e.g. "2024-09-19").

    Returns:
    --------
    res : SARIMAXResultsWrapper
        Fitted SARIMAX model results
    y_train : pd.Series
        Training series used (with reset index)
    X_train : pd.DataFrame
        Training exogenous variables used (with reset index)
    """
    # Concatenate training periods
    y_train_0 = pd.concat([
        y_log.loc["2023-07-31":"2023-10-31"],
        y_log.loc["2024-07-31":train_2024_end],
    ])
    X_train_0 = pd.concat([
        X.loc["2023-07-31":"2023-10-31"],
        X.loc["2024-07-31":train_2024_end],
    ])

    # Drop any NaNs — apply same boolean mask to both y and X
    mask = ~y_train_0.isna()
    y_train = y_train_0[mask]
    X_train = X_train_0[mask]  # v2 fix: was X_train_0.loc[mask.index] in v1

    # Reset index to remove irregular DatetimeIndex
    y_train = y_train.reset_index(drop=True)
    X_train = X_train.reset_index(drop=True)

    # Fit SARIMAX model
    mdl = SARIMAX(y_train, order=order, seasonal_order=seasonal_order,
                  exog=X_train, trend="c",
                  enforce_stationarity=True, enforce_invertibility=True)
    res = mdl.fit(method="lbfgs", maxiter=1000, disp=False)

    return res, y_train, X_train


def get_predictions_and_ci(res_ci, X_ci, y_ci,
                           forecast_start="2024-09-01",
                           forecast_end="2024-10-31"):
    """
    Get predictions and confidence intervals from fitted SARIMAX model.

    Parameters:
    -----------
    res_ci : SARIMAXResultsWrapper
        Fitted SARIMAX model results
    X_ci : pd.DataFrame
        Exogenous variables for the full period
    y_ci : pd.Series
        True values for the full period
    forecast_start : str, optional
        Start date for the forecast window. Default is "2024-09-01".
    forecast_end : str, optional
        End date for the forecast window. Default is "2024-10-31".

    Returns:
    --------
    df_rec : pd.DataFrame
        DataFrame containing true values, predicted values, and confidence intervals
    """
    forecast_idx = pd.date_range(forecast_start, forecast_end, freq="D")
    X_future = X_ci.loc[forecast_idx].reset_index(drop=True)
    fc = res_ci.get_forecast(steps=len(X_future), exog=X_future)

    # back-transform from log
    y_pred = np.expm1(fc.predicted_mean)
    y_pred = pd.Series(y_pred.values, index=forecast_idx)  # reattach real dates
    ci = fc.conf_int()
    ci = np.expm1(ci)
    lower = pd.Series(ci.iloc[:,0].values, index=forecast_idx)
    upper = pd.Series(ci.iloc[:,1].values, index=forecast_idx)

    y_true = y_ci.reindex(forecast_idx)
    df_rec = pd.DataFrame({
        "y_true": y_true,
        "y_pred": y_pred,
        "ci_lower": lower,
        "ci_upper": upper,
    }, index=forecast_idx).dropna()  # drop days where y_true is missing
    return df_rec, forecast_idx




def recovery_time_from_largest_drop(
    df: pd.DataFrame,
    *,
    y_col="y_true",
    yhat_col="y_pred",
    lower_col="ci_lower",
    upper_col="ci_upper",
    k=3,
    delta=0.05,
    side: str = "two_sided",  # "two_sided" | "lower" | "upper"
    landing_date = None
):
    """
    Recovery time starting from the largest drop (most negative relative deviation).

    side controls BOTH:
      1) CI rule:
         - two_sided:  lower <= y <= upper
         - lower:      y >= lower   (recovery from drops; allows overshoot)
         - upper:      y <= upper   (recovery from spikes; allows undershoot)
      2) Practical deviation rule on rel_dev = (y - yhat)/yhat:
         - two_sided:  |rel_dev| <= delta
         - lower:      rel_dev >= -delta
         - upper:      rel_dev <= +delta
    """
    d = df.copy()

    # Ensure datetime index
    if "date" in d.columns and not isinstance(d.index, pd.DatetimeIndex):
        d["date"] = pd.to_datetime(d["date"])
        d = d.set_index("date")
    if not isinstance(d.index, pd.DatetimeIndex):
        raise ValueError("df must have a DatetimeIndex or a 'date' column.")
    d = d.sort_index()

    y = d[y_col].astype(float)
    yhat = d[yhat_col].astype(float)
    # Relative deviation
    eps = 1e-12 ## sometimes the predicted value can be zero
    denom = yhat.replace(0, np.nan) + eps
        # Calculate relative difference: (true - predicted) / predicted * 100
    relative_diff = (y - yhat) / denom * 100
    # Calculate relative uncertainty bounds
    relative_lower = (d[lower_col] - yhat) / denom * 100
    relative_upper = (d[upper_col] - yhat) / denom * 100

    d["rel_dev"] = relative_diff

    # Trough = largest drop (most negative deviation)
    # trough_date = d["rel_dev"].idxmin()
    if landing_date is not None:
        trough_date = landing_date
    else:
        trough_date = d["rel_dev"].idxmin()

    # Post-trough period
    post = d.loc[d.index >= trough_date].copy() #the largest drop date's index is zero

    # CI rule
    if side == "two_sided":
        post["in_ci"] = (post[y_col] >= post[lower_col]) & (post[y_col] <= post[upper_col])
    elif side == "lower":
        post["in_ci"] = post[y_col] >= post[lower_col]
    elif side == "upper":
        post["in_ci"] = post[y_col] <= post[upper_col]
    else:
        raise ValueError("side must be one of: 'two_sided', 'lower', 'upper'")

    # Practical deviation rule (one-sided if side is one-sided)
    if side == "two_sided":
        post["in_delta"] = post["rel_dev"].abs() <= float(delta*100)
    elif side == "lower":
        post["in_delta"] = post["rel_dev"] >= -float(delta*100)
    else:  # side == "upper"
        post["in_delta"] = post["rel_dev"] <= float(delta*100)
    # Recovery flag
    post["recovered_flag"] = post["in_ci"] & post["in_delta"]

    # Find first k-day sustained recovery
    flags = post["recovered_flag"].fillna(False).to_numpy(dtype=int)
    if len(flags) < k:
        return {
            "trough_date": trough_date,
            "recovery_date": None,
            "recovery_days": None,
            "reason": "Insufficient data after trough.",
        }

    window_sum = np.convolve(flags, np.ones(k, dtype=int), mode="valid")
    idx = np.where(window_sum == k)[0] ## this gives the starting index of the k-day sustained recovery

    if idx.size == 0:
        return {
            "trough_date": trough_date,
            "recovery_date": None,
            "recovery_days": None,
            "reason": f"No {k}-day sustained recovery found (side={side}, delta={delta}).",
            "relative_diff": relative_diff,
            "relative_lower": relative_lower,
            "relative_upper": relative_upper
        }

    recovery_date = post.index[idx[0]]
    recovery_days = (recovery_date.normalize() - trough_date.normalize()).days

    return {
        "trough_date": trough_date,
        "recovery_date": recovery_date,
        "recovery_days": int(recovery_days),
        "k": int(k),
        "delta": float(delta),
        "side": side,
        "diagnostics": post,
        "relative_diff": relative_diff,
        "relative_lower": relative_lower,
        "relative_upper": relative_upper
    }


def plot_relative_difference(h,result_df,forecast_idx,f_path,i):
    """
    Plot relative difference with uncertainty bands and recovery annotations.

    Parameters:
    -----------
    forecast_idx : pd.DatetimeIndex
        Date index for the forecast period
    relative_diff : pd.Series
        Relative difference series
    relative_lower : pd.Series
        Lower bound of relative difference CI
    relative_upper : pd.Series
        Upper bound of relative difference CI
    recovery_date : pd.Timestamp, optional
        Date of recovery (if any)
    recovery_days : int, optional
        Number of days to recovery (if any)
    """
    trough_date = result_df["trough_date"]
    recovery_date = result_df["recovery_date"]
    recovery_days = result_df["recovery_days"]
    relative_diff = result_df["relative_diff"]
    relative_lower = result_df["relative_lower"]
    relative_upper = result_df["relative_upper"]
    plt.figure(figsize=(12, 5))
    # Plot relative difference
    plt.plot(forecast_idx, relative_diff.values, label="Relative difference (True - Pred)",
            color="black", linewidth=2)
    # Plot zero line
    plt.axhline(0, color="gray", linestyle="--", linewidth=1, alpha=0.7)
    plt.axhline(5, color="red", linestyle="--", linewidth=2, alpha=0.7)
    plt.axhline(-5, color="red", linestyle="--", linewidth=2, alpha=0.7)

    # Fill uncertainty band
    plt.fill_between(forecast_idx, relative_lower, relative_upper,
                    color="red", alpha=0.15, label="95% CI (relative)")

    # Highlight Milton landing date
    if h == 'milton':
        special_date = pd.Timestamp("2024-10-09")
    else:
        special_date = pd.Timestamp("2024-09-26")
    plt.axvline(special_date, color="blue", linestyle="--", linewidth=1.5,
                label="2024-10-09; Milton Landing date")
    # Mark trough date
    plt.axvline(
        trough_date,
        color="orange",
        linestyle="--",
        linewidth=2,
        label="Trough date"
    )
    # Mark recovery date
    if recovery_date is not None:
        plt.axvline(
            recovery_date,
            color="green",
            linestyle="--",
            linewidth=2,
            label=f"Recovery date ({recovery_days} days)"
        )

        # Annotate
        plt.text(
            recovery_date,
            plt.ylim()[1] * 0.9,
            f"Recovery\n{recovery_days} days",
            color="green",
            ha="left",
            va="top",
            fontsize=10,
            rotation=90
        )

    plt.title("Relative Difference: (True - Predicted) / Predicted (%)")
    plt.xlabel("Date")
    plt.ylabel("Relative Difference (%)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{f_path}/relative_difference_plot_c-{i}.png", dpi=300)
    # plt.show()

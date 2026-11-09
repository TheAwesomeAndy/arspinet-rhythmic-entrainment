#!/usr/bin/env python3
"""Minimal forward mTRF (ridge regression over time lags) with leave-one-trial-out CV.

fit_trf(X_list, Y_list, fs, tmin, tmax, lam): X_list[i] is (T_i, n_feat), Y_list[i] is (T_i, n_ch).
Returns weights W of shape (n_lags*n_feat + 1, n_ch) (last row = bias).
predict(W, X, ...) -> (T, n_ch).
loo_prediction_r(...) -> per-trial, per-channel Pearson r between held-out EEG and prediction.
"""
import numpy as np


def lag_matrix(X, fs, tmin, tmax):
    lags = np.arange(int(round(tmin * fs)), int(round(tmax * fs)) + 1)
    T, F = X.shape
    out = np.zeros((T, len(lags) * F))
    for k, L in enumerate(lags):
        if L >= 0:
            out[L:, k * F:(k + 1) * F] = X[:T - L]
        else:
            out[:T + L, k * F:(k + 1) * F] = X[-L:]
    return out, lags


def _xtx_xty(X_list, Y_list, fs, tmin, tmax):
    XtX = None; XtY = None
    for X, Y in zip(X_list, Y_list):
        Xl, lags = lag_matrix(X, fs, tmin, tmax)
        Xl = np.hstack([Xl, np.ones((len(Xl), 1))])
        XtX = Xl.T @ Xl if XtX is None else XtX + Xl.T @ Xl
        XtY = Xl.T @ Y if XtY is None else XtY + Xl.T @ Y
    return XtX, XtY, lags


def fit_trf(X_list, Y_list, fs, tmin=0.0, tmax=0.4, lam=1.0):
    XtX, XtY, lags = _xtx_xty(X_list, Y_list, fs, tmin, tmax)
    n = XtX.shape[0]
    reg = lam * np.trace(XtX) / n * np.eye(n); reg[-1, -1] = 0.0
    W = np.linalg.solve(XtX + reg, XtY)
    return W, lags


def predict(W, X, fs, tmin=0.0, tmax=0.4):
    Xl, _ = lag_matrix(X, fs, tmin, tmax)
    return np.hstack([Xl, np.ones((len(Xl), 1))]) @ W


def loo_prediction_r(X_list, Y_list, fs, tmin=0.0, tmax=0.4, lam=1.0):
    """Leave-one-trial-out prediction correlation, (n_trials, n_ch)."""
    XtX, XtY, lags = _xtx_xty(X_list, Y_list, fs, tmin, tmax)
    n = XtX.shape[0]
    r = np.zeros((len(X_list), Y_list[0].shape[1]))
    for i, (X, Y) in enumerate(zip(X_list, Y_list)):
        Xl, _ = lag_matrix(X, fs, tmin, tmax); Xl = np.hstack([Xl, np.ones((len(Xl), 1))])
        A = XtX - Xl.T @ Xl; B = XtY - Xl.T @ Y
        reg = lam * np.trace(A) / n * np.eye(n); reg[-1, -1] = 0.0
        W = np.linalg.solve(A + reg, B)
        P = Xl @ W
        Pc = P - P.mean(0); Yc = Y - Y.mean(0)
        r[i] = (Pc * Yc).sum(0) / (np.sqrt((Pc ** 2).sum(0) * (Yc ** 2).sum(0)) + 1e-12)
    return r, lags

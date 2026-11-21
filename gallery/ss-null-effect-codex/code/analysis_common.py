"""Fixed parametric ATT implementation. No import-time data reads."""
import csv
import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import statsmodels.api as sm
from scipy.special import expit
from scipy.stats import norm
from statsmodels.tools.sm_exceptions import PerfectSeparationWarning

SEED = 19781979
B = 499
EXPECTED_SHA = 'f09fba8695df8d2cfe44abe770860772f07a562ad88c19789f6feab946048ca9'
REQUIRED = 'id treat age educ married urban region children health_limit re74 re75 unemp74 unemp75 re78'.split()
INDICATORS = 'treat married urban health_limit unemp74 unemp75'.split()
REGIONS = ['midwest', 'northeast', 'south', 'west']
FEATURES = 'age educ married urban children health_limit re74 re75 unemp74 unemp75'.split()


def load_data(path, schema_path, include_outcome=True):
    """Hash opaque file bytes, then parse only authorized prefix columns.

    include_outcome=False never converts or inspects re78 values. It still reads
    byte strings to hash the file and split off the required prefix.
    """
    path = Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != EXPECTED_SHA:
        raise ValueError('Raw data hash mismatch; no automatic repair')
    schema = json.loads(Path(schema_path).read_text())
    if schema['observed_region_labels'] != REGIONS:
        raise ValueError('Encoding schema changed; prospective clarification required')
    wanted = REQUIRED if include_outcome else REQUIRED[:-1]
    result = {k: [] for k in wanted}
    with path.open(newline='', encoding='utf-8') as handle:
        header = next(csv.reader([next(handle)]))
        if header[:14] != REQUIRED:
            raise ValueError('Required-field schema changed')
        for line in handle:
            # Required prefix contains no quoted commas in the pinned source.
            values = next(csv.reader([','.join(line.split(',', 14)[:len(wanted)])]))
            if len(values) != len(wanted):
                raise ValueError('Malformed authorized prefix')
            for key, value in zip(wanted, values):
                if not value.strip():
                    raise ValueError('Missing required field')
                result[key].append(value if key in ('id', 'region') else float(value))
    result = {k: np.asarray(v) for k, v in result.items()}
    if len(result['id']) != 4000 or len(set(result['id'])) != 4000:
        raise ValueError('Unexpected cohort size or duplicate id')
    for key in wanted:
        if key not in ('id', 'region') and not np.isfinite(result[key]).all():
            raise ValueError('Nonfinite required field')
        if key in INDICATORS and not np.isin(result[key], [0, 1]).all():
            raise ValueError('Nonbinary indicator')
    if not np.isin(result['region'], REGIONS).all():
        raise ValueError('Region outside fixed observed encoding vocabulary')
    return result


def features(data, placebo=False):
    names = [k for k in FEATURES if not placebo or k not in ('re75', 'unemp75')]
    columns = [np.ones(len(data['treat']))]
    for key in names:
        columns.append(data[key] / 1000 if key in ('re74', 're75') else data[key])
    names = ['intercept'] + names
    for region in REGIONS[1:]:
        columns.append((data['region'] == region).astype(float))
        names.append('region_' + region)
    return np.column_stack(columns), names


def full_rank(x):
    if np.linalg.matrix_rank(x) != x.shape[1]:
        raise ValueError('Rank deficient design matrix')


def propensity(x, d):
    full_rank(x)
    if len(np.unique(d)) != 2:
        raise ValueError('Both treatment groups required')
    with warnings.catch_warnings():
        warnings.simplefilter('error', PerfectSeparationWarning)
        fit = sm.Logit(d, x).fit(method='newton', maxiter=2000, tol=1e-8, disp=False)
    if not fit.mle_retvals.get('converged', False) or not np.isfinite(fit.params).all():
        raise ValueError('Propensity MLE did not converge')
    e = expit(x @ fit.params)
    if not np.isfinite(e).all() or np.any(e <= 0) or np.any(e >= 1):
        raise ValueError('Propensity outside open unit interval')
    odds = e / (1 - e)
    if not np.isfinite(odds).all():
        raise ValueError('Nonfinite odds')
    return e, odds


def att_once(x, d, y, cap=None):
    _, odds = propensity(x, d)
    full_rank(x[d == 0])
    fit = sm.OLS(y[d == 0], x[d == 0]).fit()
    if not np.isfinite(fit.params).all():
        raise ValueError('Nonfinite control OLS')
    residual = y - x @ fit.params
    weights = odds if cap is None else np.minimum(odds, cap)
    tau = np.sum(d * residual - (1 - d) * weights * residual) / d.sum()
    if not np.isfinite(tau):
        raise ValueError('Nonfinite ATT')
    return float(tau)


def inference(tau, se):
    if not np.isfinite(se) or se <= 0:
        raise ValueError('Nonpositive or nonfinite standard error')
    return {'estimate': float(tau), 'se': float(se),
            'ci95_low': float(tau - 1.95996398454 * se),
            'ci95_high': float(tau + 1.95996398454 * se),
            'ci90_low': float(tau - 1.64485362695 * se),
            'ci90_high': float(tau + 1.64485362695 * se),
            'p_zero': float(2 * norm.sf(abs(tau / se)))}


def bootstrap_att(x, d, y, cap=None):
    tau = att_once(x, d, y, cap)
    rng = np.random.Generator(np.random.PCG64(SEED))
    values, failures = [], {}
    for _ in range(B):
        idx = rng.integers(0, len(d), size=len(d))
        try:
            values.append(att_once(x[idx], d[idx], y[idx], cap))
        except (ValueError, np.linalg.LinAlgError, PerfectSeparationWarning) as exc:
            name = type(exc).__name__
            failures[name] = failures.get(name, 0) + 1
    metrics = {'estimate': tau, 'n': len(d), 'n_treated': int(d.sum()),
               'bootstrap_requested': B, 'bootstrap_valid': len(values),
               'bootstrap_failed': B - len(values), 'seed': SEED,
               'fit_ok': 0, 'failure_reason': ''}
    for key, count in failures.items():
        metrics['bootstrap_failure_' + key] = count
    if len(values) < 490:
        metrics['failure_reason'] = 'Fewer than 490 valid bootstrap estimates'
        return metrics
    se = float(np.std(values, ddof=1))
    try:
        metrics.update(inference(tau, se))
    except ValueError as exc:
        metrics['failure_reason'] = str(exc)
        return metrics
    metrics['fit_ok'] = 1
    return metrics


def write_metrics(path, metrics):
    """Flat, finite JSON; absent estimates are omitted, never NaN substitutes."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, indent=2, allow_nan=False) + '\n')


def read_metrics(path):
    return json.loads(Path(path).read_text())


def data_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--schema', required=True)
    parser.add_argument('--metrics', required=True)
    return parser.parse_args()


def run_att(placebo=False, cap=None):
    args = data_args()
    data = load_data(args.data, args.schema, include_outcome=not placebo)
    x, _ = features(data, placebo)
    try:
        metrics = bootstrap_att(x, data['treat'], data['re75' if placebo else 're78'], cap)
    except (ValueError, np.linalg.LinAlgError, PerfectSeparationWarning) as exc:
        metrics = {'fit_ok': 0, 'failure_reason': str(exc), 'n': len(x),
                   'bootstrap_requested': B, 'bootstrap_valid': 0, 'bootstrap_failed': 0,
                   'bootstrap_not_attempted': B, 'seed': SEED}
    if metrics['fit_ok'] and not placebo and cap is None:
        tau, se = metrics['estimate'], metrics['se']
        metrics['p_tost'] = float(max(norm.sf((tau + 1000) / se), norm.cdf((tau - 1000) / se)))
    write_metrics(args.metrics, metrics)

import numpy as np
from statsmodels.tools.sm_exceptions import PerfectSeparationWarning
from analysis_common import data_args, load_data, features, propensity, write_metrics

if __name__ == '__main__':
    args = data_args()
    data = load_data(args.data, args.schema, include_outcome=False)
    x, names = features(data)
    d = data['treat']
    try:
        e, odds = propensity(x, d)
        w = odds[d == 0]
        metrics = {'fit_ok': 1, 'n': len(d), 'n_treated': int(d.sum())}
        for group in [0, 1]:
            for label, q in [('min', 0), ('p01', .01), ('p05', .05), ('p25', .25), ('p50', .5), ('p75', .75), ('p95', .95), ('p99', .99), ('max', 1)]:
                metrics[f'propensity_d{group}_{label}'] = float(np.quantile(e[d == group], q))
        metrics['control_max_odds'] = float(w.max())
        metrics['control_ess'] = float(w.sum() ** 2 / (w @ w))
        metrics['treated_fraction_above_095'] = float(np.mean(e[d == 1] > .95))
        outside = (e[d == 1] < e[d == 0].min()) | (e[d == 1] > e[d == 0].max())
        metrics['treated_fraction_outside_control_range'] = float(np.mean(outside))
        max_smd = 0.
        for j, name in enumerate(names):
            a, b = x[d == 1, j], x[d == 0, j]
            # Unweighted pooled sample SD: sqrt((s1^2+s0^2)/2).
            denominator = np.sqrt((np.var(a, ddof=1) + np.var(b, ddof=1)) / 2)
            raw_difference, weighted_difference = a.mean() - b.mean(), a.mean() - np.average(b, weights=w)
            if denominator == 0:
                if raw_difference != 0 or weighted_difference != 0:
                    raise ValueError('Undefined SMD for zero-variance feature')
                raw, weighted = 0., 0.
            else:
                raw, weighted = raw_difference / denominator, weighted_difference / denominator
            metrics['smd_raw_' + name] = float(raw)
            metrics['smd_weighted_' + name] = float(weighted)
            max_smd = max(max_smd, abs(weighted))
        metrics['flag_outside_range'] = int(outside.any())
        metrics['flag_high_propensity'] = int(metrics['treated_fraction_above_095'] > .05)
        metrics['flag_low_ess'] = int(metrics['control_ess'] < 100)
        metrics['flag_imbalance'] = int(max_smd > .10)
        metrics['support_inadequate'] = int(any(metrics[k] for k in ['flag_outside_range', 'flag_high_propensity', 'flag_low_ess', 'flag_imbalance']))
    except (ValueError, np.linalg.LinAlgError, PerfectSeparationWarning) as exc:
        metrics = {'fit_ok': 0, 'support_inadequate': 1, 'failure_reason': str(exc)}
    write_metrics(args.metrics, metrics)

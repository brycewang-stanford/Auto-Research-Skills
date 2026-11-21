import argparse
import numpy as np
from scipy.stats import norm
from analysis_common import load_data, read_metrics, write_metrics


def holm(pvalues):
    names = list(pvalues)
    order = sorted(names, key=lambda k: pvalues[k])
    result, previous = {}, 0.
    for j, key in enumerate(order):
        previous = max(previous, min(1., (len(names) - j) * pvalues[key]))
        result[key] = previous
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for key in ['main', 'ols', 'cap', 'placebo', 'support', 'precision', 'bias', 'data', 'schema', 'metrics']:
        parser.add_argument('--' + key, required=True)
    args = parser.parse_args()
    results = {k: read_metrics(getattr(args, k)) for k in ['main', 'ols', 'cap', 'placebo']}
    support = read_metrics(args.support)
    # Require successful ledger-produced prerequisite outputs, including no-test runs.
    read_metrics(args.precision)
    read_metrics(args.bias)
    pvalues = {key: value['p_zero'] if value['fit_ok'] else 1. for key, value in results.items()}
    pvalues['tost'] = results['main']['p_tost'] if results['main']['fit_ok'] else 1.
    adjusted = holm(pvalues)
    metrics = {'family_size': 5}
    for key in pvalues:
        metrics[key + '_p_raw'] = pvalues[key]
        metrics[key + '_p_holm'] = adjusted[key]
        metrics[key + '_reject_holm'] = int(adjusted[key] <= .05)
    for key, value in results.items():
        metrics[key + '_fit_ok'] = value['fit_ok']
        if value['fit_ok']:
            for field in ['estimate', 'se', 'ci95_low', 'ci95_high']:
                metrics[key + '_' + field] = value[field]
            metrics[key + '_ci99_low'] = value['estimate'] - norm.ppf(.995) * value['se']
            metrics[key + '_ci99_high'] = value['estimate'] + norm.ppf(.995) * value['se']
    main = results['main']
    permitted = bool(main['fit_ok'] and support['fit_ok'] and not support['support_inadequate'])
    metrics['affirmative_causal_interpretation_permitted'] = int(permitted)
    metrics['support_inadequate'] = support['support_inadequate']
    metrics['h1_supported'] = int(permitted and main.get('ci95_low', -np.inf) > 0 and adjusted['main'] <= .05)
    metrics['h1_interval_below_zero'] = int(main['fit_ok'] and main['ci95_high'] < 0)
    metrics['h1_interval_spans_zero'] = int(main['fit_ok'] and main['ci95_low'] <= 0 <= main['ci95_high'])
    metrics['h2_supported'] = int(permitted and main.get('ci90_low', -np.inf) > -1000 and main.get('ci90_high', np.inf) < 1000 and adjusted['tost'] <= .05)
    if main['fit_ok']:
        metrics['main_ci98_low'] = main['estimate'] - norm.ppf(.99) * main['se']
        metrics['main_ci98_high'] = main['estimate'] + norm.ppf(.99) * main['se']
    data = load_data(args.data, args.schema)
    control = data['re78'][data['treat'] == 0]
    metrics['control_re78_mean'] = float(control.mean())
    metrics['control_re78_sd'] = float(control.std(ddof=1))
    for label in ['mean', 'sd']:
        baseline = metrics['control_re78_' + label]
        defined = bool(main['fit_ok'] and baseline != 0)
        metrics['att_relative_control_' + label + '_defined'] = int(defined)
        if defined:
            metrics['att_relative_control_' + label] = main['estimate'] / baseline
    write_metrics(args.metrics, metrics)

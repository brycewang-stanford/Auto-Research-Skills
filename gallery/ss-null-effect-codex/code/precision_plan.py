import numpy as np
from scipy.stats import norm
from analysis_common import data_args, load_data, write_metrics

if __name__ == '__main__':
    args = data_args()
    data = load_data(args.data, args.schema, include_outcome=False)
    metrics = {'hypothetical_n1': 1600, 'hypothetical_n0': 2400, 'benchmark': 1000}
    for sigma in [2000, 5000, 10000]:
        for vif in [1, 2, 4]:
            prefix = f'sd{sigma}_vif{vif}_'
            se = sigma * np.sqrt(vif * (1 / 1600 + 1 / 2400))
            values = {'se': se, 'mde80_raw': (1.959964 + .841621) * se,
                      'mde80_five_test': (2.575829 + .841621) * se,
                      'halfwidth95': 1.95996398454 * se,
                      'power_equivalence_raw': max(0., 2 * norm.cdf(1000 / se - 1.644854) - 1),
                      'power_equivalence_bonferroni': max(0., 2 * norm.cdf(1000 / se - 2.326348) - 1),
                      'centered_ci90_fits': int(1.64485362695 * se < 1000),
                      'centered_ci98_fits': int(norm.ppf(.99) * se < 1000),
                      'centered_ci95_fits': int(1.95996398454 * se < 1000)}
            metrics.update({prefix + key: float(value) for key, value in values.items()})
    for key in ['re74', 're75']:
        values = data[key]
        metrics[key + '_mean'] = float(values.mean())
        metrics[key + '_sd'] = float(values.std(ddof=1))
        for label, q in [('min', 0), ('p25', .25), ('median', .5), ('p75', .75), ('max', 1)]:
            metrics[key + '_' + label] = float(np.quantile(values, q))
    write_metrics(args.metrics, metrics)

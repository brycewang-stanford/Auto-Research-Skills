import numpy as np
import statsmodels.api as sm
from analysis_common import data_args, load_data, features, full_rank, inference, write_metrics

if __name__ == '__main__':
    args = data_args()
    data = load_data(args.data, args.schema)
    x, _ = features(data)
    design = np.column_stack([x, data['treat']])
    try:
        full_rank(design)
        fit = sm.OLS(data['re78'], design).fit(cov_type='HC3', use_t=False)
        metrics = inference(fit.params[-1], fit.bse[-1])
        metrics.update(fit_ok=1, n=len(x), failure_reason='')
    except (ValueError, np.linalg.LinAlgError) as exc:
        metrics = {'fit_ok': 0, 'n': len(x), 'failure_reason': str(exc)}
    write_metrics(args.metrics, metrics)

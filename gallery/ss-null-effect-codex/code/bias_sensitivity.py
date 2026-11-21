import argparse
from analysis_common import read_metrics, write_metrics

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--main', required=True)
    parser.add_argument('--metrics', required=True)
    args = parser.parse_args()
    main = read_metrics(args.main)
    metrics = {'available': int(bool(main['fit_ok']))}
    if main['fit_ok']:
        for bias in [-2000, -1000, -500, 0, 500, 1000, 2000]:
            label = 'bias_' + ('minus' + str(-bias) if bias < 0 else str(bias))
            for key in ['estimate', 'ci95_low', 'ci95_high']:
                metrics[label + '_' + key] = main[key] - bias
        # Signed b at which estimate or an interval endpoint reaches each boundary.
        for key in ['estimate', 'ci95_low', 'ci95_high']:
            for name, boundary in [('zero', 0), ('lower_benchmark', -1000), ('upper_benchmark', 1000)]:
                metrics[key + '_bias_to_' + name] = main[key] - boundary
    write_metrics(args.metrics, metrics)

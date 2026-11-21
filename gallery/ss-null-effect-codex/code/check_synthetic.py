"""Memory-only artificial inputs. Never opens the supplied cohort."""
import unittest
import numpy as np
from scipy.special import expit
from analysis_common import att_once, bootstrap_att, full_rank, inference
from decision_report import holm


class SyntheticChecks(unittest.TestCase):
    def test_exact_linear_counterfactual(self):
        rng = np.random.Generator(np.random.PCG64(391))
        z = rng.normal(size=(600, 3))
        x = np.column_stack([np.ones(600), z])
        d = rng.binomial(1, expit(.2 + z[:, 0] * .3))
        y = x @ np.array([50., 4., -3., 2.]) + 275. * d
        self.assertAlmostEqual(att_once(x, d, y), 275., places=8)
        self.assertAlmostEqual(att_once(x, d, y, cap=10), 275., places=8)
        # Noiseless counterfactual checks the estimating equation, not uncertainty.

    def test_full_bootstrap_is_deterministic(self):
        rng = np.random.Generator(np.random.PCG64(392))
        x = np.column_stack([np.ones(350), rng.normal(size=(350, 2))])
        d = rng.binomial(1, .4, 350)
        y = x @ np.array([20., 3., -1.]) + 25. * d + rng.normal(size=350)
        first = bootstrap_att(x, d, y)
        self.assertEqual(first, bootstrap_att(x, d, y))
        self.assertEqual(first['bootstrap_valid'], 499)
        self.assertEqual(first['fit_ok'], 1)
        self.assertGreater(first['se'], 0)

    def test_rank_and_invalid_uncertainty_stop(self):
        with self.assertRaises(ValueError):
            full_rank(np.ones((10, 2)))
        with self.assertRaises(ValueError):
            inference(1., 0.)

    def test_holm_fixed_family(self):
        actual = holm(dict(a=.001, b=.02, c=.04, d=.5, e=1.))
        self.assertEqual(actual, dict(a=.005, b=.08, c=.12, d=1., e=1.))


if __name__ == '__main__':
    unittest.main()

import copy

import numpy as np
import pandas as pd
import pytest

from credit_platform.risk import validated_lgd_prediction
from lgd_research.generate_r2 import DEPLOYABLE, generate
from research_diagnostics.lgd_conditional.diagnostic import conditional_mean, outcomes


class Stub:
    def __init__(self, result):
        self.result = result

    def predict(self, features):
        return self.result


@pytest.mark.parametrize('result', [[np.inf], [-np.inf], [np.nan], [], [0.2, 0.3], [[0.2]]])
def test_lgd_rejects_corrupt_and_incomplete_outputs(result):
    with pytest.raises(ValueError, match='one finite prediction'):
        validated_lgd_prediction(Stub(result), pd.DataFrame({'feature': [1]}))


def test_lgd_preserves_approved_finite_clipping():
    np.testing.assert_array_equal(
        validated_lgd_prediction(Stub([-.1, .35, 1.1]), pd.DataFrame({'x': [1, 2, 3]})),
        [0, .35, 1],
    )


def test_conditional_equations_independently_replay_original_generator(monkeypatch):
    factory = np.random.default_rng
    states = []

    class Capture:
        def __init__(self, seed):
            self.rng = factory(seed)

        def normal(self, *args, **kwargs):
            # First .16-scale normal is the boundary between known inputs and outcomes.
            if len(args) >= 2 and args[0] == 0 and args[1] == .16 and not states:
                states.append(copy.deepcopy(self.rng.bit_generator.state))
            return self.rng.normal(*args, **kwargs)

        def __getattr__(self, name):
            return getattr(self.rng, name)

    with monkeypatch.context() as m:
        m.setattr(np.random, 'default_rng', Capture)
        original = generate(1000, 1729, 'independent-check')
    rng = factory()
    rng.bit_generator.state = states[0]
    replay = outcomes(original[DEPLOYABLE], rng)
    np.testing.assert_allclose(replay, original.economic_lgd, rtol=0, atol=1e-14)
    assert set(original.collateral_type) == {'Unsecured', 'Cash', 'Mortgage', 'Other'}
    assert set(original.cure_flag) == {0, 1}


def test_conditional_diagnostic_cannot_use_outcomes_and_is_reproducible():
    data = generate(12, 32, 'test')
    mean, se = conditional_mean(data[DEPLOYABLE], draws=64, seed=17)
    poisoned = data.copy()
    for col in set(data)-set(DEPLOYABLE):
        poisoned[col] = 'PROHIBITED FUTURE INFORMATION'
    repeated, repeated_se = conditional_mean(poisoned, draws=64, seed=17)
    np.testing.assert_array_equal(mean, repeated)
    np.testing.assert_array_equal(se, repeated_se)
    assert ((0 <= mean) & (mean <= 1)).all()
    assert (se > 0).all()

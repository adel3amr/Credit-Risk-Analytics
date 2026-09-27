"""S2 prediction-time economic contract, history and governed scenario mapping."""
import numpy as np
import pandas as pd

VERSION = 's2-economics-1'
MACRO = ['output_growth_pct', 'unemployment_pct', 'collateral_change_pct', 'liquidity']
RANGES = dict(output_growth_pct=(-10, 8), unemployment_pct=(2, 20),
              collateral_change_pct=(-35, 25), liquidity=(.05, 1))


def history(industries, start, seed, current=False):
    rng = np.random.default_rng(seed)
    rows = []
    # A shared quarter shock and persistent sector states create clustered risk.
    dates = pd.date_range(start, periods=12, freq='QS') if not current else pd.to_datetime([start])
    states = {sector: int(rng.random() < (.8 if current else .35)) for sector in industries}
    for date in dates:
        shared = rng.normal(0, .6)
        for sector in sorted(industries):
            if not current and rng.random() < .25:
                states[sector] = 1 - states[sector]
            d = states[sector]
            activity = np.clip(2 - 3.5*d + shared + rng.normal(0, .8), -10, 8)
            unemployment = np.clip(5.5 + 1.7*d - .2*activity + rng.normal(0, .7), 2, 20)
            price = np.clip(1.6*activity - 2*d + rng.normal(0, 4), -35, 25)
            liquidity = np.clip(.8 + .025*activity - .2*d + rng.normal(0, .08), .05, 1)
            rows.append(dict(industry=sector, reporting_date=date.date().isoformat(),
                economic_period=(date-pd.Timedelta(days=90)).date().isoformat(),
                published_at=(date-pd.Timedelta(days=1)).date().isoformat(),
                output_growth_pct=activity, unemployment_pct=unemployment,
                collateral_change_pct=price, liquidity=liquidity,
                latent_regime=d, economic_version=VERSION))
    return pd.DataFrame(rows)


def validate(frame):
    required = MACRO + ['reporting_date', 'economic_period', 'published_at', 'economic_version']
    if set(required) - set(frame):
        raise ValueError('Missing economic contract fields')
    for field, (lo, hi) in RANGES.items():
        values = frame[field].to_numpy(dtype=float)
        if not np.isfinite(values).all() or ((values < lo) | (values > hi)).any():
            raise ValueError('Invalid economic input: ' + field)
    if not frame.economic_version.eq(VERSION).all():
        raise ValueError('Unsupported economic version')
    dates = {k: pd.to_datetime(frame[k], errors='raise') for k in required[4:7]}
    if any(v.isna().any() for v in dates.values()):
        raise ValueError('Missing dates')
    if ((dates['published_at'] > dates['reporting_date']) |
        (dates['economic_period'] > dates['published_at'])).any():
        raise ValueError('Economic data unavailable as of reporting date')


def scenario_frame(frame, scenario, baseline):
    validate(frame)
    out = frame.copy()
    dg = scenario['real_gdp_growth_pct'] - baseline['real_gdp_growth_pct']
    du = scenario['unemployment_rate_pct'] - baseline['unemployment_rate_pct']
    # Explicit synthetic mapping; effective discount rate is not a policy rate.
    out['output_growth_pct'] += dg
    out['unemployment_pct'] += du
    out['collateral_change_pct'] += 2*dg - du
    out['liquidity'] += .035*dg - .025*du
    for field, (lo, hi) in RANGES.items():
        out[field] = out[field].clip(lo, hi)
    out['scenario'] = scenario['scenario']
    validate(out)
    return out

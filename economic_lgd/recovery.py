"""S2 cashflow simulation. Latent regime is intentionally never read here."""
import numpy as np
from .economics import validate

BUCKETS = np.array([1, 6, 12, 24, 36, 60])
VERSION = 's2-component-recovery-1'


def simulate(frame, rng, draws=1, cashflows=False):
    validate(frame)
    if not isinstance(draws, int) or draws < 1:
        raise ValueError('Positive integer draws required')
    def col(name):
        return frame[name].to_numpy()[:, None]
    e = col('ead_at_default')
    rate = col('interest_rate')
    if not np.isfinite(e).all() or (e <= 0).any() or not np.isfinite(rate).all() or (rate <= -1).any():
        raise ValueError('Invalid exposure or effective rate')
    c = col('collateral_type')
    second = col('lien_rank') == 'Second'
    shape = (len(frame), draws)
    # Four observables operate through distinct recovery mechanisms, not a state flag.
    activity_stress = np.clip((2-col('output_growth_pct'))/4, -.5, 2)
    labour_stress = np.clip((col('unemployment_pct')-5.5)/3, -.5, 2)
    illiquidity = np.clip((.8-col('liquidity'))/.4, -.5, 2)
    price = col('collateral_change_pct')/100
    market = rng.normal(0, .16, shape)
    bank = rng.normal(0, .16, shape)
    collection = rng.normal(0, .10, shape)
    cure_noise = rng.normal(0, 1, shape)
    cost_noise = rng.normal(0, .009, shape)
    p_cure = 1/(1+np.exp(-(-1.5+.6*(col('current_ratio_at_default')-1)
        -.22*(col('leverage_at_default')-2.5)+.20*(col('management_quality')-3)
        -.35*activity_stress-.20*labour_stress)))
    cure = rng.random(shape) < p_cure
    delay = rng.gamma(2, 5, shape)
    cash_months = rng.integers(1, 5, shape)
    liquidation = np.select([c=='Cash', c=='Mortgage', c=='Other'], [.97, .68, .44], default=0.)
    sensitivity = np.select([c=='Cash', c=='Mortgage', c=='Other'], [0., 1., .6], default=0.)
    secured = np.minimum(e, e*col('collateral_coverage')*liquidation*np.where(second,.72,1)*
        (.55+.6*col('security_quality'))*
        np.clip(1+market+sensitivity*(price-.12*illiquidity), .15, 1.5))
    guaranteed = np.minimum(np.maximum(e-secured,0),e*col('guarantee_coverage')*
        (.25+.65*col('guarantor_strength'))*
        np.clip(1+bank-.12*activity_stress-.08*illiquidity,0,1.3))
    residual = np.maximum(e-secured-guaranteed,0)
    unsecured = residual*np.clip(.30-.027*(col('leverage_at_default')-2.8)
        +.045*(col('current_ratio_at_default')-1)+.02*(col('management_quality')-3)
        -.06*activity_stress-.04*labour_stress+collection,0,.75)
    cured = np.minimum(np.where(cure,np.maximum(e*(.90+.04*cure_noise)-secured-guaranteed-unsecured,0),0),
        np.maximum(e-secured-guaranteed-unsecured,0))
    gross = secured+guaranteed+unsecured+cured
    months = np.clip(np.rint(8+17*(c=='Mortgage')+8*second+9*(1-cure)
        +8*illiquidity+5*labour_stress+delay),1,60)
    months = np.where(c=='Cash',np.clip(cash_months+2*labour_stress,1,60),months)
    costs = e*np.clip(.012+.014*(c=='Mortgage')+.012*second
        +.015*illiquidity+.010*labour_stress+cost_noise,.003,.16)
    weights = np.exp(-np.abs(BUCKETS[None,None,:]-months[:,:,None])/9)
    weights /= weights.sum(axis=2,keepdims=True)
    net = gross[:,:,None]*weights
    net[:,:,0] -= costs*(c=='Cash')
    net[:,:,2] -= costs*(c!='Cash')
    pv = (net/(1+rate[:,:,None])**(BUCKETS[None,None,:]/12)).sum(axis=2)
    lgd = np.clip(1-pv/e,0,1)
    return (lgd, net) if cashflows else lgd


def conditional(frame, draws=512, seed=82001):
    rng = np.random.default_rng(seed)
    mean, se = [], []
    for start in range(0,len(frame),64):
        values = simulate(frame.iloc[start:start+64],rng,draws)
        mean.extend(values.mean(axis=1))
        se.extend(values.std(axis=1,ddof=1)/np.sqrt(draws))
    return np.array(mean),np.array(se)

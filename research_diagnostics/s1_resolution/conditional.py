"""Independent S1 marginal recovery integration: no fitted model or outcome inputs."""
import numpy as np

FEATURES = ['ead_at_default','collateral_type','lien_rank','collateral_coverage',
 'guarantee_coverage','security_quality','guarantor_strength','downturn_at_default',
 'leverage_at_default','current_ratio_at_default','management_quality','interest_rate']
BUCKETS=np.array([1,6,12,24,36,60])


def simulate(frame,rng,draws):
    x=frame[FEATURES]
    if draws<1:
        raise ValueError('Positive draws required')
    num=x.drop(columns=['collateral_type','lien_rank']).to_numpy(dtype=float)
    if not np.isfinite(num).all() or (x.ead_at_default<=0).any():
        raise ValueError('Finite inputs and positive EAD required')
    def col(name):
        return x[name].to_numpy()[:,None]
    shape=(len(x),draws)
    e=col('ead_at_default'); c=col('collateral_type'); second=col('lien_rank')=='Second'
    downturn=col('downturn_at_default')
    market=rng.normal(0,.16,shape); bank=rng.normal(0,.16,shape)
    collection=rng.normal(0,.10,shape); cure_noise=rng.normal(0,1,shape)
    cost_noise=rng.normal(0,.009,shape)
    probability=1/(1+np.exp(-(-1.5+.6*(col('current_ratio_at_default')-1)
        -.22*(col('leverage_at_default')-2.5)+.20*(col('management_quality')-3)-.55*downturn)))
    cure=rng.binomial(1,np.broadcast_to(probability,shape))
    delay=rng.gamma(2,5,shape); cash_months=rng.integers(1,5,shape)
    liquidation=np.select([c=='Cash',c=='Mortgage',c=='Other'],[.97,.68,.44],default=0.)
    secured=np.minimum(e,e*col('collateral_coverage')*liquidation*np.where(second,.72,1)*
        (.55+.6*col('security_quality'))*np.clip(1+market-.2*downturn,.15,1.5))
    guaranteed=np.minimum(np.maximum(e-secured,0),e*col('guarantee_coverage')*
        (.25+.65*col('guarantor_strength'))*np.clip(1+bank-.2*downturn,0,1.3))
    unsecured=np.maximum(e-secured-guaranteed,0)*np.clip(.30-.027*(col('leverage_at_default')-2.8)
        +.045*(col('current_ratio_at_default')-1)+.02*(col('management_quality')-3)
        -.10*downturn+collection,0,.75)
    cured=np.minimum(np.where(cure==1,np.maximum(e*(.90+.04*cure_noise)-secured-guaranteed-unsecured,0),0),
        np.maximum(e-secured-guaranteed-unsecured,0))
    gross=secured+guaranteed+unsecured+cured
    months=np.clip(np.rint(8+17*(c=='Mortgage')+8*second+9*(1-cure)+13*downturn+delay),1,60)
    months=np.where(c=='Cash',cash_months+4*downturn,months)
    costs=e*np.clip(.012+.014*(c=='Mortgage')+.012*second+.025*downturn+cost_noise,.003,.16)
    # Equivalent discounted bucket recovery; no copied production function call.
    weights=np.exp(-np.abs(BUCKETS[None,None,:]-months[:,:,None])/9)
    weights/=weights.sum(axis=2,keepdims=True)
    discount=(1+col('interest_rate')[:,:,None])**(BUCKETS[None,None,:]/12)
    pv=gross*np.sum(weights/discount,axis=2)
    cost_month=np.where(c=='Cash',1,12)
    pv-=costs/(1+col('interest_rate'))**(cost_month/12)
    return np.clip(1-pv/e,0,1)


def integrate(frame,draws=4096,seed=2026092501):
    rng=np.random.default_rng(seed)
    mean=[]; variance=[]
    for start in range(0,len(frame),32):
        values=simulate(frame.iloc[start:start+32],rng,draws)
        mean.extend(values.mean(axis=1)); variance.extend(values.var(axis=1,ddof=1))
    mean=np.array(mean); variance=np.array(variance)
    return mean,variance,np.sqrt(variance/draws)

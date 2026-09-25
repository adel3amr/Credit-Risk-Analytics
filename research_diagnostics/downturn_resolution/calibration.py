"""Research calibration and explicit scenario control; no active engine dependency."""
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit,logit

COLLATERAL=('Cash','Mortgage','Other','Unsecured')


class RegimeCalibration:
    def matrix(self,base,collateral,state):
        base=np.asarray(base,dtype=float); state=np.asarray(state,dtype=float)
        collateral=np.asarray(collateral)
        if base.ndim!=1 or state.shape!=base.shape or collateral.shape!=base.shape:
            raise ValueError('Aligned one-dimensional inputs required')
        if not np.isfinite(base).all() or not np.isfinite(state).all():
            raise ValueError('Nonfinite input')
        if ((base<0)|(base>1)).any() or ((state<0)|(state>1)).any():
            raise ValueError('Inputs outside 0..1')
        if not np.isin(collateral,COLLATERAL).all():
            raise ValueError('Unknown collateral')
        categories=[(collateral==c).astype(float) for c in COLLATERAL[:-1]]
        return np.column_stack([np.ones(len(base)),logit(np.clip(base,1e-6,1-1e-6)),state,
                                 *categories,*[state*v for v in categories]])

    def fit(self,base,collateral,state,actual):
        x=self.matrix(base,collateral,state); y=np.asarray(actual,dtype=float)
        if y.shape!=(len(x),) or not np.isfinite(y).all() or ((y<0)|(y>1)).any():
            raise ValueError('Invalid realized LGD')
        def objective(beta):
            z=x@beta; penalty=.5*np.sum(beta[1:]**2)
            loss=np.sum(np.logaddexp(0,z)-y*z)+penalty
            gradient=x.T@(expit(z)-y)+np.r_[0,beta[1:]]
            return loss,gradient
        result=minimize(objective,np.zeros(x.shape[1]),jac=True,method='L-BFGS-B',options={'maxiter':1000,'ftol':1e-12})
        if not result.success: raise ValueError('Calibration did not converge')
        self.coefficients=result.x
        return self

    def predict(self,base,collateral,state):
        return expit(self.matrix(base,collateral,state)@self.coefficients)

    def mixture(self,base,collateral,probability):
        probability=np.asarray(probability,dtype=float)
        # Validate shape/range with the shared contract, but mix *predictions*,
        # not nonlinear logits evaluated at mean state.
        self.matrix(base,collateral,probability)
        n=len(base)
        return ((1-probability)*self.predict(base,collateral,np.zeros(n))+
                probability*self.predict(base,collateral,np.ones(n)))


def scenario_control(calibration,base,collateral,effective_pd,ead,*,scenario,source,run_id,purpose='sensitivity'):
    if purpose!='sensitivity':
        raise ValueError('Not approved for expected-loss booking; validated state/weights required')
    if scenario not in ('normal','downturn') or not source or not run_id:
        raise ValueError('Explicit scenario, source and run ID required')
    base=np.asarray(base,dtype=float); ead=np.asarray(ead,dtype=float); pd=np.asarray(effective_pd,dtype=float)
    if ead.shape!=base.shape or pd.shape!=base.shape or not np.isfinite(ead).all() or not np.isfinite(pd).all():
        raise ValueError('Invalid exposure/PD')
    if (ead<0).any() or ((pd<0)|(pd>1)).any(): raise ValueError('Invalid exposure/PD range')
    scenario_lgd=calibration.predict(base,collateral,np.full(len(base),int(scenario=='downturn')))
    base_ecl=pd*base*ead; scenario_ecl=pd*scenario_lgd*ead
    return dict(base_lgd=base.tolist(),scenario_lgd=scenario_lgd.tolist(),base_ecl=base_ecl.tolist(),
        scenario_ecl=scenario_ecl.tolist(),incremental_sensitivity=np.maximum(scenario_ecl-base_ecl,0).tolist(),
        scenario=scenario,source=source,run_id=run_id,status='SENSITIVITY ONLY; NOT AN IFRS9 ALLOWANCE OR ACTIVE LGD')

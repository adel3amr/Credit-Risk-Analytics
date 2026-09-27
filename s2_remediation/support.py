"""Outcome-free local economic/support contract with explicit rejection."""
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from economic_lgd.economics import MACRO,validate

FIELDS=MACRO+['collateral_coverage','guarantee_coverage']


class UnsupportedDomain(ValueError):
    pass


class Support:
    def fit(self, frame):
        validate(frame)
        self.low=frame[MACRO].min()
        self.high=frame[MACRO].max()
        # Guarantee IQR is zero in a mostly unguaranteed bank: unit coverage is
        # the economic scale, not a tiny epsilon denominator.
        self.scale=(frame[FIELDS].quantile(.75)-frame[FIELDS].quantile(.25)).replace(0,1)
        self.groups={}
        for name,g in frame.groupby('collateral_type'):
            x=g[FIELDS].to_numpy()/self.scale.to_numpy()
            index=NearestNeighbors(metric='chebyshev',algorithm='kd_tree').fit(x)
            self.groups[name]=(index,(g.industry+'|'+g.reporting_date).to_numpy())
        return self

    def inspect(self, frame):
        validate(frame)
        x=frame[FIELDS].to_numpy(dtype=float)
        if not np.isfinite(x).all(): raise ValueError('Nonfinite support feature')
        result=pd.DataFrame({'facility_id':frame.facility_id.to_numpy(),
            'outside_macro_range':((frame[MACRO]<self.low)|(frame[MACRO]>self.high)).any(axis=1).to_numpy(),
            'neighbors':0,'clusters':0,'distance_20':np.inf})
        for name in frame.collateral_type.unique():
            positions=np.flatnonzero(frame.collateral_type.to_numpy()==name)
            if name not in self.groups: continue
            index,clusters=self.groups[name]
            query=x[positions]/self.scale.to_numpy()
            # Query 20 nearest plus all radius neighbors for actual cluster support.
            distance,_=index.kneighbors(query,n_neighbors=min(20,len(clusters)))
            neighbors=index.radius_neighbors(query,radius=.75,return_distance=False)
            result.loc[positions,'distance_20']=distance[:,-1]
            result.loc[positions,'neighbors']=[len(n) for n in neighbors]
            result.loc[positions,'clusters']=[len(np.unique(clusters[n])) for n in neighbors]
        result['supported']=(~result.outside_macro_range)&(result.neighbors>=20)&(result.clusters>=3)
        return result

    def require(self,frame):
        report=self.inspect(frame)
        if not report.supported.all():
            raise UnsupportedDomain(f'{int((~report.supported).sum())} unsupported facilities; new domain validation required')
        return report

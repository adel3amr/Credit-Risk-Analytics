"""Run S1 current cohort through the unchanged, governed reference platform."""
import gzip
import json
import numpy as np
import pandas as pd
from sqlalchemy import select
from credit_platform import service,security,schema as s,audit
from credit_platform.db import engine,require_schema
from credit_platform.domain import DatasetInput,RunInput
from credit_platform.common import uid
from synthetic_bank.generate import ROOT,DEST,sha
from synthetic_bank.evaluate import verify_data


def main():
    verify_data()
    db=engine(); require_schema(db)
    name='S1-validation-'+uid()
    security.issue(db,name,'analyst')
    with db.connect() as conn:
        actor=conn.scalar(select(s.principals.c.id).where(s.principals.c.name==name))
    with gzip.open(DEST/'current/canonical.json.gz','rt') as stream:
        data=DatasetInput.model_validate(json.load(stream))
    dataset=service.ingest(db,data,actor)
    run=service.execute(db,RunInput(dataset_id=dataset['id'],request_key='S1-'+uid()),actor)
    if run['status']!='SUCCEEDED':
        raise RuntimeError(run['summary'])
    with db.connect() as conn:
        traces=service.traces(conn,run['id'])
        chain=audit.verify(conn)
    # Independent EAD reconstruction from source contracts; not production ead().
    f={x.id:x for x in data.facilities}
    max_ead=0.; max_ecl=0.
    for t in traces:
        row=f[t['facility_id']]
        e=(row.drawn if row.product=='Term Loan' else row.limit if row.product=='OVD'
           else float(np.round(row.face*{'Import LC':.2,'Performance Guarantee':.5,'Financial Guarantee':1}[row.product],2)))
        probability=1 if t['stage']=='Stage 3' else (1-(1-t['pd'])**(row.remaining_months/12) if t['stage']=='Stage 2' else t['pd'])
        max_ead=max(max_ead,abs(t['ead']-e))
        max_ecl=max(max_ecl,abs(t['ecl']-e*t['lgd']*probability))
    assert len(traces)==len(data.facilities)
    assert max_ead<1e-8 and max_ecl<1e-7
    results=dict(run_id=run['id'],dataset_hash=dataset['hash'],summary=run['summary'],
        independent_max_ead_error=max_ead,independent_max_ecl_error=max_ecl,audit=chain,
        status='REFERENCE EXECUTION ONLY; S1 CHALLENGERS NOT PROMOTED',
        data_manifest_hash=sha(DEST/'manifest.json'))
    dest=ROOT/'synthetic_bank/results'
    dest.mkdir(exist_ok=True)
    (dest/'platform_run.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))


if __name__=='__main__':
    main()

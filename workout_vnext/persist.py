"""Load the frozen ledger into an empty WN-1 namespace; transactional and append-only."""
import os,json,gzip
from sqlalchemy import select,func,inspect
from credit_platform.db import engine
from .store import migrate,load,borrowers,facilities,EVENTS
from .generate import DATA
from .experiment import verify

def main():
    verify();db=engine(os.environ['WORKOUT_DATABASE_URL']);migrate(db)
    with db.connect() as c:
        if c.scalar(select(func.count()).select_from(borrowers)):raise ValueError('Workout store already populated; no overwrite')
    # Load in bounded batches within one transaction, never publish partial state.
    with db.begin() as c:
        for name,table in [('borrower',borrowers),('facility',facilities)]+list(EVENTS.items()):
            batch=[]
            with gzip.open(DATA/(name+'.jsonl.gz'),'rt') as f:
                for line in f:
                    batch.append(json.loads(line))
                    if len(batch)==2000:c.execute(table.insert(),batch);batch=[]
            if batch:c.execute(table.insert(),batch)
    with db.connect() as c:
        counts={name:c.scalar(select(func.count()).select_from(table)) for name,table in [('borrower',borrowers),('facility',facilities)]+list(EVENTS.items())}
    assert counts==json.loads((DATA/'manifest.json').read_text())['counts']
    print(json.dumps({'dialect':db.dialect.name,'counts':counts,'status':'VERIFIED'}))
    db.dispose()
if __name__=='__main__':main()

"""Portable WN-1 relational reference store, independent additive schema lifecycle."""
from sqlalchemy import MetaData,Table,Column,String,Float,JSON,ForeignKey,CheckConstraint,select,inspect

metadata=MetaData()
versions=Table('wn_schema_version',metadata,Column('version',String,primary_key=True))
borrowers=Table('wn_borrower',metadata,Column('id',String,primary_key=True),Column('industry',String,nullable=False),Column('source',String,nullable=False))
facilities=Table('wn_facility',metadata,Column('id',String,primary_key=True),Column('borrower_id',ForeignKey('wn_borrower.id'),nullable=False),Column('product',String,nullable=False),Column('principal',Float,nullable=False),Column('predefault_interest',Float,nullable=False),Column('rate',Float,nullable=False),Column('source',String,nullable=False),CheckConstraint('principal>0 and predefault_interest>=0 and rate>=0'))
ENTITIES=['default_event','credit_snapshot','workout_snapshot','collateral','collateral_valuation','collateral_enforcement','guarantee','guarantee_claim','recovery_transaction','workout_cost','restructure_event','cure_event','writeoff_event','interest_accrual','resolution_event','macro_snapshot']
EVENTS={name:Table('wn_'+name,metadata,Column('id',String,primary_key=True),Column('facility_id',ForeignKey('wn_facility.id'),nullable=False,index=True),Column('effective_date',String,nullable=False,index=True),Column('recorded_at',String,nullable=False),Column('source',String,nullable=False),Column('amount',Float,nullable=False),Column('payload',JSON,nullable=False),CheckConstraint('amount>=0'),CheckConstraint('recorded_at>=effective_date')) for name in ENTITIES}

def migrate(db):
    """Initial additive schema, no silent modification of an existing version."""
    if inspect(db).has_table('wn_schema_version'):
        with db.connect() as c:
            if c.execute(select(versions.c.version)).scalars().all()!=['WN-1']: raise ValueError('Unsupported workout schema')
        return
    metadata.create_all(db)
    with db.begin() as c:c.execute(versions.insert().values(version='WN-1'))

def load(db,tables):
    migrate(db)
    with db.begin() as c:
        for name,table in [('borrower',borrowers),('facility',facilities)]+list(EVENTS.items()):
            rows=tables.get(name,[])
            if rows:c.execute(table.insert(),rows)

def asof(conn,facility_id,observation):
    if conn.execute(select(facilities.c.id).where(facilities.c.id==facility_id)).first() is None: raise ValueError('Unknown facility')
    return {n:[dict(r) for r in conn.execute(select(t).where(t.c.facility_id==facility_id,t.c.effective_date<=observation,t.c.recorded_at<=observation).order_by(t.c.effective_date,t.c.id)).mappings()] for n,t in EVENTS.items()}

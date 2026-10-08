"""Read frozen WN-1 reports; no training or active-scoring mutation."""
import json
from .common import ROOT
from .service import NotFound
from workout_vnext.generate import sha

def get():
    base=ROOT/'workout_vnext'
    path=base/'EVIDENCE_LOCK.json'
    if not path.exists():raise NotFound('WN-1 validation closeout is unavailable')
    lock=json.loads(path.read_text())
    for name,digest in lock['files'].items():
        if sha(base/name)!=digest:raise ValueError('WN-1 evidence hash mismatch: '+name)
    evidence={name:json.loads((base/'results'/filename).read_text()) for name,filename in [('decision','decision.json'),('ecl','ecl_bridge.json'),('ledger','ledger_audit.json')]}
    evidence['manifest_hash']=sha(base/'data/manifest.json')
    evidence['model_lock_hash']=sha(base/'results/LOCK.json')
    return evidence,{'type':'frozen_workout_validation','path':'workout_vnext/EVIDENCE_LOCK.json','hash':sha(path)}

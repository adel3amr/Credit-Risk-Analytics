"""Read-only public synthetic S2 evidence; no risk scoring or promotion authority."""
import json
from .common import ROOT,file_hash
from .service import NotFound


def get():
    path=ROOT/'economic_lgd/results/decision.json'
    if not path.exists():
        raise NotFound('S2 economic LGD evidence unavailable')
    evidence=json.loads(path.read_text())
    for name,expected in evidence['source_hashes'].items():
        source=(ROOT/name).resolve()
        if not source.is_relative_to((ROOT/'economic_lgd/results').resolve()) or file_hash(source)!=expected:
            raise ValueError('S2 evidence integrity mismatch')
    return evidence,{'type':'validation_decision','path':'economic_lgd/results/decision.json',
                     'hash':file_hash(path)}

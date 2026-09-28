"""Read-only public synthetic S2 evidence; no risk scoring or promotion authority."""
import json
from .common import ROOT,file_hash
from .service import NotFound


def get():
    latest=ROOT/'lgd_hardening/results/decision.json'
    prior=ROOT/'s2_remediation/results/decision.json'
    path=latest if latest.exists() else prior if prior.exists() else ROOT/'economic_lgd/results/decision.json'
    if not path.exists():
        raise NotFound('S2 economic LGD evidence unavailable')
    evidence=json.loads(path.read_text())
    for name,expected in evidence['source_hashes'].items():
        source=(ROOT/name).resolve()
        permitted=[path.parent.resolve()]
        if path==latest:permitted.append(prior.parent.resolve())
        if not any(source.is_relative_to(folder) for folder in permitted) or file_hash(source)!=expected:
            raise ValueError('S2 evidence integrity mismatch')
    if path in [latest,prior]:
        registry=json.loads((path.parent/'registry.json').read_text())
        if registry['decision_sha256']!=file_hash(path):
            raise ValueError('S2 remediation decision integrity mismatch')
    return evidence,{'type':'validation_decision','path':str(path.relative_to(ROOT)),
                     'hash':file_hash(path)}

"""Additional pre-scoring integrity gate; cannot be waived by a status string."""
import json
from pathlib import Path
from credit_platform.common import file_hash


def require_promotion(directory):
    directory=Path(directory)
    registry=json.loads((directory/'registry.json').read_text())
    decision=json.loads((directory/'decision.json').read_text())
    if registry.get('decision_sha256')!=file_hash(directory/'decision.json'):
        raise ValueError('Promotion evidence hash mismatch')
    if registry.get('model_id')!=decision.get('model_version'):
        raise ValueError('Promotion model identity mismatch')
    expected='PROMOTED_SYNTHETIC_REFERENCE'
    if registry.get('status')!=expected or decision.get('status')!=expected:
        raise ValueError('Model has not been promoted')
    required={'current_calibration','scenario_calibration','scenario_consistency',
              'guarantees','model_support','general_performance','ecl','engineering_governance'}
    gates=decision.get('gates',{})
    if set(gates)!=required or any(gates[k] is not True for k in required):
        raise ValueError('Promotion gates are incomplete or failed')
    if registry.get('gates')!=gates:raise ValueError('Registry/decision gates disagree')
    return registry

"""Record an actual full-suite run; never manufacture an engineering PASS."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from credit_platform.common import atomic_json,file_hash,now
from s2_remediation.evaluate import verify,verify_lock,OUT


def main():
    verify();verify_lock()
    result=subprocess.run([sys.executable,'-m','pytest','-q'],cwd=ROOT,
        capture_output=True,text=True,env={**os.environ,'OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2'})
    output=result.stdout+result.stderr
    print(output,flush=True)
    (OUT/'pytest.txt').write_text(output)
    matches=re.findall(r'(\d+) passed',output)
    skipped=bool(re.search(r'\d+ skipped',output))
    success=result.returncode==0 and bool(matches) and not skipped
    atomic_json(OUT/'engineering.json',dict(passed=success,exit_code=result.returncode,
        tests_passed=int(matches[-1]) if matches else 0,skipped=skipped,
        command=f'{sys.executable} -m pytest -q',completed_at=now(),
        pytest_output_sha256=file_hash(OUT/'pytest.txt'),
        tested_source_hashes={str(p.relative_to(ROOT)):file_hash(p)
            for folder in ['credit_platform','s2_remediation','tests']
            for p in sorted((ROOT/folder).rglob('*.py')) if 'rejected_generation' not in p.parts},
        limitation='Local Python/SQLite/API validation; hosted Actions/PostgreSQL/container/browser qualification not executed'))
    return 0 if success else 1


if __name__=='__main__': raise SystemExit(main())

"""Real socket startup check in an isolated migrated database, not browser QA."""
import json, os, socket, subprocess, sys, tempfile, time
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from credit_platform.common import ROOT

with tempfile.TemporaryDirectory(prefix='credit-red-team-http-') as tmp:
    env={**os.environ,'DATABASE_URL':'sqlite:///'+tmp+'/http.db'}
    subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT,env=env,check=True)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
    proc=subprocess.Popen([sys.executable,'-m','uvicorn','credit_platform.api:app','--host','127.0.0.1','--port',str(port),'--no-access-log'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                with urlopen(f'http://127.0.0.1:{port}/health/ready',timeout=1) as r:
                    readiness=json.load(r)
                break
            except Exception:
                if proc.poll() is not None:raise RuntimeError('Server exited')
                time.sleep(.2)
        else:raise RuntimeError('Readiness timeout')
        responses={}
        for path in ['/','/static/app.js','/static/style.css','/openapi.json','/api/v1/runs']:
            try:
                with urlopen(f'http://127.0.0.1:{port}'+path) as r:
                    responses[path]=r.status
            except HTTPError as e:responses[path]=e.code
        assert responses['/api/v1/runs']==401
        assert all(v==200 for k,v in responses.items() if k!='/api/v1/runs')
        (ROOT/'final_red_team_evidence/http.json').write_text(json.dumps({'ready':readiness,'responses':responses,'real_socket':True,'real_browser':False},indent=2))
        print(responses)
    finally:
        proc.terminate()
        proc.wait(timeout=10)

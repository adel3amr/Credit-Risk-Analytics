"""Explicitly lock completed research evidence; no model training or promotion."""
from .generate import HERE,sha,dump

def main():
    path=HERE/'EVIDENCE_LOCK.json'
    if path.exists():raise ValueError('Evidence already frozen')
    files=[HERE/'data/manifest.json']+sorted((HERE/'results').glob('*'))
    dump(path,{'version':'WN-1','status':'NOT_PROMOTED','files':{str(p.relative_to(HERE)):sha(p) for p in files if p.is_file()}})
if __name__=='__main__':main()

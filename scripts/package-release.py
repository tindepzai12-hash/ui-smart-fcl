"""Build a source/build handoff from tracked files and explicitly named QA artifacts."""
import hashlib, json, re, subprocess, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT.parent/'ui-smart'
OUT = ROOT.parent/'output'
GIT = 'git'

def build(git=GIT):
    tracked = subprocess.check_output([git,'ls-files','-z'],cwd=ROOT).decode().split('\0')
    payload = {}
    excluded = {'data','vendor','node_modules','tools','.git','tmp','__pycache__','.pytest_cache'}
    allowed = {'backend','frontend','docs','samples','scripts','tests'}
    for name in tracked:
        if not name: continue
        p=Path(name)
        if set(p.parts)&excluded or p.name.startswith('.env') or 'secret' in p.name.lower():
            raise ValueError('Unexpected tracked sensitive path: '+name)
        if len(p.parts)>1 and p.parts[0] not in allowed: continue
        payload['ui-smart/'+p.as_posix()] = (ROOT/p).read_bytes()
    for p in (LOCAL/'dist').rglob('*'):
        if p.is_file(): payload['ui-smart/dist/'+p.relative_to(LOCAL/'dist').as_posix()]=p.read_bytes()
    assert 'ui-smart/dist/index.html' in payload
    payload['BAT_DAU_TAI_DAY.md']=(ROOT/'docs/BAN_GIAO_1_1.md').read_bytes()
    for name in ['01_FCL_Bo_chung_tu_ro_net.pdf','02_FCL_Bo_chung_tu_scan.pdf']:
        payload['BO_CHUNG_TU_TEST/'+name]=(OUT/'pdf'/name).read_bytes()
    payload['BO_CHUNG_TU_TEST/HUONG_DAN_TEST.md']=(ROOT/'docs/HUONG_DAN_TEST.md').read_bytes()
    for name in ['cloud-packets-report.json','handoff-live-health.json','handoff-openai-report.json']:
        payload['QA/'+name]=(LOCAL/'qa'/name).read_bytes()
    for name in ['v11-pdf-split.png','v11-scan-workspace.png','v11-render-scan.png','handoff-openai-connected.png']:
        payload['QA/'+name]=(LOCAL/'qa/screenshots'/name).read_bytes()
    for name,data in payload.items():
        if re.search(rb'sk-(?:proj-)?[A-Za-z0-9_-]{24,}',data):
            raise ValueError('Possible API secret in '+name)
    manifest={name:hashlib.sha256(data).hexdigest() for name,data in sorted(payload.items())}
    payload['MANIFEST_SHA256.json']=json.dumps(manifest,ensure_ascii=False,indent=2).encode()
    OUT.mkdir(exist_ok=True)
    target=OUT/'U_I_SMART_1_1_Ban_Giao.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(payload.items()): z.writestr(name,data)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(name)).hexdigest()==digest for name,digest in manifest.items())
        assert not any(set(Path(name).parts)&excluded for name in z.namelist())
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix('.sha256.txt').write_text(digest+'  '+target.name+'\n')
    print(json.dumps({'path':str(target),'files':len(payload),'bytes':target.stat().st_size,'sha256':digest}))

if __name__=='__main__':
    import sys
    build(sys.argv[1] if len(sys.argv)>1 else GIT)

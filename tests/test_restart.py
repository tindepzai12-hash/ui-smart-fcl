"""A real subprocess restart, using an isolated database and localhost port."""
import json,os,subprocess,sys,time,urllib.request
import httpx
from backend import db

def test_real_backend_restart(tmp_path):
    folder=tmp_path/'persist';env=dict(os.environ,UI_SMART_DATA=str(folder));port=18765
    def request(route,body=None):
        payload=None if body is None else json.dumps(body).encode()
        req=urllib.request.Request(f'http://127.0.0.1:{port}/api/'+route,data=payload,headers={'Content-Type':'application/json','X-UI-Smart':'local'})
        with urllib.request.urlopen(req,timeout=3) as res:return json.load(res)
    def launch():
        p=subprocess.Popen([sys.executable,str(db.ROOT/'run.py'),'--port',str(port)],cwd=db.ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for _ in range(100):
            if p.poll() is not None:raise AssertionError('Isolated backend did not start')
            try:request('health');return p
            except OSError:time.sleep(.05)
        p.terminate();p.wait(timeout=10);raise AssertionError('Startup timeout')
    p=launch()
    try:
        case=request('cases',{'name':'Restart proof','customer':'Synthetic'})['case']
        uploaded=httpx.post(f'http://127.0.0.1:{port}/api/cases/'+case['id']+'/documents',headers={'X-UI-Smart':'local'},files={'files':('restart.txt',b'COMMERCIAL INVOICE\nInvoice No: 000042\n','text/plain')})
        assert uploaded.status_code==200
        job=request('cases/'+case['id']+'/process',{'mode':'local'})
        for _ in range(100):
            if request('jobs/'+job['id'])['status']!='running':break
            time.sleep(.05)
        result=request('cases/'+case['id'])
        record=next(r for r in result['records'] if r['key']=='invoice_number')
        assert record['value']['text']=='000042'
    finally:p.terminate();p.wait(timeout=10)
    p=launch()
    try:
        result=request('cases/'+case['id'])
        assert result['case']['name']=='Restart proof'
        assert next(r for r in result['records'] if r['id']==record['id'])['value']['text']=='000042'
        assert request('cases/'+case['id']+'/audit')
    finally:p.terminate();p.wait(timeout=10)

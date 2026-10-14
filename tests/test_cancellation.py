import threading,time
from backend import app as module,reader
from test_core import client,H,new,upload
from fixtures import INVOICE,pdf

def test_cancel_local_job_keeps_original(monkeypatch):
    entered=threading.Event();release=threading.Event();original=module.reader.read_document
    def delayed(*args,**kwargs):
        entered.set();release.wait(timeout=5)
        if (args[2] if len(args)>2 else kwargs.get('cancelled',lambda:False))():raise InterruptedError('Cancelled')
        return original(*args,**kwargs)
    monkeypatch.setattr(module.reader,'read_document',delayed)
    id=new();upload(id,[('cancel.txt',INVOICE.encode())])
    job=client.post('/api/cases/'+id+'/process',headers=H,json={'mode':'local'}).json();assert entered.wait(3)
    res=client.post('/api/jobs/'+job['id']+'/cancel',headers=H);release.set();assert res.status_code==200
    for _ in range(100):
        state=client.get('/api/jobs/'+job['id']).json()
        if state['status']!='running':break
        time.sleep(.03)
    assert state['status']=='cancelled',state
    bundle=client.get('/api/cases/'+id).json();assert bundle['documents'][0]['size']>0
    assert bundle['documents'][0]['status']!='reading'

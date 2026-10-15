"""Exception-first shipment comparison. Sources are immutable; edits are separate working values."""
import hashlib,json,re
from decimal import Decimal
from . import db
from .dictionary import FIELDS

def signature(documents,records):
    body={'documents':sorted((d['id'],d['type']) for d in documents),
          'records':sorted((r['id'],r['key'],db.encode(r['value']),r['status']=='rejected') for r in records)}
    return hashlib.sha256(db.encode(body).encode()).hexdigest()

def sources(group,documents):
    docs={d['id']:d for d in documents}
    return [{'id':r['id'],'document_id':r['document_id'],'document':docs.get(r['document_id'],{}).get('name','Nhập tay'),
             'type':docs.get(r['document_id'],{}).get('type','Manual'),'value':r['value'],'raw':r['raw'],
             'evidence':r['evidence'],'page':r['page'],'method':r['method']} for r in group]

def additional_checks(documents,records):
    active=[r for r in records if r['status']!='rejected'];out=[]
    def add(key,result,reason,group):
        out.append({'key':key,'result':result,'severity':'error' if result=='Mismatch' else 'warning',
                    'detail':{'reason':reason,'sources':sources(group,documents)}})
    for doc in documents:
        rows=[r for r in active if r['document_id']==doc['id']]
        gross=[r for r in rows if r['key']=='gross_weight' and not r['value'].get('warning') and r['value'].get('unit')=='KG']
        net=[r for r in rows if r['key']=='net_weight' and not r['value'].get('warning') and r['value'].get('unit')=='KG']
        if len(gross)==len(net)==1 and Decimal(net[0]['value']['number'])>Decimal(gross[0]['value']['number']):
            add('weight-order:'+doc['id'],'Mismatch','Trọng lượng tịnh lớn hơn trọng lượng cả bì trên cùng chứng từ. Kiểm lại ô và đơn vị; không tự đảo hai giá trị.',net+gross)
    # Align item rows by explicit product code, never list position or guessed description.
    items={}
    for r in active:
        if r['kind']=='item' and r['value'].get('product_code'):
            items.setdefault(re.sub(r'\s+','',r['value']['product_code']).upper(),[]).append(r)
    from .normalize import normalize,comparable
    for code,group in items.items():
        if len({r['document_id'] for r in group})<2:continue
        for key in ['quantity','unit_price','line_amount','currency']:
            present=[r for r in group if r['value'].get(key)]
            if len({r['document_id'] for r in present})<2:continue
            if len({r['value'].get('scope','invoice') for r in present})>1 and key in ['unit_price','line_amount']:continue
            if key in ['unit_price','line_amount'] and (any(not r['value'].get('currency') for r in present) or len({r['value']['currency'] for r in present})>1):continue
            values=[comparable(normalize(str(r['value'][key])+(' '+r['value'].get('unit','') if key=='quantity' else ''),'quantity' if key=='quantity' else 'number' if key in ['unit_price','line_amount'] else 'currency')) for r in present]
            if any(v is None for v in values):continue
            if key=='quantity' and len({v[1] for v in values})>1:continue
            if len(set(values))>1:
                contract=any(r['value'].get('scope')=='contract' for r in present)
                add('item:'+code+':'+key,'Needs Verification' if contract else 'Mismatch',
                    f'Mã hàng {code}: {key} khác nhau giữa các nguồn. '+('Hợp đồng có thể giao nhiều đợt; kiểm điều khoản và phạm vi trước khi kết luận.' if contract else 'Các dòng được ghép bằng mã hàng in trên nguồn, không ghép theo thứ tự.'),present)
    return out

def ai_checks(case_id,documents,records):
    if not case_id:return []
    saved=db.one('SELECT * FROM packet_reviews WHERE case_id=?',(case_id,))
    if not saved or saved['signature']!=signature(documents,records):return []
    return json.loads(saved['payload'])

def report(case,documents,records,checks):
    byid={r['id']:r for r in records};issues=[];matched=[];single=[];gaps=[]
    for check in checks:
        c={**check,'detail':dict(check['detail'])}
        c['detail']['sources']=[{**s,**({'raw':byid[s['id']]['raw'],'evidence':byid[s['id']]['evidence'],
                  'document_id':byid[s['id']]['document_id'],'method':byid[s['id']]['method']} if s['id'] in byid else {})} for s in c['detail'].get('sources',[])]
        if c['key'].startswith('classification:'):continue
        if c['result']=='Matched':matched.append(c)
        elif c['result']=='Not Yet Checked':single.append(c)
        elif c['result']=='Missing':gaps.append(c)
        elif c['result'] in ['Mismatch','Needs Verification']:issues.append(c)
    issues.sort(key=lambda c:(bool(c.get('resolution')),c['result']!='Mismatch',c['key']!='field:gross_weight'))
    saved=db.one('SELECT signature,error,created_at FROM packet_reviews WHERE case_id=?',(case['id'],))
    state='not_run' if not saved else 'stale' if saved['signature']!=signature(documents,records) else 'error' if saved['error'] else 'completed'
    return {'issues':issues,'matched':matched,'single_source':single,'gaps':gaps,
            'open_count':sum(not c.get('resolution') for c in issues),'mismatch_count':sum(c['result']=='Mismatch' and not c.get('resolution') for c in issues),
            'ai_state':state,'ai_error':saved['error'] if saved and state=='error' else '',
            'scope':'Một hồ sơ = một lô hàng. Nguồn kế hoạch, hợp đồng giao nhiều đợt và dữ liệu chưa rõ đơn vị được cảnh báo riêng, không tự kết luận sai.'}

def run_ai_review(case_id,documents,records):
    """AI only suggests semantic issues over existing IDs; never creates or corrects data."""
    from . import ai
    from pydantic import Field
    from typing import List
    class Issue(ai.Strict):
        field_id:str
        record_ids:List[str]=Field(min_length=2,max_length=12)
        reason:str=Field(min_length=5,max_length=1000)
    class Review(ai.Strict):
        issues:List[Issue]=Field(max_length=40)
    sig=signature(documents,records);output=[];error=''
    active=[r for r in records if r['status']!='rejected']
    try:
        if len(active)>350:raise ValueError('Hồ sơ hơn 350 bản ghi; chưa chạy đối chiếu ngữ nghĩa AI. Đối chiếu số liệu vẫn hoạt động.')
        payload=[{**s,'field_id':r['key'],'kind':r['kind']} for r,s in zip(active,sources(active,documents))]
        policy=(db.ROOT/'docs'/'AI_SHIPMENT_CONSISTENCY.md').read_text(encoding='utf-8')
        response=ai.OpenAI(api_key=ai.key(),timeout=60,max_retries=1).responses.parse(model=ai._model,store=False,text_format=Review,
            input=[{'role':'system','content':ai.NO_INFERENCE_POLICY+'\n'+policy},
                   {'role':'user','content':db.encode(payload)}],
            **({'temperature':0} if ai._model.startswith(('gpt-4.1','gpt-4o')) else {}))
        db.execute('INSERT INTO ai_usage VALUES (?,?,?,?,?,?,?)',(db.uid(),case_id,db.now(),ai._model,getattr(response.usage,'input_tokens',None),getattr(response.usage,'output_tokens',None),'packet-consistency'))
        if response.output_parsed is None:raise ValueError('AI chưa trả kết quả đối chiếu có cấu trúc.')
        index={r['id']:r for r in active};seen=set()
        for issue in response.output_parsed.issues:
            ids=list(dict.fromkeys(issue.record_ids))
            if len(ids)<2 or any(i not in index for i in ids):continue
            group=[index[i] for i in ids]
            # Cross-role guesses cannot enter the exception queue.
            if any(r['key']!=issue.field_id for r in group):continue
            if len({r['document_id'] for r in group})<2:continue
            if any(r['kind']=='item' for r in group):
                codes={re.sub(r'\s+','',r['value'].get('product_code','')).upper() for r in group}
                if '' in codes or len(codes)!=1:continue
            if issue.field_id in seen:continue
            seen.add(issue.field_id)
            output.append({'key':'ai-semantic:'+issue.field_id,'result':'Needs Verification','severity':'warning',
                           'detail':{'reason':'AI gợi ý cần so sánh: '+issue.reason,'sources':sources(group,documents),'method':'OpenAI semantic suggestion'}})
    except Exception as exc:
        error=str(exc)[:500] if isinstance(exc,ValueError) else ai.safe_error(exc)
    db.execute('INSERT OR REPLACE INTO packet_reviews VALUES (?,?,?,?,?)',(case_id,sig,db.encode(output),error,db.now()))
    return error

"""Exception-first shipment comparison. Sources are immutable; edits are separate working values."""
import hashlib,json,re
from decimal import Decimal
from . import db
from .dictionary import FIELDS

CONTEXT_FIELDS={'incoterms','payment_terms','shipment_terms','origin','port_loading','port_discharge',
    'seller','buyer','shipper','consignee','notify_party','exporter','importer',
    'seller_address','buyer_address','shipper_address','consignee_address','exporter_address','importer_address'}
REFERENCE_FIELDS={'booking_number','invoice_number','packing_list_number','contract_number','po_number','bl_number','awb_number'}

def signature(documents,records):
    body={'policy':hashlib.sha256((db.ROOT/'docs'/'AI_SHIPMENT_CONSISTENCY.md').read_bytes()).hexdigest(),
          'documents':sorted((d['id'],d['type'],d.get('hash','')) for d in documents),
          'records':sorted((r['id'],r['key'],db.encode(r['value']),r['status']=='rejected',
                            r.get('page'),r.get('evidence','')) for r in records)}
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
        if len({(r['document_id'],r['page']) for r in group})<2:continue
        for key in ['quantity','unit_price','line_amount','currency']:
            present=[r for r in group if r['value'].get(key)]
            if len({(r['document_id'],r['page']) for r in present})<2:continue
            if len({r['value'].get('scope','invoice') for r in present})>1 and key in ['unit_price','line_amount']:continue
            if key in ['unit_price','line_amount'] and (any(not r['value'].get('currency') for r in present) or len({r['value']['currency'] for r in present})>1):continue
            values=[comparable(normalize(str(r['value'][key])+(' '+r['value'].get('unit','') if key=='quantity' else ''),'quantity' if key=='quantity' else 'number' if key in ['unit_price','line_amount'] else 'currency')) for r in present]
            if any(v is None for v in values):continue
            if key=='quantity' and len({v[1] for v in values})>1:continue
            if len(set(values))>1:
                contract=any(r['value'].get('scope')=='contract' for r in present)
                ambiguous=len({(r['document_id'],r['page'],r['value'].get('scope','invoice')) for r in present})<len(present)
                add('item:'+code+':'+key,'Needs Verification' if contract or ambiguous else 'Mismatch',
                    f'Mã hàng {code}: {key} khác nhau giữa các nguồn. '+('Hợp đồng có thể giao nhiều đợt; kiểm điều khoản và phạm vi trước khi kết luận.' if contract else 'Mã hàng lặp trên cùng trang; cần xác định quan hệ các dòng trước khi kết luận.' if ambiguous else 'Các dòng được ghép bằng mã hàng in trên nguồn, không ghép theo thứ tự.'),present)
    return out

def ai_checks(case_id,documents,records):
    if not case_id:return []
    saved=db.one('SELECT * FROM packet_reviews WHERE case_id=?',(case_id,))
    if not saved or saved['error'] or saved['signature']!=signature(documents,records):return []
    return [c for c in json.loads(saved['payload']) if c['result']=='Needs Verification' and semantic_difference(c,records)]


def description_assessment(case_id,documents,records,group):
    """Only a current, complete AI assessment can explain semantic compatibility."""
    if not case_id:return None
    from .validation import comparison_values
    values=comparison_values('cargo_description',group,records)
    if all(v is not None for v in values) and len(set(values))==1:return None
    saved=db.one('SELECT * FROM packet_reviews WHERE case_id=?',(case_id,))
    if not saved or saved['error'] or saved['signature']!=signature(documents,records):return None
    ids={r['id'] for r in group}
    for check in json.loads(saved['payload']):
        if check['key']!='ai-description:cargo_description':continue
        if {s['id'] for s in check['detail']['sources']}==ids:return check
    return None

def contextual_candidates(documents,records):
    """Semantic review is bounded: it can never waive numbers, dates or identifiers."""
    from .validation import comparison_values,port_detail_compatible
    groups={}
    for r in records:
        if r['status']!='rejected' and r['kind']=='field' and r['key'] in CONTEXT_FIELDS:
            groups.setdefault(r['key'],[]).append(r)
    candidates={}
    for key,group in groups.items():
        if len({r['document_id'] for r in group})<2:continue
        values=comparison_values(key,group,records)
        if any(v is None for v in values) or len(set(values))<=1:continue
        if key in ['port_loading','port_discharge'] and port_detail_compatible(group):continue
        candidates[key]=group
    return candidates

def packet_context(documents,records,source_pages=None):
    """Observed links and source clauses, never a guessed 'same shipment' assertion."""
    refs={}
    for r in records:
        if r['kind']=='field' and r['key'] in REFERENCE_FIELDS:
            value=re.sub(r'\s+','',r['value'].get('text','')).upper()
            if value:refs.setdefault((r['key'],value),[]).append(r)
    links=[{'field_id':key,'record_ids':[r['id'] for r in group],
            'document_ids':sorted({r['document_id'] for r in group})}
           for (key,_),group in refs.items() if len({r['document_id'] for r in group})>=2]
    # Full contract pages supplement extracted clauses without manufacturing fields.
    # Bound context size, and tell the model when a page/context is incomplete.
    pages=[];budget=80000
    docs={d['id']:d for d in documents}
    eligible=[p for p in (source_pages or []) if docs.get(p['document_id'],{}).get('type') in ['Contract','Purchase Order']]
    for p in eligible:
        if budget<=0:break
        original=p['text'];text=original[:min(16000,budget)];budget-=len(text)
        pages.append({'document_id':p['document_id'],'page':p['number'],'text':text,'truncated':len(text)<len(original)})
    return {'documents':[{'id':d['id'],'type':d['type'],'name':d['name']} for d in documents],
            'shared_explicit_references':links,'contract_pages':pages,
            'contract_context_incomplete':len(pages)<len(eligible) or any(p['truncated'] for p in pages),
            'extracted_clause_record_ids':[r['id'] for r in records if r['key'] in ['shipment_terms','payment_terms','incoterms']]}

def contextual_assessment(case_id,documents,records,key,group):
    if not case_id or key not in contextual_candidates(documents,records):return None
    saved=db.one('SELECT * FROM packet_reviews WHERE case_id=?',(case_id,))
    if not saved or saved['error'] or saved['signature']!=signature(documents,records):return None
    ids={r['id'] for r in group}
    return next((c for c in json.loads(saved['payload']) if c['key']=='ai-context:'+key
                 and {s['id'] for s in c['detail']['sources']}==ids),None)

def semantic_difference(check,records):
    """AI prose cannot override equal, typed source values (including cached reviews)."""
    from .validation import comparison_values,port_detail_compatible
    index={r['id']:r for r in records if r['status']!='rejected'}
    group=[index[s['id']] for s in check['detail'].get('sources',[]) if s['id'] in index]
    if len(group)<2:return False
    if all(r['kind']=='field' for r in group):
        if group[0]['key'] in ['port_loading','port_discharge'] and port_detail_compatible(group):return False
        values=comparison_values(group[0]['key'],group,list(index.values()))
        if all(v is not None for v in values) and len(set(values))==1:return False
    return True

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
            'open_count':sum(not c.get('resolution') for c in issues),'mismatch_count':sum((c['result']=='Mismatch' or c['detail'].get('category')=='difference') and not c.get('resolution') for c in issues),
            'ai_state':state,'ai_error':saved['error'] if saved and state=='error' else '',
            'scope':'Một hồ sơ = một lô hàng. Nguồn kế hoạch, hợp đồng giao nhiều đợt và dữ liệu chưa rõ đơn vị được cảnh báo riêng, không tự kết luận sai.'}

def run_ai_review(case_id,documents,records,source_pages=None):
    """AI only suggests semantic issues over existing IDs; never creates or corrects data."""
    from . import ai
    from pydantic import Field,create_model
    from typing import List,Literal
    active=[r for r in records if r['status']!='rejected']
    descriptions=[r for r in active if r['kind']=='field' and r['key']=='cargo_description']
    needs_description=len({r['document_id'] for r in descriptions})>=2
    candidates=contextual_candidates(documents,active)
    class Issue(ai.Strict):
        field_id:str
        record_ids:List[str]=Field(min_length=2,max_length=12)
        reason:str=Field(min_length=5,max_length=1000)
    class DescriptionAssessment(ai.Strict):
        record_ids:List[str]=Field(min_length=2,max_length=30)
        relation:Literal['compatible','contradiction','uncertain']
        reason:str=Field(min_length=5,max_length=1000)
    # The server binds each required assessment to its complete source group.
    # Do not ask the model to copy long ID lists (which can omit a valid source).
    context_models={key:(create_model('Context_'+key,__base__=ai.Strict,
        relation=(Literal['compatible','contradiction','insufficient_context'],...),
        contradicting_record_ids=(List[Literal[tuple(r['id'] for r in group)]],Field(max_length=2)),
        context_record_ids=(List[str],Field(max_length=20)),
        reason=(str,Field(min_length=5,max_length=1000))),...) for key,group in candidates.items()}
    ContextualAssessments=create_model('ContextualAssessments',__base__=ai.Strict,**context_models)
    class Review(ai.Strict):
        issues:List[Issue]=Field(max_length=40)
        description_assessments:List[DescriptionAssessment]=Field(default_factory=list,min_length=1 if needs_description else 0,max_length=1)
        contextual_assessments:ContextualAssessments=Field(default_factory=ContextualAssessments)
    sig=signature(documents,records);output=[];error=''
    try:
        if len(active)>350:raise ValueError('Hồ sơ hơn 350 bản ghi; chưa chạy đối chiếu ngữ nghĩa AI. Đối chiếu số liệu vẫn hoạt động.')
        payload=[{**s,'field_id':r['key'],'kind':r['kind']} for r,s in zip(active,sources(active,documents))]
        policy=(db.ROOT/'docs'/'AI_SHIPMENT_CONSISTENCY.md').read_text(encoding='utf-8')
        response=ai.OpenAI(api_key=ai.key(),timeout=60,max_retries=1).responses.parse(model=ai._model,store=False,text_format=Review,
            input=[{'role':'system','content':ai.NO_INFERENCE_POLICY+'\n'+policy},
                   {'role':'user','content':db.encode({'records':payload,
                       'description_comparison_record_ids':[r['id'] for r in descriptions] if needs_description else [],
                       'contextual_comparisons':[{'field_id':k,'record_ids':[r['id'] for r in g]} for k,g in candidates.items()],
                       'packet_context':packet_context(documents,active,source_pages)})}],
            **({'temperature':0} if ai._model.startswith(('gpt-4.1','gpt-4o')) else {}))
        db.execute('INSERT INTO ai_usage VALUES (?,?,?,?,?,?,?)',(db.uid(),case_id,db.now(),ai._model,getattr(response.usage,'input_tokens',None),getattr(response.usage,'output_tokens',None),'packet-consistency'))
        if response.output_parsed is None:raise ValueError('AI chưa trả kết quả đối chiếu có cấu trúc.')
        index={r['id']:r for r in active};seen=set()
        assessed=set()
        for key,group in candidates.items():
            assessment=getattr(response.output_parsed.contextual_assessments,key)
            ids={r['id'] for r in group};context_ids=list(dict.fromkeys(assessment.context_record_ids))
            if any(i not in index for i in context_ids):continue
            opposing=set(assessment.contradicting_record_ids)
            if assessment.relation=='contradiction' and (len(opposing)!=2 or not opposing<=ids
                    or len({index[i]['document_id'] for i in opposing})!=2):continue
            if assessment.relation=='contradiction':
                pair={'detail':{'sources':sources([index[i] for i in opposing],documents)}}
                if not semantic_difference(pair,active):continue
            if assessment.relation!='contradiction' and opposing:continue
            output.append({'key':'ai-context:'+key,
                'result':'Needs Verification' if assessment.relation=='contradiction' else 'Not Yet Checked','severity':'warning',
                'detail':{'reason':assessment.reason,'sources':sources(group,documents),
                          'method':'OpenAI related-document contextual comparison','relation':assessment.relation,
                          'context_sources':sources([index[i] for i in context_ids],documents),
                          **({'category':'difference','contradicting_record_ids':sorted(opposing)} if opposing else {})}})
            assessed.add(key);seen.add(key)
        if assessed!=set(candidates):raise ValueError('AI chưa đối chiếu đủ các trường theo ngữ cảnh hoặc dẫn nguồn không hợp lệ; giữ đối chiếu gốc, không tự duyệt.')
        for assessment in response.output_parsed.description_assessments:
            ids=list(dict.fromkeys(assessment.record_ids))
            if (set(ids)!={r['id'] for r in descriptions} or len(ids)<2
                    or len({r['document_id'] for r in descriptions})<2):continue
            output.append({'key':'ai-description:cargo_description',
                'result':'Needs Verification' if assessment.relation=='contradiction' else 'Not Yet Checked','severity':'warning',
                'detail':{'reason':assessment.reason,'sources':sources(descriptions,documents),
                          'method':'OpenAI contextual description comparison','relation':assessment.relation,
                          **({'category':'difference'} if assessment.relation=='contradiction' else {})}})
            seen.add('cargo_description')
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
            check={'key':'ai-semantic:'+issue.field_id,'result':'Needs Verification','severity':'warning',
                   'detail':{'reason':'AI gợi ý cần so sánh: '+issue.reason,'sources':sources(group,documents),'method':'OpenAI semantic suggestion','category':'difference'}}
            if semantic_difference(check,active):output.append(check)
    except Exception as exc:
        error=str(exc)[:500] if isinstance(exc,ValueError) else ai.safe_error(exc)
    db.execute('INSERT OR REPLACE INTO packet_reviews VALUES (?,?,?,?,?)',(case_id,sig,db.encode(output),error,db.now()))
    return error

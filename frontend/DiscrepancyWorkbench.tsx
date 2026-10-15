import React,{useEffect,useRef,useState} from 'react';
import {AlertTriangle,ArrowRight,Check,Download,Eye,FileText,Loader2,X} from 'lucide-react';
import {api,patch,post,textValue,label} from './api';

function SourceCard({source,record,onSaved,disabled,documentLabel}:any){
  const [value,setValue]=useState(textValue(record?.value||source.value));
  const [note,setNote]=useState('');const [error,setError]=useState('');const [saving,setSaving]=useState(false);
  const [data,setData]=useState<any>(null);const [show,setShow]=useState(false);const anchor=useRef<HTMLSpanElement>(null);
  useEffect(()=>{setValue(textValue(record?.value||source.value));setError('');},[record?.version,source.id]);
  useEffect(()=>{if(!show||!record)return;let active=true;setError('');setData(null);
    api('/records/'+record.id+'/source').then(v=>{if(active)setData(v);}).catch(e=>{if(active)setError(e.message);});
    return()=>{active=false;};},[show,record?.id,record?.version]);
  async function save(e:React.FormEvent){e.preventDefault();setSaving(true);setError('');try{
    const b=await patch('/records/'+record.id,{value,note:note.trim(),version:record.version});await onSaved(b);setNote('');
  }catch(e:any){setError(e.message);}finally{setSaving(false);}}
  return <article className="conflict-source">
    <header><FileText size={17}/><div><strong>{source.document}</strong><small>{documentLabel||source.type} · Trang {source.page||'—'}</small></div></header>
    <div className="conflict-value"><small>Giá trị đang đối chiếu</small><strong>{textValue(record?.value||source.value)||'Chưa đọc được'}</strong></div>
    <details className="conflict-evidence" open><summary>Bằng chứng máy đọc</summary><blockquote>{record?.evidence||source.evidence||'Chưa có trích dẫn; mở bản gốc để kiểm tra.'}</blockquote>
      <small>Giá trị đọc gốc: {typeof (record?.raw??source.raw)==='object'?JSON.stringify(record?.raw??source.raw):String(record?.raw??source.raw??'—')}</small></details>
    {record?.value?.warning&&<p className="warning-text">{record.value.warning}</p>}
    {record&&<button className="btn small" onClick={()=>setShow(!show)} aria-expanded={show}><Eye size={15}/>{show?'Ẩn bản gốc':'Hiện bản gốc có đánh dấu'}</button>}
    {show&&!data&&!error&&<p role="status"><Loader2 className="spin" size={16}/> Đang định vị nguồn…</p>}
    {show&&data&&<><p className="muted">{data.message||'Khung xanh đánh dấu chữ khớp; kiểm cả nhãn và đơn vị.'}</p><div className="conflict-preview"><div className="source-image"><img alt={`Nguồn ${source.document}, trang ${source.page}`} src={`/api/documents/${data.document_id}/preview/${data.page}`} onLoad={()=>anchor.current?.scrollIntoView({block:'nearest'})}/>
      {(data.boxes||[]).map((b:any,i:number)=><span key={i} ref={i===0?anchor:undefined} className="source-box" style={{left:100*b.x+'%',top:100*b.y+'%',width:100*b.w+'%',height:100*b.h+'%'}} title={b.text}/>)}</div></div></>}
    {record&&<details className="conflict-edit"><summary>Nhập lại giá trị làm việc</summary>
      <p className="muted">Chỉ sửa ô đã đọc sai hoặc giá trị đã được xác nhận có căn cứ. Nếu giấy tờ gốc sai, yêu cầu bản sửa từ khách; PDF gốc luôn được giữ lại.</p>
      <form onSubmit={save}>
        <label className="form-label">Giá trị của {source.document}
          {record.kind==='field'?<input required value={value} onChange={e=>setValue(e.target.value)}/>:<textarea required value={typeof value==='string'?value:JSON.stringify(value)} onChange={e=>setValue(e.target.value)}/>}
        </label>
        <label className="form-label">Căn cứ sửa (bắt buộc)<textarea required minLength={5} value={note} onChange={e=>setNote(e.target.value)}/></label>
        <button className="btn primary small" disabled={disabled||saving||note.trim().length<5||record.kind!=='field'}>{saving?'Đang lưu…':'Lưu & đối chiếu lại'}</button>
        {record.kind!=='field'&&<p className="muted">Dùng “Mở chứng từ” để sửa từng ô dòng hàng.</p>}
      </form></details>}
    {error&&<p className="alert bad" role="alert">{error}</p>}
  </article>;
}

export function DiscrepancyWorkbench({current,dict,busy,onSaved,onDocuments,onSource,onExport}:any){
  const report=current.consistency||{issues:[],gaps:[],matched:[],single_source:[],open_count:0,mismatch_count:0,ai_state:'not_run'};
  const running=current.active_job?.status==='running';
  const [filter,setFilter]=useState('open');const [selected,setSelected]=useState('');const [note,setNote]=useState('');const [error,setError]=useState('');const [saving,setSaving]=useState(false);
  const dialog=useRef<HTMLDivElement>(null);const opener=useRef<HTMLElement|null>(null);
  const all=[...report.issues,...report.gaps,...report.matched,...report.single_source];
  const chosen=all.find((c:any)=>c.key===selected);
  const list=filter==='gaps'?report.gaps:filter==='matched'?report.matched:filter==='single'?report.single_source:filter==='resolved'?report.issues.filter((c:any)=>c.resolution):report.issues.filter((c:any)=>!c.resolution&&(filter!=='mismatch'||c.result==='Mismatch'));
  const title=(c:any)=>c.title||dict.fields[c.key.replace(/^(?:field|ai-semantic|missing):/,'')]?.label||c.key;
  function close(){setSelected('');setNote('');setError('');opener.current?.focus();}
  useEffect(()=>{if(!selected)return;dialog.current?.focus();const key=(e:KeyboardEvent)=>{
    if(e.key==='Escape'){e.preventDefault();close();}
    if(e.key==='Tab'){const elements=Array.from(dialog.current?.querySelectorAll<HTMLElement>('button:not(:disabled),input,textarea,summary,a[href]')||[]).filter(e=>e.getClientRects().length>0);const first=elements[0],last=elements[elements.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus();}}
  };document.addEventListener('keydown',key);return()=>document.removeEventListener('keydown',key);},[selected]);
  async function resolve(e:React.FormEvent){e.preventDefault();setSaving(true);setError('');try{await onSaved(await post('/checks/'+chosen.id+'/resolve',{note:note.trim()}));close();}catch(e:any){setError(e.message);}finally{setSaving(false);}}
  return <div className="discrepancy-workbench">
    <section className="surface padded exception-heading"><div><span className="badge info">Kết quả sau khi đọc chứng từ</span><h2>Sai lệch & xử lý</h2><p>AI đọc nội dung, hệ thống đối chiếu các nguồn trong cùng hồ sơ. Bạn chỉ cần xử lý những điểm khác nhau hoặc chưa đủ chắc chắn.</p></div><button className="btn" onClick={onExport}><Download size={16}/> Xuất báo cáo</button></section>
    <div className="exception-stats" aria-live="polite"><div><strong>{report.mismatch_count}</strong><span>Sai lệch</span></div><div><strong>{report.open_count-report.mismatch_count}</strong><span>Cần làm rõ</span></div><div><strong>{report.matched.length}</strong><span>Chỉ tiêu khớp</span></div><div><strong>{report.single_source.length}</strong><span>Mới có một nguồn</span></div></div>
    {running?<p className="alert" role="status">AI đang đọc và đối chiếu toàn bộ hồ sơ. Danh sách dưới đây chưa phải kết quả cuối; chờ hoàn tất trước khi xử lý.</p>:report.ai_state!=='completed'&&<p className="alert warn" role="status">{report.ai_state==='stale'?'Dữ liệu đã sửa: đối chiếu số liệu đã cập nhật; chạy AI lại để cập nhật nhận xét ngữ nghĩa.':report.ai_state==='error'?`Chưa hoàn tất đối chiếu ngữ nghĩa AI: ${report.ai_error}`:'Chưa chạy đối chiếu ngữ nghĩa OpenAI cho hồ sơ này. Kết quả dưới đây là đối chiếu dữ liệu đã đọc.'}</p>}
    <div className="filter-pills">{[['open',`Cần xử lý (${report.open_count})`],['mismatch',`Sai lệch (${report.mismatch_count})`],['gaps',`Thiếu nguồn (${report.gaps.length})`],['matched',`Khớp (${report.matched.length})`],['single',`Một nguồn (${report.single_source.length})`],['resolved','Đã ghi nhận']].map(([id,text])=><button key={id} className={'pill-btn '+(filter===id?'active':'')} onClick={()=>setFilter(id)}>{text}</button>)}</div>
    <section className="exception-list" aria-label="Danh sách điểm cần xử lý">
      {list.map((c:any)=><article key={c.key} className={'surface exception-row '+(c.result==='Mismatch'?'is-mismatch':'')}>
        <div><span className={'badge '+(c.resolution?'good':c.result==='Mismatch'?'bad':'warn')}>{c.resolution?'Đã ghi nhận':label(c.result)}</span><h3>{title(c)}</h3><p>{c.detail.reason}</p>
          <div className="exception-values">{(c.detail.sources||[]).slice(0,3).map((s:any)=><span key={s.id}><small>{s.document} · tr.{s.page||'—'}</small><strong>{textValue(s.value)||'—'}</strong></span>)}</div>
          {c.resolution&&<p className="muted">Căn cứ đã ghi: {c.resolution}</p>}
        </div><button className="btn" onClick={e=>{opener.current=e.currentTarget;setSelected(c.key);setNote(c.resolution||'');}}><Eye size={16}/> Xem lý do</button>
      </article>)}
      {!list.length&&<div className="surface padded exception-empty"><Check size={25}/><h3>Không có mục trong nhóm này</h3><p>Không phát hiện sai lệch không có nghĩa là hồ sơ đã đầy đủ. Xem “Thiếu nguồn” và “Một nguồn” để biết phạm vi đã đối chiếu.</p><button className="btn" onClick={onDocuments}>Mở chứng từ <ArrowRight size={15}/></button></div>}
    </section>
    {chosen&&<div className="modal-overlay" onClick={e=>{if(e.target===e.currentTarget)close();}}><div ref={dialog} className="conflict-dialog" role="dialog" aria-modal="true" aria-labelledby="conflict-title" tabIndex={-1}>
      <header className="conflict-head"><div><span className="badge warn">So sánh bằng chứng</span><h2 id="conflict-title">{title(chosen)}</h2></div><button className="icon-btn" aria-label="Đóng so sánh" onClick={close}><X size={21}/></button></header>
      <p className="conflict-reason">{chosen.detail.reason}</p><p className="muted">Mỗi ô bên dưới giữ riêng tài liệu, trang và giá trị gốc. Không tự chọn nguồn đúng và không sửa đồng loạt các chứng từ để làm cho khớp.</p>
      <div className="conflict-grid">{(chosen.detail.sources||[]).map((s:any)=><SourceCard key={s.id} source={s} documentLabel={dict.document_labels?.[s.type]} record={current.records.find((r:any)=>r.id===s.id)} onSaved={onSaved} disabled={busy}/>)}</div>
      {!(chosen.detail.sources||[]).length&&<p className="alert warn">Chưa có đủ trường nguồn. Tải bổ sung chứng từ hoặc mở tệp gốc để nhập giá trị có căn cứ.</p>}
      <div className="row"><button className="btn" onClick={()=>{close();onDocuments();}}>Mở chứng từ</button>{(chosen.detail.sources||[]).filter((s:any)=>current.records.some((r:any)=>r.id===s.id)).map((s:any)=><button key={s.id} className="text-btn" onClick={()=>{close();onSource(current.records.find((r:any)=>r.id===s.id));}}>Mở vùng nguồn · {s.document}</button>)}</div>
      {['Mismatch','Needs Verification'].includes(chosen.result)&&!chosen.key.startsWith('reading:')&&<form className="conflict-resolution" onSubmit={resolve}><h3>Hai bản gốc thực sự khác nhau?</h3><p>Yêu cầu khách gửi bản sửa, hoặc ghi rõ lý do chấp nhận khác biệt về phạm vi / phiên bản. Ghi nhận không làm thay đổi các giá trị gốc.</p><label className="form-label">Lý do và căn cứ xử lý<textarea required minLength={5} value={note} onChange={e=>setNote(e.target.value)}/></label><button className="btn" disabled={busy||saving||note.trim().length<5}>{saving?'Đang lưu…':'Ghi nhận cách xử lý'}</button></form>}
      {error&&<p className="alert bad" role="alert">{error}</p>}
    </div></div>}
  </div>;
}

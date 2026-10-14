import React, {useEffect,useRef,useState} from 'react';
import {AlertTriangle,Check,ChevronRight,Loader2,X,ZoomIn,ZoomOut} from 'lucide-react';
import {api,textValue} from './api';

function SourceText({text,raw,evidence}:any) {
  const anchor=useRef<HTMLElement>(null);
  const chars:string[]=[];const positions:number[]=[];
  for(let i=0;i<text.length;i++) {
    const ch=/\s/.test(text[i])?' ':text[i].toLowerCase();
    if(ch===' ' && chars[chars.length-1]===' ')continue;
    chars.push(ch);positions.push(i);
  }
  const candidates=[typeof raw==='string'?raw:'',evidence?.split('\n[')[0] || ''].filter(Boolean);
  let start=-1,end=-1;
  for(const candidate of candidates) {
    const query=candidate.toLowerCase().replace(/\s+/g,' ').trim();
    const found=chars.join('').indexOf(query);
    if(found>=0){start=positions[found];end=positions[found+query.length-1]+1;break;}
  }
  useEffect(()=>{anchor.current?.scrollIntoView({block:'center'});},[text,raw,evidence]);
  return <pre>{start<0?text:<>{text.slice(0,start)}<mark ref={anchor}>{text.slice(start,end)}</mark>{text.slice(end)}</>}</pre>;
}

export function SourceInspector({record,title,reason,busy,onClose,onVerify,onNext,onEdit,onSave}:any) {
  const [data,setData]=useState<any>(null);
  const [error,setError]=useState('');
  const [attempt,setAttempt]=useState(0);
  const [zoom,setZoom]=useState(100);
  const [showText,setShowText]=useState(false);
  const [editing,setEditing]=useState(false);
  const [draft,setDraft]=useState(textValue(record.value));
  const [saving,setSaving]=useState(false);
  const editor=useRef<HTMLInputElement>(null);
  const first=useRef<HTMLSpanElement>(null);
  const loadKey=record.id+':'+record.version;
  useEffect(()=>{setDraft(textValue(record.value));setEditing(false);},[loadKey]);
  async function saveAndVerify() {
    setSaving(true);setError('');
    try {
      const saved=record.kind==='field' && draft!==textValue(record.value)?await onSave(record,draft):record;
      if(saved)await onVerify(saved);
    } finally {setSaving(false);}
  }
  async function saveDraft() {
    if(draft===textValue(record.value))return;
    setSaving(true);setError('');try {await onSave(record,draft);}finally{setSaving(false);}
  }
  useEffect(()=>{
    let active=true;setData(null);setError('');setZoom(100);setShowText(false);
    api('/records/'+record.id+'/source').then(d=>{if(active)setData(d);}).catch(e=>{if(active)setError(e.message);});
    return ()=>{active=false;};
  },[loadKey,attempt]);
  const scroll=()=>first.current?.scrollIntoView({block:'center',inline:'center',behavior:'smooth'});
  const raw=typeof record.raw==='string'?record.raw:textValue(record.raw);
  return <section className="source-inspector" aria-label="Đối chiếu vùng nguồn">
    <header className="source-inspector-head"><div><strong>{title}</strong><small>{data?`${data.name} · trang ${data.page}`:'Đang tìm trang nguồn…'}</small></div>
      <button className="icon-btn" aria-label="Đóng vùng nguồn" onClick={onClose}><X size={17}/></button></header>
    <div className="source-value"><span>Giá trị đang làm việc</span>{editing && record.kind==='field'?
      <div className="source-inline-editor"><input ref={editor} aria-label="Sửa giá trị tại nguồn" value={draft} onChange={e=>setDraft(e.target.value)} disabled={saving||busy}/><button className="btn small" disabled={saving||busy||!draft.trim()} onClick={saveDraft}>Lưu sửa</button></div>:<strong>{textValue(record.value)||'—'}</strong>}
      {raw && raw!==textValue(record.value) && <small>Máy đọc gốc: {raw}</small>}
      <p>{reason || 'Chưa được nhân viên xác minh; chưa có nghĩa là máy đọc sai.'}</p></div>
    {error && <div className="source-notice" role="alert"><p>{error}</p><button className="btn small" onClick={()=>setAttempt(attempt+1)}>Thử định vị lại</button></div>}
    {!data && !error && <div className="source-loading" role="status"><Loader2 className="spin" size={20}/> Đang định vị chữ trên bản gốc…</div>}
    {data && <>
      <div className="source-controls"><button className="text-btn" onClick={scroll}>Tới vùng đánh dấu</button><div className="row">
        <button className="icon-btn" aria-label="Thu nhỏ vùng nguồn" onClick={()=>setZoom(Math.max(80,zoom-20))}><ZoomOut size={16}/></button><span>{zoom}%</span>
        <button className="icon-btn" aria-label="Phóng to vùng nguồn" onClick={()=>setZoom(Math.min(240,zoom+20))}><ZoomIn size={16}/></button>
        <button className="text-btn" onClick={()=>setShowText(!showText)}>{showText?'Bản gốc':'Chữ OCR / PDF'}</button></div></div>
      {(data.message || data.ambiguous || data.low_confidence_words.length>0) && <div className="source-notice" role="status"><AlertTriangle size={16}/><div>
        {data.message && <p>{data.message}</p>}
        {data.ambiguous && <p>Có nhiều vị trí chữ khớp. Kiểm tra nhãn và dòng hàng trước khi chọn giá trị.</p>}
        {data.low_confidence_words.length>0 && <p>OCR đọc chưa chắc: {[...new Set(data.low_confidence_words.map((w:any)=>`${w.text} (${Math.round(w.confidence)}/100)`))].join(', ')}. Điểm OCR không phải xác suất dữ liệu đúng.</p>}
      </div></div>}
      <div className="source-canvas">
        {showText || !['.pdf','.jpg','.jpeg','.png','.tif','.tiff'].includes(data.ext)?
          <div className="source-text"><strong>Câu trích dẫn máy dùng</strong><blockquote>{data.evidence||'Chưa có câu trích dẫn.'}</blockquote><SourceText text={data.text} raw={data.raw} evidence={data.evidence}/></div>:
          <div className="source-image" style={{width:zoom+'%'}}><img alt={`Bản gốc ${data.name}, trang ${data.page}, có đánh dấu nguồn`} src={`/api/documents/${data.document_id}/preview/${data.page}`} onLoad={scroll}/>
            {data.boxes.map((b:any,i:number)=><span key={i} ref={i===0?first:undefined} className={'source-box'+(b.confidence!==null && b.confidence<70?' low':'')}
              style={{left:100*b.x+'%',top:100*b.y+'%',width:100*b.w+'%',height:100*b.h+'%'}} title={`${b.text} · ${b.layer}${b.confidence===null?'':` · OCR ${Math.round(b.confidence)}/100`}`}/>)}</div>}
      </div>
      <p className="source-legend">Khung xanh: chữ khớp nguồn · Cam: OCR có điểm nhận chữ thấp. Khung đánh dấu không tự xác nhận đúng/sai nghiệp vụ.</p>
      <details className="source-quote"><summary>Câu trích dẫn và chất lượng đọc</summary><blockquote>{data.evidence||'Chưa có trích dẫn.'}</blockquote><p>{data.quality||'Lớp chữ PDF; vẫn cần đối chiếu nội dung.'}</p></details>
    </>}
    <footer className="source-review-actions"><button className="btn small" disabled={saving||busy} onClick={()=>{
      if(record.kind!=='field'){onEdit();return;}setEditing(true);setTimeout(()=>editor.current?.focus(),0);
    }}>Sửa giá trị</button>
      <button className="btn small primary" disabled={busy||saving||!draft.trim()||record.status==='verified'||!!record.value?.warning||!data} onClick={saveAndVerify}><Check size={15}/> {saving?'Đang lưu…':'Đúng, xác minh & tiếp'}</button>
      <button className="text-btn" disabled={busy||saving} onClick={()=>{
        if(draft!==textValue(record.value)){setError('Bạn đang sửa giá trị. Bấm Lưu sửa trước khi chuyển mục, hoặc đóng và mở lại nguồn để bỏ bản sửa chưa lưu.');return;}onNext();
      }}>Để sau, mục tiếp <ChevronRight size={15}/></button></footer>
  </section>;
}

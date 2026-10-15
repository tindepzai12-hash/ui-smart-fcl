import React,{useEffect,useRef,useState} from 'react';
import {Crosshair,Search,ZoomIn,ZoomOut} from 'lucide-react';

/** The image and its source boxes share one coordinate system at every scale. */
export function SourceImageViewer({src,alt,boxes=[]}:any){
  const [zoom,setZoom]=useState(100),[magnify,setMagnify]=useState(false);
  const [point,setPoint]=useState<any>(null),[loaded,setLoaded]=useState(false),[failed,setFailed]=useState(false);
  const viewport=useRef<HTMLDivElement>(null),image=useRef<HTMLDivElement>(null);
  const first=useRef<HTMLSpanElement>(null),pending=useRef(false);
  const jump=()=>{
    const v=viewport.current,b=first.current;if(!v||!b)return;
    const vr=v.getBoundingClientRect(),br=b.getBoundingClientRect();
    v.scrollTo({left:v.scrollLeft+br.left-vr.left-v.clientWidth/2+br.width/2,
      top:v.scrollTop+br.top-vr.top-v.clientHeight/2+br.height/2});
  };
  useEffect(()=>{setZoom(100);setPoint(null);setLoaded(false);setFailed(false);},[src]);
  useEffect(()=>{if(loaded)jump();},[loaded]);
  useEffect(()=>{if(pending.current){pending.current=false;jump();}setPoint(null);},[zoom]);
  function change(next:number){pending.current=true;setZoom(Math.max(75,Math.min(400,next)));}
  function move(e:React.PointerEvent){
    if(!magnify||!loaded)return;
    const r=image.current?.getBoundingClientRect(),v=viewport.current?.getBoundingClientRect();if(!r||!v)return;
    setPoint({x:Math.max(0,Math.min(r.width,e.clientX-r.left)),y:Math.max(0,Math.min(r.height,e.clientY-r.top)),
      left:Math.max(90,Math.min(v.width-90,e.clientX-v.left)),top:Math.max(90,Math.min(v.height-90,e.clientY-v.top)),width:r.width});
  }
  const marks=(anchor:boolean)=>(boxes||[]).map((b:any,i:number)=><span key={i} ref={anchor&&i===0?first:undefined}
    className={'source-box'+(b.confidence!=null&&b.confidence<70?' low':'')}
    style={{left:100*b.x+'%',top:100*b.y+'%',width:100*b.w+'%',height:100*b.h+'%'}} title={b.text}/>);
  return <section className="source-viewer" aria-label="Xem phóng to bản gốc">
    <div className="source-zoom-tools">
      <button className="icon-btn" aria-label="Thu nhỏ bản gốc" disabled={zoom<=75||!loaded} onClick={()=>change(zoom-25)}><ZoomOut size={17}/></button>
      <output aria-live="polite" aria-label="Mức phóng to">{zoom}%</output>
      <button className="icon-btn" aria-label="Phóng to bản gốc" disabled={zoom>=400||!loaded} onClick={()=>change(zoom+25)}><ZoomIn size={17}/></button>
      <button className="btn small" disabled={!loaded} onClick={()=>{change(100);jump();}}>Vừa khung</button>
      <button className={'btn small '+(magnify?'active':'')} aria-pressed={magnify} disabled={!loaded} onClick={()=>{setMagnify(!magnify);setPoint(null);}}><Search size={16}/> Kính lúp</button>
      {!!boxes.length&&<button className="btn small" disabled={!loaded} onClick={jump}><Crosshair size={16}/> Vùng đánh dấu</button>}
    </div>
    <p className="source-zoom-help">{magnify?'Rê chuột hoặc chạm và kéo trên giấy để soi bằng kính lúp 2,5×.':'Bấm + để phóng to; cuộn ngang/dọc để xem phần ngoài khung.'}</p>
    <div className="source-viewer-stage">
      <div ref={viewport} className="source-zoom-viewport" tabIndex={0} aria-label="Bản gốc có thể cuộn ngang và dọc"
        onScroll={()=>setPoint(null)}>
        <div ref={image} className={'source-image '+(magnify?'magnifying':'')} style={{width:zoom+'%'}}
          onPointerMove={move} onPointerDown={e=>{if(magnify){e.currentTarget.setPointerCapture(e.pointerId);move(e);}}}
          onPointerLeave={()=>setPoint(null)} onPointerUp={e=>{if(e.pointerType!=='mouse')setPoint(null);}} onPointerCancel={()=>setPoint(null)}>
          <img alt={alt} src={src} draggable={false} onLoad={()=>setLoaded(true)} onError={()=>{setFailed(true);setLoaded(false);}}/>{marks(true)}
        </div>
      </div>
      {magnify&&point&&<div className="source-magnifier" aria-hidden="true" style={{left:point.left,top:point.top}}>
        <div className="source-image" style={{position:'absolute',width:point.width*2.5,left:90-point.x*2.5,top:90-point.y*2.5}}>
          <img alt="" src={src}/>{marks(false)}
        </div>
      </div>}
    </div>
    {failed&&<p className="alert bad" role="alert">Không tải được ảnh bản gốc. Đóng và mở lại vùng nguồn để thử lại.</p>}
  </section>;
}

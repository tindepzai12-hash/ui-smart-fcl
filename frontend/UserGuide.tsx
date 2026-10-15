import React from 'react';
import {BookOpen,Printer} from 'lucide-react';
import guide from './guide-content.json';

export function UserGuide(){return <article className="user-guide">
  <div className="page-heading"><div><h1><BookOpen size={25}/> Hướng dẫn nhân viên xử lý hồ sơ</h1><p>{guide.intro}</p></div><div className="row"><a className="btn" href="/huong-dan.html" download="HUONG_DAN_UI_SMART.html">Tải hướng dẫn</a><button className="btn" onClick={()=>window.print()}><Printer size={16}/> In / lưu PDF</button></div></div>
  <p className="guide-intro">{guide.scope}</p>
  <section aria-labelledby="guide-example"><h2 id="guide-example">{guide.scenario.title}</h2><p>{guide.scenario.notice}</p><dl className="guide-facts">{guide.scenario.facts.map(([label,value])=><div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl></section>
  <nav className="guide-contents" aria-label="Các bước xử lý hồ sơ"><strong>Nhân viên làm theo thứ tự</strong><ol>{guide.steps.map((s,i)=><li key={s.id}><a href={'#guide-'+s.id} onClick={e=>{e.preventDefault();document.getElementById('guide-'+s.id)?.focus();}}>Bước {i+1}: {s.title}</a></li>)}</ol></nav>
  {guide.steps.map((s,i)=><section className="guide-step" id={'guide-'+s.id} key={s.id} tabIndex={-1}><h2>Bước {i+1}. {s.title}</h2><dl><dt>Việc nhân viên làm</dt><dd>{s.task}</dd><dt>Thao tác trên web</dt><dd>{s.action}</dd><dt>Kiểm tra trong bộ ví dụ</dt><dd>{s.check}</dd><dt>Khi nào chuyển bước?</dt><dd>{s.done}</dd><dt>Nếu chưa đạt</dt><dd>{s.problem}</dd></dl></section>)}
  <section className="guide-step"><h2>Các tình huống để biết phải xử lý thế nào</h2><dl>{guide.examples.map(s=><React.Fragment key={s.title}><dt>{s.title}</dt><dd>{s.action}</dd></React.Fragment>)}</dl></section>
  <section className="guide-step"><h2>Phần việc thực hiện bên ngoài U&I SMART</h2><ul>{guide.external.map(text=><li key={text}>{text}</li>)}</ul><p>{guide.limitation}</p><p>Nguồn nghiệp vụ: <a href={guide.source.url} target="_blank" rel="noreferrer">{guide.source.title}</a>. {guide.source.note}</p></section>
  <section className="guide-step"><h2>Khi gặp vấn đề với web</h2><dl>{guide.problems.map(([title,text])=><React.Fragment key={title}><dt>{title}</dt><dd>{text}</dd></React.Fragment>)}</dl></section>
</article>}

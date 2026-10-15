import React, { useState } from 'react';

type Group = { start: number; end: number; type: string };

export function PdfSplit({ document: doc, types, loading, submit }: any) {
  const total = doc.pages.length;
  const initial: Group[] = doc.split_suggestion?.length > 1 ? doc.split_suggestion :
    [{ start: 1, end: 1, type: doc.type }, { start: 2, end: total, type: 'Other' }];
  const [groups, setGroups] = useState<Group[]>(initial);
  const [preview, setPreview] = useState(1);
  let cursor = 1;
  let valid = groups.length >= 2 && groups.length <= 30;
  for (const group of groups) {
    valid = valid && Number.isInteger(group.start) && Number.isInteger(group.end) && group.start === cursor && group.end >= group.start && group.end <= total;
    cursor = group.end + 1;
  }
  valid = valid && cursor === total + 1;
  const edit = (index: number, patch: Partial<Group>) => setGroups(previous => previous.map((g, i) => i === index ? { ...g, ...patch } : g));
  return <section className="pdf-split">
    <h2>Tách bộ PDF thành từng chứng từ</h2>
    <p className="muted">{doc.name} · {total} trang. Kiểm tra khoảng trang và loại chứng từ. File gốc được giữ để tải lại; dữ liệu tách vẫn chờ bạn xác minh.</p>
    <div className="split-preview-controls row">
      <label>Xem trang gốc <select aria-label="Trang PDF gốc" value={preview} onChange={e => setPreview(Number(e.target.value))}>
        {doc.pages.map((p: any) => <option key={p.number} value={p.number}>{p.number}</option>)}
      </select></label>
      <small>Gợi ý theo tiêu đề từng trang; kiểm tra cả các trang tiếp nối.</small>
    </div>
    <a href={`/api/documents/${doc.id}/preview/${preview}`} target="_blank" rel="noopener noreferrer" title="Mở ảnh trang gốc để đọc rõ"><img className="split-preview" src={`/api/documents/${doc.id}/preview/${preview}`} alt={`Bản gốc trang ${preview} - bấm để phóng lớn`} /></a>
    <small>Bấm ảnh để mở trang gốc và đọc rõ trước khi phân nhóm.</small>
    <form onSubmit={e => { e.preventDefault(); if (valid && !loading) submit({ groups }); }}>
      <div className="split-groups">
        {groups.map((g, i) => <fieldset key={i} disabled={loading}>
          <legend>Chứng từ {i + 1}</legend>
          <div className="split-range">
            <label>Từ trang<input aria-label={`Chứng từ ${i+1} từ trang`} type="number" min="1" max={total} required value={g.start || ''} onChange={e => edit(i, { start: Number(e.target.value) })} /></label>
            <label>Đến trang<input aria-label={`Chứng từ ${i+1} đến trang`} type="number" min="1" max={total} required value={g.end || ''} onChange={e => edit(i, { end: Number(e.target.value) })} /></label>
            <label>Loại chứng từ<select aria-label={`Chứng từ ${i+1} loại`} value={g.type} onChange={e => edit(i, { type: e.target.value })}>{Array.from(new Set([...types, 'Invoice & Packing List', 'Other', g.type])).map((t: any) => <option key={t}>{t}</option>)}</select></label>
          </div>
          <button className="text-btn danger" type="button" disabled={groups.length <= 2} onClick={() => setGroups(previous => previous.filter((_, n) => n !== i))}>Bỏ nhóm trang này</button>
        </fieldset>)}
      </div>
      <button className="btn small" type="button" disabled={loading || groups.length >= 30} onClick={() => setGroups(previous => [...previous, { start: previous.at(-1)!.end + 1, end: total, type: 'Other' }])}>Thêm nhóm trang</button>
      {!valid && <p className="warning-text" role="alert">Phân bổ liên tiếp đủ trang 1–{total}; không để trùng hoặc bỏ sót trang.</p>}
      <div className="modal-actions"><button className="btn primary" disabled={!valid || loading}>{loading ? 'Đang tách…' : `Tách thành ${groups.length} chứng từ`}</button></div>
    </form>
  </section>;
}

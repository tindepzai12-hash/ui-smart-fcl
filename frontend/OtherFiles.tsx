import React, { useEffect, useState } from 'react';
import { api } from './api';

function OtherFile({ file, types, disabled, onRestore }: any) {
  const [kind, setKind] = useState(types.includes(file.type) ? file.type : '');
  const [show, setShow] = useState(false);
  const [page, setPage] = useState(1);
  const [text, setText] = useState('');
  const [error, setError] = useState('');
  const [reading, setReading] = useState(false);
  const visual = ['.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff'].includes(file.ext);
  useEffect(() => {
    if (!show || visual) return;
    let cancelled = false;
    setReading(true); setText(''); setError('');
    api(`/documents/${file.id}/pages/${page}`).then((p: any) => {
      if (!cancelled) setText(p.text);
    }).catch(() => {
      if (!cancelled) setError('Chưa có văn bản đã đọc. Tải bản gốc để kiểm tra.');
    }).finally(() => { if (!cancelled) setReading(false); });
    return () => { cancelled = true; };
  }, [show, page, file.id, visual]);
  return <li className="other-file">
    <div className="other-file-heading">
      <div><strong>{file.name}</strong><span className="badge">{file.type === 'Other' ? 'Chưa xác định loại' : file.type}</span></div>
      <div className="row">
        <button className="btn small" aria-expanded={show} onClick={() => { setShow(!show); setError(''); }}>{show ? 'Đóng bản gốc' : 'Xem bản gốc'}</button>
        <a className="btn small" href={`/api/documents/${file.id}/original`} download>Tải bản gốc</a>
      </div>
    </div>
    <p>{file.collection_reason || 'Tệp được giữ riêng; không tính vào checklist chính.'}</p>
    {file.classification_evidence && <p className="muted">Căn cứ nhận diện: {file.classification_evidence}</p>}
    {show && <div className="other-preview">
      {file.pages?.length > 1 && <label>Trang / khối nội dung
        <select value={page} onChange={e => { setPage(Number(e.target.value)); setError(''); }}>
          {file.pages.map((p: any) => <option key={p.number} value={p.number}>{p.number}</option>)}
        </select>
      </label>}
      {visual ? <img src={`/api/documents/${file.id}/preview/${page}`} alt={`Bản gốc ${file.name}, trang ${page}`} onError={() => setError('Không mở được hình xem trước. Tải bản gốc để kiểm tra.')} />
        : <pre>{reading ? 'Đang mở nội dung đã đọc…' : text}</pre>}
      {error && <p role="alert">{error}</p>}
    </div>}
    <div className="other-restore">
      <label>Máy phân loại nhầm? Chọn loại đúng
        <select value={kind} disabled={disabled} onChange={e => setKind(e.target.value)}>
          <option value="">Chọn loại chứng từ chính</option>
          {types.map((t: string) => <option key={t} value={t}>{t === 'Contract' ? 'Hợp đồng / Sales Contract' : t === 'Purchase Order' ? 'Đơn đặt hàng / PO' : t}</option>)}
        </select>
      </label>
      <button className="btn small" disabled={disabled || !kind} onClick={() => onRestore(file, kind)}>Đưa vào bộ chính</button>
    </div>
  </li>;
}

export function OtherFiles({ files, types, disabled, onRestore }: any) {
  return <details className="other-files" open={files.length > 0}>
    <summary>Giấy tờ khác ({files.length})</summary>
    <p>Tệp ngoài phạm vi chứng từ được giữ ở đây sau khi đọc và nhận diện. B/L và tờ khai thuộc bộ đối chiếu. Tệp chưa rõ loại cần xem lại bản gốc.</p>
    {files.length ? <ul>{files.map((file: any) => <OtherFile key={file.id} file={file} types={types} disabled={disabled} onRestore={onRestore} />)}</ul>
      : <p className="muted">Chưa có giấy tờ khác. Tải tất cả tệp ở “Thêm chứng từ”; hệ thống sẽ phân nhóm sau khi đọc.</p>}
  </details>;
}

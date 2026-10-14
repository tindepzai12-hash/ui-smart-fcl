import React, { useState } from 'react';
import { Camera, Upload, Download, FileText, ArrowRight } from 'lucide-react';

export function ReferenceFiles({ files, busy, onUpload, onMove }: {
  files: any[]; busy: boolean;
  onUpload: (files: FileList | File[]) => void;
  onMove: (id: string) => void;
}) {
  const [selected, setSelected] = useState('');
  const active = files.find(f => f.id === selected) || files[0];
  return <section className="reference-files" aria-label="Bộ ảnh riêng">
    <div className="reference-heading">
      <div><h2><Camera size={22} /> Ảnh hiện trường & màn hình</h2>
        <p>Ảnh container, seal, hàng hóa và màn hình tra cứu được xem ở đây. Bộ này không tham gia đối chiếu chứng từ hoặc xuất bảng kê.</p>
        <p className="reference-hint">Ảnh chụp giấy Invoice, Packing List, B/L… tải vào <strong>Chứng từ</strong>. Nếu đưa nhầm vào đây, chọn “Chuyển về Chứng từ”.</p>
      </div>
      <label className={'btn upload-btn' + (busy ? ' disabled' : '')}><Upload size={16} /> Thêm ảnh vào bộ riêng
        <input aria-label="Tải ảnh hiện trường hoặc màn hình" type="file" multiple accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff" hidden disabled={busy}
          onChange={e => { if (e.target.files) onUpload(e.target.files); e.target.value = ''; }} />
      </label>
    </div>
    {!files.length ? <div className="empty reference-empty"><Camera size={32} /><h3>Chưa có ảnh trong bộ riêng</h3><p>Tải ảnh bằng nút phía trên hoặc kéo nhiều ảnh vào vùng này.</p>
      <p>Không cần thêm ảnh để hoàn thành hồ sơ chứng từ.</p>
    </div> : <div className="reference-layout">
      <aside aria-label="Danh sách ảnh riêng">{files.map(f => <button key={f.id} className={'reference-item' + (active?.id === f.id ? ' selected' : '')} onClick={() => setSelected(f.id)}>
        {f.ext === '.pdf' ? <FileText size={18} /> : <Camera size={18} />}<span><strong>{f.name}</strong><small>{Math.ceil(f.size / 1024)} KB · Bộ ảnh riêng</small></span>
      </button>)}</aside>
      {active && <div className="reference-preview">
        <div className="reference-actions"><strong>{active.name}</strong><div className="row">
          <a className="btn small" href={`/api/documents/${active.id}/original`} download><Download size={15} /> Tải bản gốc</a>
          <button className="btn small" disabled={busy} onClick={() => onMove(active.id)}>Chuyển về Chứng từ <ArrowRight size={15} /></button>
        </div></div>
        {active.collection_reason && <p className="reference-reason">Lý do phân nhóm: {active.collection_reason}</p>}
        <img src={`/api/documents/${active.id}/preview/1`} alt={`Xem bản gốc: ${active.name}`} onError={e => { e.currentTarget.alt = 'Không xem trước được tệp; chọn Tải bản gốc để kiểm tra.'; }} />
        {['.pdf', '.tif', '.tiff'].includes(active.ext) && <small>Đang xem trang/khung đầu tiên. Tải bản gốc để xem toàn bộ.</small>}
      </div>}
    </div>}
    <div className="reference-drop" onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); if (!busy) onUpload(Array.from(e.dataTransfer.files)); }}>
      <Upload size={18} /><span>Kéo ảnh vào bộ riêng · JPG, PNG, TIFF hoặc PDF · 25 MB/tệp · tối đa 30 tệp/lần</span>
    </div>
  </section>;
}

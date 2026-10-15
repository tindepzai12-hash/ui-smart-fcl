export async function api(path: string, options: RequestInit = {}) {
  let res: Response;
  try { res = await fetch('/api' + path, {
    ...options,
    headers: {
      'X-UI-Smart': 'local',
      ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...options.headers,
    },
  }); } catch { throw new Error('Không kết nối được máy chủ. Chờ máy chủ khởi động rồi thử lại.'); }
  const data = await res.json().catch(() => ({ detail: 'Máy chủ trả dữ liệu không đọc được. Hãy thử lại.' }));
  if (!res.ok) {
    if (res.status === 401 && data.code === 'auth_required' && typeof window !== 'undefined') window.location.assign('/__cloud/login');
    if (typeof data.detail === 'string') throw new Error(data.detail);
    if (data.detail?.message && Array.isArray(data.detail?.blockers)) {
      throw new Error(data.detail.message + ': ' + data.detail.blockers.join('; '));
    }
    if (res.status === 422) throw new Error('Thông tin nhập chưa hợp lệ. Kiểm tra các ô bắt buộc, độ dài và lý do xử lý.');
    throw new Error(res.status >= 500 ? 'Máy chủ gặp lỗi xử lý. Hãy thử lại hoặc xem nhật ký local.' : 'Không thực hiện được thao tác. Tải lại hồ sơ và thử lại.');
  }
  return data;
}

export const post = (path: string, body: unknown = {}) =>
  api(path, { method: 'POST', body: JSON.stringify(body) });

export const patch = (path: string, body: unknown) =>
  api(path, { method: 'PATCH', body: JSON.stringify(body) });

export const textValue = (v: any): string => {
  if (v == null) return '';
  if (typeof v === 'string') return v;
  if (v.number != null) return v.number + (v.unit ? ' ' + v.unit : '');
  if (typeof v.text === 'string') return v.text;
  if (v.container_number) {
    const parts = [v.container_number];
    if (v.seal_number) parts.push('Seal: ' + v.seal_number);
    if (v.container_type) parts.push('Loại: ' + v.container_type);
    if (v.packages) parts.push('Kiện: ' + v.packages);
    if (v.gross_weight) parts.push('GW: ' + v.gross_weight);
    return parts.join(' · ');
  }
  if (v.description) {
    const qty = v.quantity ? `${v.quantity} ${v.unit || ''}`.trim() : '';
    const amt = v.line_amount ? `${v.line_amount} ${v.currency || ''}`.trim() : '';
    return [v.product_code ? `[${v.product_code}]` : '', v.description, qty, amt].filter(Boolean).join(' · ');
  }
  return '';
};

export const statusLabel: Record<string, string> = {
  Draft: 'Bản nháp (Draft)',
  Uploaded: 'Đã tải file',
  Reading: 'Đang xử lý',
  'Needs verification': 'Cần xử lý',
  'Ready for review': 'Đã có kết quả',
  Reviewed: 'Đã kiểm tra (Reviewed)',
  Exported: 'Đã xuất Reviewed',
  pending: 'Chờ xác minh',
  verified: 'Đã xác minh',
  rejected: 'Đã từ chối',
  Matched: 'Khớp',
  Mismatch: 'Sai lệch',
  Missing: 'Thiếu',
  'Needs Verification': 'Cần kiểm tra',
  'Not Applicable': 'Không áp dụng',
  'Not Yet Checked': 'Chưa đủ nguồn',
  uploaded: 'Đã tải',
  read: 'Đã đọc',
  error: 'Lỗi',
  reading: 'Đang đọc',
  needs_split: 'Chờ tách PDF',
  saving: 'Đang lưu…',
  saved: 'Đã lưu',
  save_error: 'Lưu lỗi',
};

export const label = (s: string): string => statusLabel[s] || s;

export const tone = (s: string): string =>
  ['verified', 'Matched', 'Reviewed', 'Exported', 'read', 'saved'].includes(s)
    ? 'good'
    : ['Mismatch', 'error', 'rejected', 'save_error'].includes(s)
    ? 'bad'
    : ['Missing', 'pending', 'Needs Verification', 'Needs verification', 'needs_split', 'saving'].includes(s)
    ? 'warn'
    : 'neutral';

export function unitLabel(docOrExt: any, pageNum?: number | null, totalPages?: number | null): string {
  if (!pageNum && !totalPages) return '';
  const ext = (typeof docOrExt === 'string' ? docOrExt : docOrExt?.ext || '').toLowerCase();
  const method = (typeof docOrExt === 'object' ? docOrExt?.reading_method || docOrExt?.method || '' : '').toLowerCase();
  let prefix = 'Trang';
  if (ext === '.xlsx' || ext === '.xls' || method.includes('excel')) {
    prefix = 'Sheet';
  } else if (ext === '.docx' || method.includes('word')) {
    prefix = 'Khối Word';
  } else if (ext === '.txt' || ext === '.csv' || method.includes('text')) {
    prefix = 'Khối văn bản';
  }
  if (pageNum && totalPages) return `${prefix} ${pageNum}/${totalPages}`;
  if (pageNum) return `${prefix} ${pageNum}`;
  return prefix;
}

export function physicalContainerStats(records: any[] = [], documents: any[] = []) {
  const docsMap: Record<string, string> = {};
  for (const d of documents || []) docsMap[d.id] = d.name;
  const active = (records || []).filter((r: any) => r.kind === 'container' && r.status !== 'rejected');
  const byNumber: Record<string, { container_number: string; seals: string[]; types: string[]; sources: string[]; records: any[]; hasConflict: boolean }> = {};
  for (const r of active) {
    const num = String(r.value?.container_number || '').replace(/\s+/g, '').toUpperCase();
    if (!num) continue;
    if (!byNumber[num]) {
      byNumber[num] = { container_number: num, seals: [], types: [], sources: [], records: [], hasConflict: false };
    }
    const entry = byNumber[num];
    entry.records.push(r);
    const seal = String(r.value?.seal_number || '').trim().toUpperCase();
    if (seal && !entry.seals.includes(seal)) entry.seals.push(seal);
    const ctype = String(r.value?.container_type || '').trim().toUpperCase();
    if (ctype && !entry.types.includes(ctype)) entry.types.push(ctype);
    const srcName = docsMap[r.document_id] || 'Nhập tay';
    if (!entry.sources.includes(srcName)) entry.sources.push(srcName);
  }
  for (const entry of Object.values(byNumber)) {
    entry.hasConflict = entry.seals.length > 1 || entry.types.length > 1;
  }
  const groups = Object.values(byNumber);
  return {
    physicalCount: groups.length,
    sourceRecordCount: active.length,
    groups,
  };
}

export function humanCheckTitle(key: string, fieldsDict: Record<string, any> = {}, documents: any[] = []): { title: string; category: string } {
  const docsMap: Record<string, any> = {};
  for (const d of documents || []) docsMap[d.id] = d;
  if (key.startsWith('document:')) {
    const docKind = key.slice('document:'.length);
    return { title: `Chứng từ: ${docKind}`, category: 'Checklist chứng từ' };
  }
  if (key.startsWith('reading:')) {
    const docId = key.slice('reading:'.length);
    return { title: `Đọc tệp: ${docsMap[docId]?.name || 'Tài liệu'}`, category: 'Đọc / OCR' };
  }
  if (key.startsWith('classification:')) {
    const docId = key.slice('classification:'.length);
    return { title: `Phân loại: ${docsMap[docId]?.name || 'Tài liệu'}`, category: 'Xác nhận loại chứng từ' };
  }
  if (key.startsWith('transport:')) {
    const docId = key.slice('transport:'.length);
    return { title: `Phương thức vận tải: ${docsMap[docId]?.name || 'Tài liệu'}`, category: 'Kiểm tra nghiệp vụ FCL' };
  }
  if (key.startsWith('missing:')) {
    const sub = key.slice('missing:'.length);
    if (sub === 'items') return { title: 'Dữ liệu dòng hàng độc lập', category: 'Dữ liệu cốt lõi' };
    if (sub === 'containers') return { title: 'Dữ liệu container vận chuyển', category: 'Dữ liệu cốt lõi' };
    return { title: fieldsDict[sub]?.label || sub, category: 'Dữ liệu cốt lõi' };
  }
  if (key.startsWith('field:')) {
    const sub = key.slice('field:'.length);
    return { title: fieldsDict[sub]?.label || sub, category: 'Đối chiếu chỉ tiêu' };
  }
  if (key.startsWith('arithmetic:')) {
    return { title: 'Kiểm tra số lượng × đơn giá = thành tiền', category: 'Số học dòng hàng Invoice' };
  }
  if (key.startsWith('total:')) {
    const docId = key.slice('total:'.length);
    return { title: `Tổng các dòng hàng vs Tổng trị giá hóa đơn (${docsMap[docId]?.name || 'Invoice'})`, category: 'Số học tổng Invoice' };
  }
  if (key.startsWith('container:')) {
    const num = key.slice('container:'.length);
    return { title: `Container vật lý ${num}`, category: 'Đối chiếu Container & Seal' };
  }
  if (key.startsWith('container-weight:')) return { title: `Trọng lượng riêng container ${key.split(':')[1]}`, category: 'Đối chiếu trọng lượng' };
  return { title: key, category: 'Quy tắc kiểm tra' };
}

export function computeStepStates(current: any) {
  if(current?.consistency){
    const r=current.consistency,docs=current.documents||[],read=docs.length>0&&docs.every((d:any)=>d.status==='read');
    return [
      {index:1,label:'Tải chứng từ',tab:'documents',done:docs.length>0,partial:false,detail:`${docs.length} tệp · cùng một lô`},
      {index:2,label:'AI đọc & đối chiếu',tab:'documents',done:read&&r.ai_state==='completed',partial:docs.length>0&&(!read||r.ai_state!=='completed'),detail:r.ai_state==='completed'?'Đã đọc toàn hồ sơ':read?'Đã đọc · xem phạm vi AI':'Chưa đọc xong'},
      {index:3,label:'Xử lý sai lệch',tab:'comparison',done:read&&r.open_count===0,partial:r.open_count>0,detail:`${r.open_count} điểm cần xử lý`},
      {index:4,label:'Xuất báo cáo',tab:'export',done:(current.exports||[]).some((e:any)=>e.case_revision===current.case.revision),partial:false,detail:'Giữ nguồn & lịch sử'},
    ];
  }
  const docs = current?.documents || [];
  const records = (current?.records || []).filter((r: any) => r.status !== 'rejected');
  const checks = current?.checks || [];
  const hasDocs = docs.length > 0;
  const allRead = hasDocs && docs.every((d: any) => d.status === 'read' && !!d.type_verified);
  const pending = records.filter((r: any) => r.status !== 'verified' || r.value?.warning).length;
  const unresolved = checks.filter((c: any) => ['Mismatch', 'Missing', 'Needs Verification'].includes(c.result) && !c.resolution);
  const prepared = records.length > 0 && !unresolved.some((c: any) => c.key.startsWith('missing:'));
  const reviewed = !!current?.case?.reviewed_at && (current?.blockers || []).length === 0;
  const exported = reviewed && (current?.exports || []).some((e: any) => e.mode === 'Reviewed' && e.case_revision === current?.case?.revision);
  const draft = (current?.exports || []).some((e: any) => e.mode === 'Draft') && !exported;
  if (current?.case?.requirements?.Booking && current?.case?.requirements?.Contract) return [
    {index:1,label:'Tải & nhận diện',tab:'documents',done:allRead,partial:hasDocs&&!allRead,detail:`${docs.length} tệp · ${docs.filter((d:any)=>!d.type_verified || d.status!=='read').length} cần xử lý`},
    {index:2,label:'Kiểm trường',tab:'review',done:records.length>0&&pending===0,partial:pending>0,detail:`${pending} bản ghi cần kiểm`},
    {index:3,label:'Đối chiếu',tab:'comparison',done:checks.length>0&&unresolved.length===0,partial:unresolved.length>0,detail:`${unresolved.length} mục chưa xử lý`},
    {index:4,label:'Checklist',tab:'customs',done:prepared,partial:hasDocs&&!prepared,detail:prepared?'Đủ trường cốt lõi':'Kiểm 5 nhóm chứng từ'},
    {index:5,label:'Duyệt & xuất Excel',tab:'export',done:exported,partial:records.length>0&&!exported,detail:exported?'Đã xuất Reviewed':reviewed?'Sẵn sàng xuất':draft?'Đã xuất bản nháp':'Chưa hoàn thành kiểm tra'},
  ];
  return [
    { index: 1, label: 'Tạo hồ sơ', tab: 'documents', done: !!current?.case?.id, partial: false, detail: current?.case?.id ? 'Đã tạo' : 'Chưa tạo' },
    { index: 2, label: 'Nạp chứng từ', tab: 'documents', done: hasDocs, partial: false, detail: `${docs.length} tệp` },
    { index: 3, label: 'Đọc & nhận diện', tab: 'documents', done: allRead, partial: hasDocs && !allRead, detail: `${docs.filter((d: any) => d.status !== 'read' || !d.type_verified).length} tệp cần xử lý` },
    { index: 4, label: 'Xác minh trường', tab: 'review', done: records.length > 0 && pending === 0, partial: records.length > 0 && pending > 0, detail: `${pending} bản ghi cần kiểm` },
    { index: 5, label: 'Đối chiếu chéo', tab: 'comparison', done: checks.length > 0 && unresolved.length === 0, partial: unresolved.length > 0, detail: `${unresolved.length} mục chưa xử lý` },
    { index: 6, label: 'Chuẩn bị bảng kê', tab: 'customs', done: prepared, partial: records.length > 0 && !prepared, detail: prepared ? 'Đủ dữ liệu cốt lõi / đã xử lý miễn' : 'Còn thiếu dữ liệu cốt lõi' },
    { index: 7, label: 'Kiểm tra xuất file', tab: 'review', done: reviewed, partial: records.length > 0 && !reviewed, detail: reviewed ? 'Đã duyệt Reviewed' : `${(current?.blockers || []).length} điều kiện chặn` },
    { index: 8, label: 'Xuất Excel', tab: 'export', done: exported, partial: draft, detail: exported ? 'Đã xuất Reviewed' : draft ? 'Mới xuất bản Draft' : 'Chưa xuất' },
  ];
}

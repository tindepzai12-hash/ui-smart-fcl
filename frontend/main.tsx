import React, { useEffect, useState, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import {
  LayoutDashboard, FolderOpen, FileCheck2, History, Settings, PanelLeftClose,
  Plus, ArrowRight, FileText, Upload, ChevronLeft, ChevronRight, Search,
  Check, AlertTriangle, Download, RotateCw, ZoomIn, ZoomOut, ShieldCheck,
  X, Loader2, Trash2, Undo2, Eye, FileSpreadsheet, HardDrive, Link2
} from 'lucide-react';
import '@fontsource/inter/latin-400.css';
import '@fontsource/inter/latin-500.css';
import '@fontsource/inter/latin-600.css';
import '@fontsource/inter/latin-700.css';
import '@fontsource/inter/vietnamese-400.css';
import '@fontsource/inter/vietnamese-500.css';
import '@fontsource/inter/vietnamese-600.css';
import '@fontsource/inter/vietnamese-700.css';
import {
  api, post, patch, textValue, label, tone, unitLabel,
  physicalContainerStats, humanCheckTitle, computeStepStates
} from './api';
import './styles.css';
import { TemplateCenter } from './TemplateCenter';

type Any = any;

export const Badge = ({ status }: Any) => (
  <span className={'badge ' + tone(status)}>
    {status === 'verified' || status === 'Matched' ? <Check size={12} /> : null}
    {label(status)}
  </span>
);

export function HighlightedText({ text, query }: Any) {
  if (!query) return <pre>{text}</pre>;
  const i = String(text || '').toLowerCase().indexOf(String(query).toLowerCase());
  return (
    <pre>
      {i < 0 ? (
        text
      ) : (
        <>
          {text.slice(0, i)}
          <mark>{text.slice(i, i + query.length)}</mark>
          {text.slice(i + query.length)}
        </>
      )}
    </pre>
  );
}

export function StepTracker({ current, onSelectTab }: Any) {
  const steps = computeStepStates(current);
  return (
    <div className="steps" aria-label="Quy trình tám bước">
      {steps.map((s: Any) => (
        <button
          type="button"
          aria-label={`Bước ${s.index}: ${s.label}`}
          key={s.label}
          className={s.done ? 'done' : s.partial ? 'partial' : ''}
          onClick={() => onSelectTab && onSelectTab(s.tab)}
          style={{ cursor: onSelectTab ? 'pointer' : 'default' }}
          title={`Bước ${s.index}: ${s.label} — ${s.detail}`}
        >
          <span>{s.done ? <Check size={13} /> : s.index}</span>
          <div className="step-meta">
            <strong>{s.label}</strong>
            <small>{s.detail}</small>
          </div>
        </button>
      ))}
    </div>
  );
}

export function ContainerSummaryBanner({ records, documents, checks = [] }: Any) {
  const stats = physicalContainerStats(records, documents);
  if (!stats.sourceRecordCount) return null;
  return (
    <div className="container-summary-bar" role="region" aria-label="Tổng hợp container vật lý và nguồn">
      <div>
        <strong>
          {stats.physicalCount} container vật lý duy nhất · {stats.sourceRecordCount} bản ghi nguồn
        </strong>
        <p className="muted">
          Đếm theo số container; các bản ghi từ Packing List và B/L được giữ riêng để đối chiếu và truy vết.
        </p>
      </div>
      {checks.filter((c: Any) => (c.key === 'field:gross_weight' || c.key.startsWith('container-weight:')) && ['Mismatch', 'Needs Verification'].includes(c.result) && !c.resolution).map((c: Any) => <p className="warning-text" key={c.key}>Trọng lượng cần kiểm tra: {c.detail.reason}</p>)}
      <div className="container-chips">
        {stats.groups.map((g: Any) => (
          <span
            key={g.container_number}
            className={'badge ' + (g.hasConflict ? 'bad' : g.records.length > 1 ? 'good' : 'neutral')}
          >
            {g.container_number} · {g.records.length} nguồn ({g.sources.join(', ')})
            {g.hasConflict ? ' · Lệch Seal/Loại' : g.seals.length ? ` · Seal ${g.seals.join('/')}` : ''}
          </span>
        ))}
      </div>
    </div>
  );
}

const date = (s: string) =>
  new Date(s).toLocaleString('vi-VN', { dateStyle: 'short', timeStyle: 'short' });

function App() {
  const [view, setView] = useState('overview');
  const [collapsed, setCollapsed] = useState(false);
  const [cases, setCases] = useState<Any[]>([]);
  const [health, setHealth] = useState<Any>(null);
  const [dict, setDict] = useState<Any>({ fields: {}, document_types: [] });
  const [current, setCurrent] = useState<Any>(null);
  const [tab, setTab] = useState('documents');
  const [toast, setToast] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [dialog, setDialog] = useState<Any>(null);
  const [job, setJob] = useState<Any>(null);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('');
  const [sort, setSort] = useState('updated');
  const [audit, setAudit] = useState<Any[]>([]);

  const [selectedDoc, setSelectedDoc] = useState('');
  const [page, setPage] = useState(1);
  const [pageData, setPageData] = useState<Any>(null);
  const [zoom, setZoom] = useState(100);
  const [rotation, setRotation] = useState(0);
  const [recordGroup, setRecordGroup] = useState('field');
  const [recordFilter, setRecordFilter] = useState('all');
  const [recordSearch, setRecordSearch] = useState('');
  const [documentTypes, setDocumentTypes] = useState<Record<string, string>>({});
  const savesInFlight = useRef<Partial<Record<string, Promise<Any>>>>({});
  const [docScopeOnly, setDocScopeOnly] = useState(true);
  const [checkFilter, setCheckFilter] = useState('all');
  const [highlight, setHighlight] = useState('');
  const [findText, setFindText] = useState('');
  const [mode, setMode] = useState('local');
  const [consent, setConsent] = useState(false);
  const [exportMode, setExportMode] = useState('Draft');
  const [workbookType, setWorkbookType] = useState('A');
  const [selectedFields, setSelectedFields] = useState<string[]>([]);
  const [showText, setShowText] = useState(false);
  const [saveStates, setSaveStates] = useState<Record<string, { status: string; message?: string }>>({});
  const [activeRecordId, setActiveRecordId] = useState('');

  const refresh = async () => {
    const [c, h, d] = await Promise.all([api('/cases'), api('/health'), api('/dictionary')]);
    setCases(c);
    setHealth(h);
    setDict(d);
    return c;
  };

  const notify = (s: string) => {
    setToast(s);
    setTimeout(() => setToast(''), 4200);
  };

  const run = async (fn: () => Promise<Any>, message = '') => {
    setError('');
    setLoading(true);
    try {
      const result = await fn();
      if (message) notify(message);
      return result;
    } catch (e: Any) {
      setError(e.message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const replace = (b: Any) => {
    if (b?.case) {
      setCurrent((previous: Any) => previous?.case?.id === b.case.id && previous.case.revision > b.case.revision ? previous : b);
      if (!selectedDoc && b.documents.length) setSelectedDoc(b.documents[0].id);
    }
    return b;
  };

  useEffect(() => {
    run(refresh);
    const parsed = new URLSearchParams(location.hash.replace('#', ''));
    const id = parsed.get('case');
    if (id) openCase(id);
  }, []);

  useEffect(() => {
    if (!job || job.status !== 'running') return;
    let active = true;
    const timer = setInterval(async () => {
      try {
        const j = await api('/jobs/' + job.id);
        if (!active) return;
        setJob(j);
        if (j.status !== 'running') {
          replace(await api('/cases/' + j.case_id));
          await refresh();
          if (j.status === 'completed') {
            if (j.errors?.length) {
              setError(j.errors.map((err: Any) => `${err.document}: ${err.error}`).join('\n'));
            }
            notify('Đã xử lý. Kiểm tra nguồn và xác minh từng giá trị.');
          } else {
            notify('Tác vụ đã dừng. Dữ liệu được giữ lại.');
          }
        }
      } catch (e: Any) {
        setError(e.message);
        clearInterval(timer);
      }
    }, 1000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [job?.id, job?.status]);

  useEffect(() => {
    setPageData(null);
    const doc = current?.documents.find((d: Any) => d.id === selectedDoc);
    if (!doc || doc.status !== 'read') return;
    let active = true;
    api(`/documents/${selectedDoc}/pages/${page}`)
      .then((p) => {
        if (active) setPageData(p);
      })
      .catch((e: Any) => { if (active) setError(e.message); });
    return () => {
      active = false;
    };
  }, [selectedDoc, page, current?.case.updated_at]);

  async function openCase(id: string) {
    const b = await run(() => api('/cases/' + id));
    if (b) {
      setCurrent(b);
      setView('case');
      setTab('documents');
      setSelectedDoc(b.documents[0]?.id || '');
      setPage(1);
      setRotation(0);
      setHighlight('');
      setSaveStates({});
      location.hash = 'case=' + id;
    }
  }

  function go(v: string) {
    setView(v);
    setError('');
    if (v === 'history') run(async () => setAudit(await api('/audit')));
  }

  const update = (fn: () => Promise<Any>, msg = '') =>
    run(async () => {
      const b = await fn();
      replace(b);
      await refresh();
      return b;
    }, msg);

  useEffect(() => {
    if (!dialog) return;
    const old = document.activeElement as HTMLElement;
    const modal = document.querySelector<HTMLElement>('.modal');
    const focusable = () =>
      Array.from(
        modal?.querySelectorAll<HTMLElement>(
          'button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),a[href]'
        ) || []
      );
    focusable()
      .find((e) => e.tagName !== 'BUTTON')
      ?.focus();
    const trap = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setDialog(null);
        return;
      }
      if (e.key === 'Tab') {
        const list = focusable();
        const first = list[0];
        const last = list[list.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener('keydown', trap);
    return () => {
      document.removeEventListener('keydown', trap);
      old?.focus();
    };
  }, [dialog?.kind]);

  const activeDoc = current?.documents.find((d: Any) => d.id === selectedDoc);
  const allGroupRecords = current?.records.filter((r: Any) => r.kind === recordGroup) || [];
  const scopedRecords = allGroupRecords.filter(
    (r: Any) => !docScopeOnly || !selectedDoc || r.document_id === selectedDoc || !r.document_id
  );
  const filterRecordsFn = (list: Any[]) =>
    list.filter((r: Any) => {
      const term = recordSearch.trim().toLocaleLowerCase('vi');
      if (term && ![dict.fields[r.key]?.label, r.key, textValue(r.value), JSON.stringify(r.raw)].join(' ').toLocaleLowerCase('vi').includes(term)) return false;
      const blockedByCheck = current?.checks.some((c: Any) => ['Missing', 'Mismatch', 'Needs Verification'].includes(c.result) && !c.resolution && c.detail.sources?.some((s: Any) => s.id === r.id));
      if (recordFilter === 'blocked') return r.status !== 'rejected' && (r.status !== 'verified' || !!r.value?.warning || blockedByCheck);
      if (recordFilter === 'pending') return r.status === 'pending';
      if (recordFilter === 'warning') return r.status !== 'rejected' && (!!r.value?.warning || blockedByCheck);
      if (recordFilter === 'verified') return r.status === 'verified';
      return true;
    });
  const activeRecords = filterRecordsFn(scopedRecords);
  const reviewRecords = filterRecordsFn(allGroupRecords);
  const pending = current?.records.filter((r: Any) => r.status === 'pending').length || 0;
  const unresolved =
    current?.checks.filter(
      (c: Any) => ['Mismatch', 'Missing', 'Needs Verification'].includes(c.result) && !c.resolution
    ) || [];
  const containerStats = physicalContainerStats(current?.records || [], current?.documents || []);

  const filtered = cases
    .filter(
      (c) =>
        (c.name + ' ' + c.id + ' ' + c.customer).toLowerCase().includes(search.toLowerCase()) &&
        (!filter || c.status === filter)
    )
    .sort((a, b) =>
      sort === 'name'
        ? a.name.localeCompare(b.name)
        : sort === 'created'
        ? b.created_at.localeCompare(a.created_at)
        : b.updated_at.localeCompare(a.updated_at)
    );

  async function upload(files: FileList | File[]) {
    if (!files.length) return;
    const f = new FormData();
    Array.from(files).forEach((file) => f.append('files', file));
    await run(async () => {
      const result = await api('/cases/' + current.case.id + '/documents', { method: 'POST', body: f });
      replace(result.bundle);
      await refresh();
      const failed = result.results.filter((r: Any) => r.status !== 'uploaded');
      if (failed.length) setError(failed.map((r: Any) => r.name + ': ' + r.error).join('\n'));
      notify('Đã nhận ' + result.results.filter((r: Any) => r.status === 'uploaded').length + ' file');
    });
  }

  async function loadSampleSet(conflict: boolean) {
    if (current.documents.length) {
      setError('Bộ mẫu chỉ nạp vào hồ sơ trống. Tạo hồ sơ riêng để thử nghiệm, tránh trộn với chứng từ đang làm.');
      return;
    }
    const files = await run(async () => {
      const names = ['invoice.txt', 'packing.txt', conflict ? 'bl-conflict.txt' : 'bl.txt'];
      return Promise.all(names.map(async (name) => {
        const response = await fetch('/api/samples/' + name);
        if (!response.ok) throw new Error('Không tải được bộ mẫu local.');
        return new File([await response.blob()], name, { type: 'text/plain' });
      }));
    });
    if (files) await upload(files);
  }

  function chooseSource(r: Any) {
    setActiveRecordId(r.id || '');
    if (r.document_id) {
      setSelectedDoc(r.document_id);
      setPage(r.page || 1);
      setHighlight(r.evidence || '');
      setTab('documents');
      setShowText(true);
    }
  }

  function jumpToNextPending() {
    if (!current?.records?.length) return;
    setTab('documents');
    setRecordFilter('all');
    setRecordSearch('');
    const pendingList = current.records.filter((r: Any) => r.status === 'pending');
    if (!pendingList.length) {
      notify('Tất cả bản ghi đã được xác minh.');
      return;
    }
    const idx = pendingList.findIndex((r: Any) => r.id === activeRecordId);
    const next = pendingList[(idx + 1) % pendingList.length];
    setRecordGroup(next.kind);
    setActiveRecordId(next.id);
    if (next.document_id) {
      setSelectedDoc(next.document_id);
      setPage(next.page || 1);
      setHighlight(next.evidence || '');
      setShowText(true);
    }
    setTimeout(() => {
      const el = document.getElementById('card-' + next.id) || document.getElementById('field-' + next.id);
      el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      if (el && 'focus' in el) (el as HTMLElement).focus();
    }, 60);
  }

  async function saveRecordValue(r: Any, value: Any) {
    const unchanged =
      (r.kind === 'field' ? textValue(r.value) : JSON.stringify(r.value)) ===
      (typeof value === 'string' ? value : JSON.stringify(value));
    if (unchanged) return r;
    if (r.kind === 'field' && typeof value === 'string' && !value.trim()) {
      setSaveStates((prev) => ({
        ...prev,
        [r.id]: { status: 'save_error', message: 'Giá trị không được để trống; dùng Từ chối nếu muốn bỏ bản ghi sai.' },
      }));
      return null;
    }
    setSaveStates((prev) => ({ ...prev, [r.id]: { status: 'saving' } }));
    try {
      const b = await patch('/records/' + r.id, {
        value,
        note: 'Hiệu chỉnh theo bản gốc',
        version: r.version,
      });
      replace(b);
      await refresh();
      setSaveStates((prev) => ({ ...prev, [r.id]: { status: 'saved', message: 'Đã lưu · cần xác minh lại' } }));
      notify('Đã lưu · cần xác minh lại');
      return b.records.find((x: Any) => x.id === r.id) || r;
    } catch (e: Any) {
      setSaveStates((prev) => ({ ...prev, [r.id]: { status: 'save_error', message: e.message } }));
      setError(e.message);
      return null;
    }
  }

  async function editRecord(r: Any, value: Any): Promise<Any> {
    if (savesInFlight.current[r.id]) {
      const saved = await savesInFlight.current[r.id];
      if (!saved) return null;
      r = saved;
    }
    const task = saveRecordValue(r, value);
    savesInFlight.current[r.id] = task;
    try { return await task; }
    finally { if (savesInFlight.current[r.id] === task) delete savesInFlight.current[r.id]; }
  }

  async function verifyRecord(r: Any, status: string) {
    let targetRecord = savesInFlight.current[r.id] ? await savesInFlight.current[r.id] : r;
    if (!targetRecord) return;
    if (r.kind === 'field') {
      const inputEl = document.getElementById('field-' + r.id) as HTMLInputElement | null;
      if (inputEl && inputEl.value !== textValue(targetRecord.value)) {
        const updated = await editRecord(targetRecord, inputEl.value);
        if (!updated) return;
        targetRecord = updated;
      }
    }
    const note =
      targetRecord.note ||
      (targetRecord.key === 'hs_code' || targetRecord.key === 'tax_rate' || targetRecord.key === 'customs_value'
        ? prompt('Ghi căn cứ pháp lý/xác minh cho chỉ tiêu này:')
        : 'Đã đối chiếu chứng từ gốc');
    if (note === null) return;
    setSaveStates((prev) => ({ ...prev, [targetRecord.id]: { status: 'saving' } }));
    try {
      const b = await post('/records/' + targetRecord.id + '/verify', {
        status,
        note: note || '',
        version: targetRecord.version,
      });
      replace(b);
      await refresh();
      setSaveStates((prev) => ({
        ...prev,
        [targetRecord.id]: { status: 'saved', message: status === 'verified' ? 'Đã xác minh' : 'Đã cập nhật' },
      }));
      notify('Đã lưu trạng thái xác minh');
    } catch (e: Any) {
      setSaveStates((prev) => ({ ...prev, [targetRecord.id]: { status: 'save_error', message: e.message } }));
      setError(e.message);
    }
  }

  function editDialog(r: Any) {
    setDialog({ kind: 'record', record: r, recordKind: r.kind, value: { ...r.value }, note: r.note || '' });
  }

  function renderNextActionBanner() {
    if (!current) return null;
    const docs = current.documents || [];
    const unreadDocs = docs.filter((d: Any) => d.status !== 'read');
    const unverifiedDocs = docs.filter((d: Any) => d.status === 'read' && !d.type_verified);
    const warningRecords = (current.records || []).filter((r: Any) => r.status !== 'rejected' && r.value?.warning);

    if (!docs.length) {
      return (
        <div className="next-action-bar">
          <div>
            <span className="badge info">Việc cần làm tiếp theo · Bước 3</span>
            <strong>Tải bộ chứng từ FCL (Invoice, Packing List, B/L) vào hồ sơ</strong>
            <p>Kéo thả hoặc chọn tệp từ máy tính để bắt đầu đọc và trích xuất dữ liệu local.</p>
          </div>
          <label className="btn primary upload-btn">
            <Upload size={16} />
            Thêm chứng từ
            <input
              type="file"
              multiple
              accept={health?.supported.join(',')}
              hidden
              onChange={(e) => {
                if (e.target.files) upload(e.target.files);
                e.target.value = '';
              }}
            />
          </label>
        </div>
      );
    }
    if (unreadDocs.length > 0) {
      return (
        <div className="next-action-bar">
          <div>
            <span className="badge warn">Việc cần làm tiếp theo · Bước 3</span>
            <strong>
              Còn {unreadDocs.length}/{docs.length} tệp chưa đọc hoặc đọc lỗi ({unreadDocs.map((d: Any) => d.name).join(', ')})
            </strong>
            <p>Bấm “Đọc & trích xuất” để đọc nội dung văn bản/OCR và nhận diện các trường thông tin.</p>
          </div>
          <button
            className="btn primary"
            disabled={loading || job?.status === 'running' || (mode === 'openai' && !consent)}
            onClick={() => {
              setTab('documents');
              run(async () => {
                const j = await post('/cases/' + current.case.id + '/process', {
                  mode,
                  allow_external: mode === 'openai' && consent,
                });
                setJob(j);
                replace(await api('/cases/' + current.case.id));
              });
            }}
          >
            <FileCheck2 size={16} />
            Chạy đọc & trích xuất ngay
          </button>
        </div>
      );
    }
    if (unverifiedDocs.length > 0) {
      const targetDoc = unverifiedDocs[0];
      return (
        <div className="next-action-bar">
          <div>
            <span className="badge warn">Việc cần làm tiếp theo · Bước 3</span>
            <strong>
              Xác nhận loại chứng từ cho {unverifiedDocs.length} tệp ({unverifiedDocs.map((d: Any) => `${d.name} → ${d.type}`).join(', ')})
            </strong>
            <p>Loại chứng từ do máy nhận diện từ nội dung cần nhân viên kiểm tra và bấm “Xác nhận loại”.</p>
          </div>
          <div className="row">
            <button
              className="btn"
              onClick={() => {
                setTab('documents');
                setSelectedDoc(targetDoc.id);
                setPage(1);
              }}
            >
              Xem {targetDoc.name}
            </button>
            <button
              className="btn primary"
              disabled={loading}
              onClick={() =>
                update(
                  () => patch('/documents/' + targetDoc.id + '/classification', { type: targetDoc.type }),
                  'Đã xác nhận loại ' + targetDoc.name
                )
              }
            >
              <Check size={16} />
              Xác nhận {targetDoc.name} là {targetDoc.type}
            </button>
          </div>
        </div>
      );
    }
    if (warningRecords.length > 0) {
      const firstWarn = warningRecords[0];
      return (
        <div className="next-action-bar">
          <div>
            <span className="badge warn">Việc cần làm tiếp theo · Bước 4</span>
            <strong>Có {warningRecords.length} bản ghi có định dạng số / ngày / đơn vị mơ hồ cần chỉnh rõ</strong>
            <p>{firstWarn.value?.warning}</p>
          </div>
          <button
            className="btn primary"
            onClick={() => {
              setRecordGroup(firstWarn.kind);
              chooseSource(firstWarn);
            }}
          >
            Đi tới bản ghi cần sửa
          </button>
        </div>
      );
    }
    if (unresolved.length > 0) {
      return (
        <div className="next-action-bar">
          <div>
            <span className="badge bad">Việc cần làm tiếp theo · Bước 5</span>
            <strong>Còn {unresolved.length} mục đối chiếu / thiếu dữ liệu chưa xử lý</strong>
            <p>Kiểm tra các mục Sai lệch, Thiếu hoặc Cần kiểm tra trong bảng Đối chiếu trước khi duyệt hồ sơ.</p>
          </div>
          <button
            className="btn primary"
            onClick={() => {
              setCheckFilter('unresolved');
              setTab('comparison');
            }}
          >
            Mở {unresolved.length} mục cần đối chiếu
          </button>
        </div>
      );
    }
    if (pending > 0) {
      return (
        <div className="next-action-bar">
          <div>
            <span className="badge warn">Việc cần làm tiếp theo · Bước 4</span>
            <strong>Còn {pending} bản ghi ở trạng thái Chờ xác minh</strong>
            <p>Đối chiếu từng giá trị với bằng chứng gốc rồi bấm “Xác minh” (không duyệt tự động hàng loạt).</p>
          </div>
          <div className="row">
            <button className="btn primary" onClick={jumpToNextPending}>
              Đi tới bản ghi chờ tiếp theo ({pending})
            </button>
            <button className="btn" onClick={() => setTab('review')}>
              Mở bàn Xác minh tổng hợp
            </button>
          </div>
        </div>
      );
    }
    if (!current.case.reviewed_at && current.blockers.length === 0) {
      return (
        <div className="next-action-bar ready">
          <div>
            <span className="badge good">Sẵn sàng duyệt · Bước 7</span>
            <strong>Tất cả chứng từ, bản ghi và đối chiếu đã được xác minh đầy đủ</strong>
            <p>Bạn có thể bấm “Hoàn thành kiểm tra” để chuyển hồ sơ sang trạng thái Đã kiểm tra (Reviewed).</p>
          </div>
          <button
            className="btn primary"
            disabled={loading}
            onClick={() => update(() => post('/cases/' + current.case.id + '/review'), 'Đã hoàn thành kiểm tra hồ sơ')}
          >
            <ShieldCheck size={16} />
            Hoàn thành kiểm tra hồ sơ
          </button>
        </div>
      );
    }
    if (current.blockers.length) return (
      <div className="next-action-bar">
        <div><span className="badge warn">Kiểm tra xuất file · Bước 7</span><strong>Còn {current.blockers.length} điều kiện cần xử lý</strong><p>Mở danh sách để kiểm tra dữ liệu và điều kiện duyệt hồ sơ.</p></div>
        <button className="btn primary" onClick={() => setTab('review')}>Mở kiểm tra hồ sơ</button>
      </div>
    );
    return (
      <div className="next-action-bar ready">
        <div>
          <span className="badge good">Đã duyệt Reviewed · Bước 8</span>
          <strong>
            Hồ sơ đã hoàn thành kiểm tra lúc {current.case.reviewed_at ? date(current.case.reviewed_at) : 'hiện tại'}
          </strong>
          <p>
            Bạn có thể xuất workbook Reviewed chính thức. Mọi thao tác sửa/thêm dữ liệu sau thời điểm này sẽ tự động yêu cầu xác minh lại.
          </p>
        </div>
        <button
          className="btn primary"
          onClick={() => {
            setExportMode('Reviewed');
            setTab('export');
          }}
        >
          <Download size={16} />
          Mở Xuất Excel Reviewed
        </button>
      </div>
    );
  }

  const tableCases = () => (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Hồ sơ / khách hàng</th>
            <th>Chứng từ</th>
            <th>Trạng thái</th>
            <th>Cập nhật</th>
            <th>
              <span className="sr-only">Thao tác</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((c) => (
            <tr key={c.id}>
              <td>
                <button className="case-link" onClick={() => openCase(c.id)}>
                  {c.name}
                </button>
                <small>
                  {c.id} · {c.customer || 'Chưa có khách hàng'}
                </small>
              </td>
              <td>
                {c.document_count} file
                {c.pending_count > 0 ? <small>{c.pending_count} bản ghi chờ xác minh</small> : null}
              </td>
              <td>
                <Badge status={c.status} />
              </td>
              <td className="muted">{date(c.updated_at)}</td>
              <td>
                <button className="icon-btn" aria-label={'Mở hồ sơ ' + c.name} onClick={() => openCase(c.id)}>
                  <ArrowRight size={18} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!filtered.length && (
        <div className="empty">
          <FolderOpen size={36} />
          <h3>{cases.length ? 'Không tìm thấy hồ sơ' : 'Bắt đầu với bộ chứng từ đầu tiên'}</h3>
          <p>Tạo hồ sơ, tải Invoice, Packing List và vận đơn để kiểm tra.</p>
          <button className="btn primary" onClick={() => setDialog({ kind: 'case' })}>
            <Plus size={16} />
            Tạo hồ sơ
          </button>
        </div>
      )}
    </div>
  );

  const recordCard = (r: Any) => {
    const docObj = current.documents.find((d: Any) => d.id === r.document_id);
    const docName = docObj?.name || 'Nhập tay';
    const uLabel = r.page ? ' · ' + unitLabel(docObj || r.method, r.page) : '';
    const saveInfo = saveStates[r.id];
    const fieldCheck = current.checks.find((c: Any) => c.key === 'field:' + r.key);
    const hasConflict = fieldCheck?.result === 'Mismatch';
    return (
      <article
        id={'card-' + r.id}
        className={
          'field-card ' +
          (r.status === 'verified' ? 'is-verified ' : '') +
          (hasConflict ? 'is-conflict ' : '') +
          (activeRecordId === r.id ? 'is-focused' : '')
        }
        key={r.id}
      >
        <div className="row">
          <button className="field-name" onClick={() => chooseSource(r)}>
            {dict.fields[r.key]?.label || r.key}
          </button>
          <div className="row" style={{ gap: 6 }}>
            {hasConflict && <span className="badge bad">Đang lệch nguồn</span>}
            <Badge status={r.status} />
          </div>
        </div>
        <label className="sr-only" htmlFor={'field-' + r.id}>
          {dict.fields[r.key]?.label || r.key}
        </label>
        <input
          id={'field-' + r.id}
          key={r.id + ':' + r.version}
          defaultValue={textValue(r.value)}
          onFocus={() => setActiveRecordId(r.id)}
          onBlur={(e) => editRecord(r, e.target.value)}
          disabled={job?.status === 'running'}
        />
        <div className="source-row">
          <small className="source">
            {r.method} · {docName}
            {uLabel} · v{r.version}
          </small>
          {saveInfo && (
            <span className={'save-pill ' + tone(saveInfo.status)} role="status">
              {saveInfo.status === 'saving'
                ? 'Đang lưu…'
                : saveInfo.status === 'save_error'
                ? 'Lưu lỗi'
                : 'Đã lưu'}
            </span>
          )}
        </div>
        {saveInfo?.status === 'save_error' && saveInfo.message && (
          <div className="inline-save-error">
            <span>{saveInfo.message}</span>
            {saveInfo.message.includes('thay đổi') && (
              <button
                className="text-btn"
                onClick={() => run(async () => replace(await api('/cases/' + current.case.id)), 'Đã tải lại bản mới nhất')}
              >
                Tải lại bản mới nhất
              </button>
            )}
          </div>
        )}
        {r.value.warning && <p className="warning-text">{r.value.warning}</p>}
        <details>
          <summary>Bằng chứng và giá trị gốc</summary>
          <blockquote>{r.evidence || 'Chưa có bằng chứng'}</blockquote>
          <small>Giá trị gốc: {typeof r.raw === 'string' ? r.raw : JSON.stringify(r.raw)}</small>
          {r.note && <p>Ghi chú: {r.note}</p>}
        </details>
        <div className="field-actions">
          <button className="text-btn" disabled={job?.status === 'running' || saveInfo?.status === 'saving'} onMouseDown={(e) => e.preventDefault()} onClick={() => {
            const input = document.getElementById('field-' + r.id) as HTMLInputElement | null;
            if (input) editRecord(r, input.value);
          }}>Lưu chỉnh sửa</button>
          {fieldCheck && ['Mismatch', 'Needs Verification'].includes(fieldCheck.result) && !fieldCheck.resolution && (
            <button className="text-btn" onClick={() => setDialog({ kind: 'resolve', check: fieldCheck })}>Ghi lý do xử lý</button>
          )}
          <button className="text-btn" onClick={() => chooseSource(r)}>
            <Eye size={14} />
            Xem nguồn
          </button>
          <button
            className="icon-btn"
            title="Hoàn tác lần sửa gần nhất"
            aria-label="Hoàn tác"
            onClick={() => update(() => post('/records/' + r.id + '/undo'), 'Đã hoàn tác')}
          >
            <Undo2 size={15} />
          </button>
          {r.status === 'verified' ? (
            <button className="text-btn" onClick={() => verifyRecord(r, 'pending')}>
              Mở lại
            </button>
          ) : (
            <>
              <button className="text-btn danger" onClick={() => verifyRecord(r, 'rejected')}>
                Từ chối
              </button>
              <button
                className="btn small"
                disabled={job?.status === 'running' || !!r.value.warning}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => verifyRecord(r, 'verified')}
              >
                <Check size={14} />
                Xác minh
              </button>
            </>
          )}
        </div>
      </article>
    );
  };

  function recordTable(group: string) {
    const rr = reviewRecords;
    const cols =
      group === 'item'
        ? ['line_number', 'product_code', 'description', 'quantity', 'unit', 'unit_price', 'line_amount', 'currency']
        : ['container_number', 'seal_number', 'container_type', 'packages', 'gross_weight', 'cbm'];
    const names: Any = {
      line_number: 'STT',
      product_code: 'Mã hàng',
      description: 'Mô tả',
      quantity: 'Số lượng',
      unit: 'Đơn vị',
      unit_price: 'Đơn giá',
      line_amount: 'Thành tiền',
      currency: 'Tiền tệ',
      container_number: 'Container vật lý',
      seal_number: 'Seal',
      container_type: 'Loại',
      packages: 'Số kiện',
      gross_weight: 'Gross Weight',
      cbm: 'CBM',
    };
    return (
      <>
        {group === 'container' && (
          <ContainerSummaryBanner records={current.records} documents={current.documents} />
        )}
        <div className="section-title">
          <div>
            <h2>{group === 'item' ? 'Dòng hàng độc lập' : 'Container & seal theo từng chứng từ nguồn'}</h2>
            <p className="muted">
              {group === 'container'
                ? `${containerStats.physicalCount} container vật lý duy nhất trên ${containerStats.sourceRecordCount} bản ghi nguồn. Mỗi chứng từ giữ bản ghi riêng để đối chiếu.`
                : 'Mỗi dòng hàng giữ nguyên nguồn và phạm vi (Invoice / Packing List); kiểm tra trước khi tổng hợp.'}
            </p>
          </div>
          <button
            className="btn"
            onClick={() => setDialog({ kind: 'record', recordKind: group, value: {}, note: '' })}
          >
            <Plus size={16} />
            Thêm {group === 'item' ? 'dòng hàng' : 'container'}
          </button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {cols.map((k) => (
                  <th key={k}>{names[k]}</th>
                ))}
                <th>Nguồn & đơn vị đọc</th>
                <th>Trạng thái</th>
                <th>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {rr.map((r: Any) => {
                const docObj = current.documents.find((d: Any) => d.id === r.document_id);
                const docName = docObj?.name || 'Nhập tay';
                const uLabel = r.page ? ' · ' + unitLabel(docObj || r.method, r.page) : '';
                return (
                  <tr key={r.id} id={'card-' + r.id}>
                    {cols.map((k) => (
                      <td key={k}>{r.value[k] || '—'}</td>
                    ))}
                    <td>
                      <button className="text-btn" onClick={() => chooseSource(r)}>
                        {docName}
                        {uLabel}
                      </button>
                      {r.value.scope && <small>Phạm vi: {r.value.scope}</small>}
                    </td>
                    <td>
                      <Badge status={r.status} />
                      {r.value.warning && <small className="warning-text">{r.value.warning}</small>}
                    </td>
                    <td>
                      <div className="row">
                        <button className="btn small" onClick={() => editDialog(r)}>
                          Sửa
                        </button>
                        <button
                          className="btn small"
                          disabled={!!r.value.warning}
                          onClick={() => verifyRecord(r, r.status === 'verified' ? 'pending' : 'verified')}
                        >
                          {r.status === 'verified' ? 'Mở lại' : 'Xác minh'}
                        </button>
                        <button className="text-btn danger" onClick={() => verifyRecord(r, 'rejected')}>
                          Từ chối
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {!rr.length && (
            <div className="empty compact">
              Chưa nhận diện được bản ghi phù hợp bộ lọc. Kiểm tra bảng gốc hoặc thêm thủ công có căn cứ.
            </div>
          )}
        </div>
      </>
    );
  }

  function handleBlockerAction(blockerText: string) {
    const key = current.checks.find((c: Any) => blockerText === c.title + ': chưa xử lý')?.key || '';
    if (blockerText.includes('tài liệu chưa đọc hoặc chưa xác nhận loại') || key.startsWith('classification:') || key.startsWith('reading:')) {
      const targetDoc = current.documents.find((d: Any) => d.status !== 'read' || !d.type_verified);
      if (targetDoc) {
        setSelectedDoc(targetDoc.id);
        setPage(1);
      }
      setTab('documents');
      return;
    }
    if (blockerText.includes('bản ghi chưa được xác minh')) {
      jumpToNextPending();
      return;
    }
    if (key.startsWith('document:')) {
      setTab('customs');
      return;
    }
    if (key.startsWith('missing:')) {
      const sub = key.split(':')[1] || '';
      if (sub === 'items') {
        setDialog({ kind: 'record', recordKind: 'item', value: {}, note: '' });
      } else if (sub === 'containers') {
        setDialog({ kind: 'record', recordKind: 'container', value: {}, note: '' });
      } else {
        setDialog({ kind: 'record', recordKind: 'field', defaultKey: sub, value: '', note: '' });
      }
      return;
    }
    setCheckFilter('unresolved');
    setTab('comparison');
  }

  const caseTabs = [
    ['documents', 'Chứng từ'],
    ['review', 'Xác minh'],
    ['comparison', 'Đối chiếu'],
    ['customs', 'Chuẩn bị khai báo'],
    ['export', 'Xuất Excel'],
    ['case-history', 'Lịch sử'],
  ];

  const filteredChecks = (current?.checks || []).filter((c: Any) => {
    if (checkFilter === 'unresolved')
      return ['Mismatch', 'Missing', 'Needs Verification'].includes(c.result) && !c.resolution;
    if (checkFilter === 'Mismatch') return c.result === 'Mismatch';
    if (checkFilter === 'Missing') return c.result === 'Missing';
    if (checkFilter === 'Needs Verification') return c.result === 'Needs Verification';
    if (checkFilter === 'Matched') return c.result === 'Matched';
    if (checkFilter === 'resolved') return !!c.resolution;
    return true;
  });

  return (
    <div className={'app ' + (collapsed ? 'collapsed' : '')}>
      <a href="#main-content" className="skip-link">
        Đến nội dung chính
      </a>
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <FileCheck2 size={24} />
          </div>
          <div className="brand-copy">
            <strong>U&I SMART</strong>
            <span>FCL Document Workbench</span>
          </div>
        <button
          className="collapse"
          type="button"
          aria-label={collapsed ? 'Mở rộng điều hướng' : 'Thu gọn điều hướng'}
          title={collapsed ? 'Mở rộng điều hướng' : 'Thu gọn điều hướng'}
          aria-expanded={!collapsed}
          aria-controls="primary-navigation"
          onClick={() => setCollapsed(!collapsed)}
        >
          <PanelLeftClose size={16} className={collapsed ? 'expand-icon' : ''} />
        </button>
        </div>
        <div className="nav-label">Không gian làm việc</div>
        <nav id="primary-navigation" aria-label="Điều hướng chính">
          {[
            ['overview', 'Tổng quan', LayoutDashboard],
            ['cases', 'Hồ sơ logistics', FolderOpen],
            ['history', 'Lịch sử xử lý', History],
            ['settings', 'Cài đặt', Settings],
          ].map(([id, title, Icon]: Any) => (
            <button
              title={title}
              aria-label={title}
              key={id}
              className={view === id ? 'active' : ''}
              onClick={() => go(id)}
            >
              <Icon size={19} />
              <span>{title}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-guide">
          <ShieldCheck size={22} />
          <strong>Kiểm tra cùng bằng chứng</strong>
          <p>Nhân viên chứng từ xác minh từng giá trị trước khi hoàn thành hồ sơ FCL.</p>
        </div>
        <div className="local-foot">
          <span className={'dot ' + (health?.ok ? 'online' : '')} />
          <div>
            <strong>{health?.ok ? (health?.deployment?.cloud ? 'Đã kết nối cloud' : 'Đã kết nối local') : 'Đang kiểm tra backend'}</strong>
            <small>{health?.deployment?.cloud ? 'Dữ liệu demo tạm thời' : 'SQLite lưu trên máy này'}</small>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            Không gian làm việc <ChevronRight size={14} />
            <strong>
              {view === 'case'
                ? current?.case.name
                : view === 'settings'
                ? 'Cài đặt'
                : view === 'history'
                ? 'Lịch sử xử lý'
                : view === 'cases'
                ? 'Hồ sơ logistics'
                : 'Tổng quan'}
            </strong>
          </div>
          <div className="row">
            <span className="badge neutral">
              <HardDrive size={13} />
              {health?.deployment?.cloud ? 'Cloud demo · Không gian dùng chung' : 'Local workspace · Nhân viên local'}
            </span>
            {health?.deployment?.cloud && <form method="post" action="/__cloud/logout"><button className="btn" type="submit">Đăng xuất</button></form>}
            <div className="avatar" title={health?.deployment?.cloud ? 'Phiên truy cập không gian dùng chung' : 'Nhân viên local (chưa định danh đăng nhập)'}>
              NV
            </div>
          </div>
        </header>
        <main id="main-content" tabIndex={-1}>
          {health?.deployment?.ephemeral && <div className="alert warn" role="status"><AlertTriangle size={18} /><div><strong>Bản demo Render Free — dữ liệu tạm thời.</strong><p>Hồ sơ và file có thể mất khi máy chủ ngủ, khởi động lại hoặc cập nhật. Tải bản sao lưu trong Cài đặt trước khi rời phiên. Máy chủ có thể cần khoảng 1 phút để thức dậy.</p></div><button className="btn" onClick={() => setView('settings')}>Sao lưu</button></div>}
          {error && (
            <div className="alert bad" role="alert">
              <AlertTriangle size={18} />
              <div style={{ whiteSpace: 'pre-wrap' }}>{error}</div>
              <button
                className="icon-btn"
                aria-label="Đóng thông báo lỗi"
                onClick={() => setError('')}
              >
                <X size={16} />
              </button>
            </div>
          )}

          {(view === 'overview' || view === 'cases') && (
            <>
              <div className="page-heading">
                <div>
                  <h1>{view === 'overview' ? 'Tổng quan hồ sơ' : 'Hồ sơ logistics'}</h1>
                  <p>Tiếp nhận, kiểm tra và chuẩn bị dữ liệu từ bộ chứng từ nhập khẩu FCL đường biển.</p>
                </div>
                <button className="btn primary" onClick={() => setDialog({ kind: 'case' })}>
                  <Plus size={18} />
                  Tạo hồ sơ
                </button>
              </div>
              {view === 'overview' && (
                <>
                  <div className="summary-strip">
                    {[
                      ['Tổng hồ sơ', cases.length, FolderOpen],
                      ['Cần xác minh', cases.filter((c) => c.status === 'Needs verification').length, AlertTriangle],
                      ['Đã kiểm tra (Reviewed)', cases.filter((c) => ['Reviewed', 'Exported'].includes(c.status)).length, ShieldCheck],
                      ['Đã xuất Reviewed', cases.filter((c) => c.status === 'Exported').length, FileSpreadsheet],
                    ].map(([title, n, Icon]: Any) => (
                      <div className="metric" key={title}>
                        <div className="metric-icon">
                          <Icon size={20} />
                        </div>
                        <div>
                          <span>{title}</span>
                          <strong>{n}</strong>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="workflow-intro">
                    <div>
                      <h2>Bàn làm việc chứng từ nhập khẩu FCL · Nguồn dữ liệu minh bạch</h2>
                      <p>
                        Tiếp nhận → Đọc file & OCR local → Phân loại (nhân viên xác nhận) → Trích xuất → Chuẩn hóa → Đối chiếu → Nhân viên xác minh → Xuất Excel 7 sheet.
                      </p>
                    </div>
                    <span className="badge neutral">Không cần API key cho Local</span>
                  </div>
                </>
              )}
              <section className="surface">
                <div className="section-title">
                  <h2>{view === 'overview' ? 'Hồ sơ gần đây' : 'Danh sách hồ sơ'}</h2>
                  <span className="muted">{filtered.length} hồ sơ</span>
                </div>
                <div className="filters">
                  <label className="search">
                    <Search size={17} />
                    <input
                      aria-label="Tìm hồ sơ"
                      placeholder="Tìm tên hồ sơ, khách hàng hoặc mã…"
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                    />
                  </label>
                  <select
                    aria-label="Lọc trạng thái"
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                  >
                    <option value="">Tất cả trạng thái</option>
                    {['Draft', 'Reading', 'Needs verification', 'Reviewed', 'Exported'].map((s) => (
                      <option key={s} value={s}>
                        {label(s)}
                      </option>
                    ))}
                  </select>
                  <select
                    aria-label="Sắp xếp"
                    value={sort}
                    onChange={(e) => setSort(e.target.value)}
                  >
                    <option value="updated">Cập nhật gần nhất</option>
                    <option value="created">Mới tạo</option>
                    <option value="name">Tên hồ sơ A–Z</option>
                  </select>
                </div>
                {tableCases()}
              </section>
              <div className="help-inline">
                <ShieldCheck size={16} />
                <span>
                  Excel xuất ra là hồ sơ làm việc nội bộ của bộ phận chứng từ. Mã HS, thuế suất, trị giá hải quan và tính hợp lệ C/O cần căn cứ xác minh riêng.
                </span>
              </div>
            </>
          )}

          {view === 'case' && current && (
            <>
              <div className="page-heading case-heading">
                <div>
                  <button className="text-btn" onClick={() => go('cases')}>
                    <ChevronLeft size={16} />
                    Danh sách hồ sơ
                  </button>
                  <h1>{current.case.name}</h1>
                  <p>
                    {current.case.id} · {current.case.customer || 'Chưa có khách hàng'} ·{' '}
                    {current.case.mode === 'FCL' ? 'Nhập khẩu FCL đường biển' : 'Hàng không'} · Phiên sửa đổi #{current.case.revision}{' '}
                    <Badge status={current.case.status} />
                  </p>
                </div>
                <div className="row">
                  <button className="btn" onClick={() => setTab('export')}>
                    <Download size={16} />
                    Xuất Excel
                  </button>
                  <button
                    className="icon-btn danger"
                    aria-label="Xóa hồ sơ"
                    onClick={() => setDialog({ kind: 'delete-case' })}
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>

              <StepTracker current={current} onSelectTab={(t: string) => setTab(t)} />
              <ContainerSummaryBanner records={current.records} documents={current.documents} checks={current.checks} />
              {renderNextActionBanner()}

              <nav className="tabs" aria-label="Các phân hệ kiểm tra hồ sơ">
                {caseTabs.map(([id, title]) => (
                  <button
                    key={id}
                    className={tab === id ? 'active' : ''}
                    onClick={() => {
                      setTab(id);
                      if (id === 'case-history')
                        run(async () => setAudit(await api('/cases/' + current.case.id + '/audit')));
                    }}
                  >
                    {title}
                    {id === 'review' && pending > 0 ? <b>{pending}</b> : null}
                    {id === 'comparison' && unresolved.length > 0 ? <b>{unresolved.length}</b> : null}
                  </button>
                ))}
              </nav>

              {tab === 'documents' && (
                <>
                  <div className="processing-toolbar">
                    <div className="row">
                      <span className="badge neutral">
                        {mode === 'local' ? 'Rules / OCR local' : 'OpenAI hỗ trợ'}
                      </span>
                      <select
                        aria-label="Chế độ xử lý"
                        value={mode}
                        onChange={(e) => {
                          setMode(e.target.value);
                          setConsent(false);
                        }}
                      >
                        <option value="local">Xử lý Local</option>
                        <option value="openai">AI hỗ trợ · OpenAI</option>
                      </select>
                      {pending > 0 && (
                        <button className="btn small" onClick={jumpToNextPending}>
                          Đi tới bản ghi chờ tiếp theo ({pending})
                        </button>
                      )}
                    </div>
                    <div className="row">
                      <label className="btn upload-btn">
                        <Upload size={16} />
                        Thêm chứng từ
                        <input
                          type="file"
                          multiple
                          accept={health?.supported.join(',')}
                          hidden
                          onChange={(e) => {
                            if (e.target.files) upload(e.target.files);
                            e.target.value = '';
                          }}
                        />
                      </label>
                      <button
                        className="btn primary"
                        disabled={
                          loading ||
                          !current.documents.length ||
                          job?.status === 'running' ||
                          (mode === 'openai' && !consent)
                        }
                        onClick={() =>
                          run(async () => {
                            const j = await post('/cases/' + current.case.id + '/process', {
                              mode,
                              allow_external: mode === 'openai' && consent,
                            });
                            setJob(j);
                            replace(await api('/cases/' + current.case.id));
                          })
                        }
                      >
                        {job?.status === 'running' ? (
                          <Loader2 size={16} className="spin" />
                        ) : (
                          <FileCheck2 size={16} />
                        )}
                        Đọc & trích xuất
                      </button>
                    </div>
                  </div>

                  {mode === 'openai' && (
                    <div className="alert info">
                      <Link2 size={18} />
                      <div>
                        {!health?.ai.configured ? (
                          <>
                            <strong>Kết nối OpenAI để sử dụng AI</strong>
                            <p>AI hỗ trợ nhận diện và trích xuất từ bước 3. Bạn vẫn có thể xử lý bằng Local.</p>
                            <button className="btn" onClick={() => go('settings')}>
                              Cấu hình OpenAI
                            </button>
                          </>
                        ) : (
                          <label className="check-label">
                            <input
                              type="checkbox"
                              checked={consent}
                              onChange={(e) => setConsent(e.target.checked)}
                            />
                            Tôi chọn gửi văn bản đã đọc/OCR của các chứng từ trong hồ sơ tới OpenAI để phân loại và trích xuất cho yêu cầu này. File gốc được giữ local.
                          </label>
                        )}
                      </div>
                    </div>
                  )}

                  {job?.case_id === current.case.id && (
                    <div className="job-status" role="status">
                      <div>
                        <div className="row">
                          {job.status === 'running' && <Loader2 size={16} className="spin" />}
                          <strong>{job.stage}</strong>
                          <span>
                            {job.document} {job.index}/{job.total}
                            {job.pages ? ' · ' + job.pages + ' đơn vị/trang đã đọc' : ''}
                          </span>
                        </div>
                        {job.errors?.length > 0 && (
                          <div className="job-errors">
                            {job.errors.map((err: Any, idx: number) => (
                              <small key={idx} className="danger">
                                • {err.document}: {err.error}
                              </small>
                            ))}
                          </div>
                        )}
                      </div>
                      {job.status === 'running' && (
                        <button
                          className="text-btn"
                          onClick={() => run(() => post('/jobs/' + job.id + '/cancel'), 'Đã yêu cầu hủy')}
                        >
                          Hủy sau tác vụ hiện tại
                        </button>
                      )}
                    </div>
                  )}

                  <div
                    className="workspace"
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      upload(Array.from(e.dataTransfer.files));
                    }}
                  >
                    <aside className="document-list">
                      <div className="pane-title">
                        <h3>Chứng từ</h3>
                        <span>{current.documents.length}</span>
                      </div>
                      <div className="sample-loader">
                        <small>Dữ liệu giả lập · nạp vào hồ sơ trống</small>
                        <button className="btn small" disabled={loading || !!current.documents.length} onClick={() => loadSampleSet(false)}>Bộ mẫu chuẩn</button>
                        <button className="btn small" disabled={loading || !!current.documents.length} onClick={() => loadSampleSet(true)}>Bộ mẫu sai lệch</button>
                      </div>
                      {current.documents.map((d: Any) => {
                        const docPending = current.records.filter(
                          (r: Any) => r.document_id === d.id && r.status === 'pending'
                        ).length;
                        return (
                          <div className="document-entry" key={d.id}>
                          <button
                            className={'document-item ' + (selectedDoc === d.id ? 'selected' : '')}
                            key={d.id}
                            onClick={() => {
                              setSelectedDoc(d.id);
                              setPage(1);
                              setRotation(0);
                              setHighlight('');
                              setShowText(false);
                            }}
                          >
                            <FileText size={21} />
                            <div>
                              <strong>{d.name}</strong>
                              <small>
                                {d.type} · {Math.ceil(d.size / 1024)} KB
                              </small>
                              <small>{d.reading_method || 'Chưa đọc'}{d.pages?.some((p: Any) => p.quality) ? ' · Có ghi chú chất lượng đọc' : ''}</small>
                              <div className="row" style={{ gap: 4 }}>
                                <Badge status={d.status} />
                                {d.status === 'read' && (
                                  <span className={'badge ' + (d.type_verified ? 'good' : 'warn')}>
                                    {d.type_verified ? 'Đã xác nhận loại' : 'Chờ xác nhận loại'}
                                  </span>
                                )}
                                {docPending > 0 && (
                                  <span className="badge neutral">{docPending} chờ duyệt</span>
                                )}
                              </div>
                            </div>
                          </button>
                          <div className="document-classification">
                            <select aria-label={'Loại chứng từ ' + d.name} value={documentTypes[d.id] || d.type} disabled={loading || job?.status === 'running'} onChange={(e) => setDocumentTypes((previous) => ({ ...previous, [d.id]: e.target.value }))}>
                              {dict.document_types.map((type: string) => <option key={type} value={type}>{type}</option>)}
                            </select>
                            <button className="btn small" disabled={loading || d.status !== 'read' || (!!d.type_verified && (!documentTypes[d.id] || documentTypes[d.id] === d.type)) || job?.status === 'running'} onClick={() => update(() => patch('/documents/' + d.id + '/classification', { type: documentTypes[d.id] || d.type }), 'Đã xác nhận loại ' + d.name)}>Xác nhận loại</button>
                          </div>
                          </div>
                        );
                      })}
                      <label className="drop-hint">
                        <Upload size={22} />
                        <strong>Kéo file vào đây</strong>
                        <span>PDF, ảnh, Excel, CSV, TXT, DOCX · tối đa 25 MB/file</span>
                        <input
                          type="file"
                          multiple
                          hidden
                          onChange={(e) => {
                            if (e.target.files) upload(e.target.files);
                            e.target.value = '';
                          }}
                        />
                      </label>
                    </aside>

                    <section className="preview-pane">
                      <div className="preview-toolbar">
                        <strong>{activeDoc?.name || 'Xem trước chứng từ'}</strong>
                        <div className="row">
                          <button
                            className="icon-btn"
                            aria-label="Thu nhỏ"
                            onClick={() => setZoom(Math.max(40, zoom - 20))}
                          >
                            <ZoomOut size={16} />
                          </button>
                          <span>{zoom}%</span>
                          <button
                            className="icon-btn"
                            aria-label="Phóng to"
                            onClick={() => setZoom(Math.min(200, zoom + 20))}
                          >
                            <ZoomIn size={16} />
                          </button>
                          <button
                            className="icon-btn"
                            title="Xoay chiều xem bản gốc (chỉ xoay hiển thị, không chạy lại OCR)"
                            aria-label="Xoay chiều xem bản gốc (không chạy lại OCR)"
                            onClick={() => setRotation((rotation + 90) % 360)}
                          >
                            <RotateCw size={16} />
                          </button>
                          <button className="text-btn" onClick={() => setShowText(!showText)}>
                            {showText ? 'Bản gốc' : 'Văn bản'}
                          </button>
                        </div>
                      </div>

                      {rotation !== 0 && (
                        <div className="reading-note">
                          Đang xoay góc nhìn hiển thị {rotation}° (chỉ tác động khung xem ảnh, không tự xoay tệp gốc hay chạy lại OCR).
                        </div>
                      )}

                      {activeDoc && (
                        <div className="classification">
                          <label>
                            Loại chứng từ
                            <select
                              aria-label="Loại chứng từ"
                              value={activeDoc.type}
                              onChange={(e) =>
                                update(
                                  () => patch('/documents/' + activeDoc.id + '/classification', { type: e.target.value }),
                                  'Đã lưu loại · chạy lại trích xuất nếu đã đổi loại'
                                )
                              }
                            >
                              {dict.document_types.map((t: string) => (
                                <option key={t}>{t}</option>
                              ))}
                            </select>
                          </label>
                          {activeDoc.classification_evidence && (
                            <small className="classification-evidence" title={activeDoc.classification_evidence}>
                              Căn cứ nhận diện: “{activeDoc.classification_evidence}”
                            </small>
                          )}
                          <button
                            className="btn small"
                            disabled={loading || !!activeDoc.type_verified}
                            onClick={() =>
                              update(
                                () => patch('/documents/' + activeDoc.id + '/classification', { type: activeDoc.type }),
                                'Đã xác nhận loại'
                              )
                            }
                          >
                            {activeDoc.type_verified ? (
                              <>
                                <Check size={14} />
                                Đã xác nhận
                              </>
                            ) : (
                              'Xác nhận loại'
                            )}
                          </button>
                          <button
                            className="icon-btn danger"
                            aria-label="Xóa tài liệu"
                            onClick={() => setDialog({ kind: 'delete-doc', document: activeDoc })}
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      )}

                      {activeDoc?.error && <div className="alert bad">{activeDoc.error}</div>}
                      {pageData?.quality && <div className="reading-note">{pageData.quality}</div>}

                      {activeDoc && (
                        <label className="search preview-search">
                          <Search size={15} />
                          <input
                            aria-label="Tìm văn bản trên trang"
                            placeholder="Tìm trong văn bản đang mở…"
                            value={findText}
                            onChange={(e) => {
                              setFindText(e.target.value);
                              setShowText(true);
                            }}
                          />
                        </label>
                      )}

                      <div className="preview-content">
                        {!activeDoc ? (
                          <div className="empty">
                            <FileText size={42} />
                            <h3>Chọn chứng từ để bắt đầu</h3>
                            <p>Tải file và chọn “Đọc & trích xuất”.</p>
                          </div>
                        ) : !pageData ? (
                          <div className="empty">
                            <FileText size={34} />
                            <p>
                              {activeDoc.status === 'reading'
                                ? 'Đang đọc tài liệu…'
                                : 'Tài liệu chưa đọc được. Chọn Đọc & trích xuất hoặc thử lại.'}
                            </p>
                          </div>
                        ) : showText || !['.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff'].includes(activeDoc.ext) ? (
                          <div className="document-text" style={{ fontSize: (14 * zoom) / 100 }}>
                            {highlight && (
                              <blockquote className="evidence-focus">
                                <strong>
                                  Bằng chứng được chọn · {unitLabel(activeDoc, page)}
                                </strong>
                                <br />
                                {highlight}
                              </blockquote>
                            )}
                            <HighlightedText text={pageData.text} query={findText} />
                          </div>
                        ) : (
                          <img
                            alt={'Bản gốc ' + activeDoc.name + ' ' + unitLabel(activeDoc, page)}
                            src={`/api/documents/${activeDoc.id}/preview/${page}`}
                            style={{ width: zoom + '%', transform: `rotate(${rotation}deg)` }}
                          />
                        )}
                      </div>

                      <footer className="preview-footer">
                        <span>
                          {pageData?.method || 'Chưa đọc'} ·{' '}
                          {activeDoc ? unitLabel(activeDoc, page, activeDoc.pages?.length || 1) : '—'}
                        </span>
                        <div className="row">
                          <button
                            className="icon-btn"
                            disabled={page <= 1}
                            aria-label="Đơn vị/trang trước"
                            onClick={() => setPage(page - 1)}
                          >
                            <ChevronLeft size={17} />
                          </button>
                          <button
                            className="icon-btn"
                            disabled={!activeDoc || page >= activeDoc.pages.length}
                            aria-label="Đơn vị/trang sau"
                            onClick={() => setPage(page + 1)}
                          >
                            <ChevronRight size={17} />
                          </button>
                        </div>
                      </footer>
                    </section>

                    <aside className="fields-pane">
                      <div className="pane-title">
                        <h3>Dữ liệu trích xuất</h3>
                        <div className="row" style={{ gap: 6 }}>
                          <button
                            className="text-btn"
                            onClick={() => setDocScopeOnly(!docScopeOnly)}
                            title="Chuyển giữa chỉ xem dữ liệu của tệp đang chọn hoặc toàn bộ hồ sơ"
                          >
                            {docScopeOnly ? 'Theo tệp đang mở' : 'Toàn hồ sơ'}
                          </button>
                          <button
                            className="icon-btn"
                            aria-label="Thêm dữ liệu thủ công"
                            onClick={() => setDialog({ kind: 'record', recordKind: recordGroup, value: {}, note: '' })}
                          >
                            <Plus size={18} />
                          </button>
                        </div>
                      </div>
                      <p className="pane-help">
                        Sửa giá trị rồi rời ô để lưu. Kiểm tra bằng chứng gốc trước khi bấm Xác minh.
                      </p>
                      <div className="segments">
                        {[
                          ['field', `Trường (${current.records.filter((r: Any) => r.kind === 'field').length})`],
                          ['item', `Hàng (${current.records.filter((r: Any) => r.kind === 'item').length})`],
                          [
                            'container',
                            `Cont (${containerStats.physicalCount} VL/${containerStats.sourceRecordCount} nguồn)`,
                          ],
                        ].map(([id, t]) => (
                          <button
                            key={id}
                            className={recordGroup === id ? 'active' : ''}
                            onClick={() => setRecordGroup(id)}
                          >
                            {t}
                          </button>
                        ))}
                      </div>
                      <div className="filter-pills">
                        {[
                          ['all', 'Tất cả'],
                          ['blocked', 'Chặn xuất'],
                          ['warning', 'Cần kiểm'],
                          ['verified', 'Đã duyệt'],
                        ].map(([fid, flabel]) => (
                          <button
                            key={fid}
                            className={'pill-btn ' + (recordFilter === fid ? 'active' : '')}
                            onClick={() => setRecordFilter(fid)}
                          >
                            {flabel}
                          </button>
                        ))}
                      </div>
                      <label className="field-search">
                        <Search size={15} />
                        <input aria-label="Tìm trường hoặc giá trị" placeholder="Tìm tên trường, giá trị…" value={recordSearch} onChange={(e) => setRecordSearch(e.target.value)} />
                      </label>
                      <div className="fields-scroll">
                        {recordGroup === 'container' && (
                          <div className="pane-container-note">
                            <strong>
                              {containerStats.physicalCount} container vật lý · {containerStats.sourceRecordCount} bản ghi nguồn
                            </strong>
                            <small>
                              Mỗi bản ghi ứng với 1 chứng từ nguồn (Packing List / B/L).
                            </small>
                          </div>
                        )}
                        {recordGroup === 'field' && recordFilter !== 'verified' && current.checks.filter((c: Any) => c.key.startsWith('missing:') && !['missing:items', 'missing:containers'].includes(c.key) && !c.resolution && (!recordSearch || (dict.fields[c.key.slice(8)]?.label || '').toLocaleLowerCase('vi').includes(recordSearch.toLocaleLowerCase('vi')))).map((c: Any) => (
                          <article className="field-card is-conflict" key={c.id}>
                            <strong>{dict.fields[c.key.slice(8)]?.label || 'Dữ liệu thiếu'}</strong>
                            <Badge status={c.result} /><p>{c.detail.reason}</p>
                            <div className="field-actions">
                              <button className="btn small" onClick={() => setDialog({ kind: 'record', recordKind: 'field', defaultKey: c.key.slice(8), value: '', note: '' })}>Nhập bổ sung</button>
                              {c.result === 'Needs Verification' && <button className="text-btn" onClick={() => setDialog({ kind: 'resolve', check: c })}>Ghi lý do xử lý</button>}
                            </div>
                          </article>
                        ))}
                        {recordGroup === 'field'
                          ? activeRecords.map(recordCard)
                          : activeRecords.map((r: Any) => {
                              const docObj = current.documents.find((d: Any) => d.id === r.document_id);
                              const docName = docObj?.name || 'Nhập tay';
                              const uLabel = r.page ? ' · ' + unitLabel(docObj || r.method, r.page) : '';
                              return (
                                <article className="field-card" key={r.id} id={'card-' + r.id}>
                                  <div className="row">
                                    <Badge status={r.status} />
                                    <small className="source">
                                      {docName}
                                      {uLabel}
                                    </small>
                                  </div>
                                  <strong>{r.value.description || r.value.container_number}</strong>
                                  <p>
                                    {r.kind === 'item'
                                      ? `${r.value.quantity || '—'} ${r.value.unit || ''} × ${r.value.unit_price || '—'} = ${r.value.line_amount || '—'} ${r.value.currency || ''}`
                                      : `Seal: ${r.value.seal_number || '—'} · Loại: ${r.value.container_type || '—'}`}
                                  </p>
                                  {r.value.warning && <p className="warning-text">{r.value.warning}</p>}
                                  <div className="field-actions">
                                    <button className="text-btn" onClick={() => chooseSource(r)}>
                                      <Eye size={14} />
                                      Xem nguồn
                                    </button>
                                    <button className="btn small" onClick={() => editDialog(r)}>
                                      Kiểm tra / sửa
                                    </button>
                                    <button
                                      className="btn small"
                                      disabled={!!r.value.warning}
                                      onClick={() => verifyRecord(r, r.status === 'verified' ? 'pending' : 'verified')}
                                    >
                                      {r.status === 'verified' ? 'Mở lại' : 'Xác minh'}
                                    </button>
                                  </div>
                                </article>
                              );
                            })}
                        {!activeRecords.length && (
                          <div className="empty compact">
                            <FileCheck2 size={26} />
                            <p>
                              Không có bản ghi nào khớp bộ lọc hiện tại. Đổi bộ lọc hoặc thêm dữ liệu thủ công.
                            </p>
                          </div>
                        )}
                      </div>
                    </aside>
                  </div>
                </>
              )}

              {tab === 'review' && (
                <>
                  <div className="review-banner">
                    <ShieldCheck size={24} />
                    <div>
                      <h2>{pending} bản ghi cần xác minh</h2>
                      <p>
                        Không xác nhận hàng loạt. Kiểm tra giá trị và bằng chứng gốc của từng bản ghi trước khi duyệt hồ sơ.
                      </p>
                    </div>
                    <div className="row">
                      {pending > 0 && (
                        <button className="btn" onClick={jumpToNextPending}>
                          Đi tới mục chờ tiếp theo
                        </button>
                      )}
                      <button
                        className="btn primary"
                        disabled={loading || current.blockers.length > 0}
                        onClick={() =>
                          update(() => post('/cases/' + current.case.id + '/review'), 'Đã hoàn thành kiểm tra hồ sơ')
                        }
                      >
                        Hoàn thành kiểm tra
                      </button>
                    </div>
                  </div>

                  {current.blockers.length > 0 && (
                    <section className="surface padded blockers-panel">
                      <div className="section-title">
                        <div>
                          <h2>Điều kiện cần xử lý trước khi duyệt Reviewed ({current.blockers.length})</h2>
                          <p className="muted">
                            Bấm vào từng mục bên dưới để đi thẳng tới nơi cần xác nhận hoặc đối chiếu.
                          </p>
                        </div>
                      </div>
                      <div className="blocker-list">
                        {current.blockers.map((s: string) => (
                          <div className="blocker-item" key={s}>
                            <span>{s}</span>
                            <button className="btn small" onClick={() => handleBlockerAction(s)}>
                              Đi tới xử lý <ArrowRight size={13} />
                            </button>
                          </div>
                        ))}
                      </div>
                    </section>
                  )}

                  <div className="row" style={{ justifyContent: 'space-between', marginBottom: 16 }}>
                    <div className="segments standalone" style={{ margin: 0 }}>
                      {[
                        ['field', `Trường dữ liệu (${current.records.filter((r: Any) => r.kind === 'field').length})`],
                        ['item', `Dòng hàng (${current.records.filter((r: Any) => r.kind === 'item').length})`],
                        [
                          'container',
                          `Container (${containerStats.physicalCount} vật lý / ${containerStats.sourceRecordCount} nguồn)`,
                        ],
                      ].map(([id, t]) => (
                        <button
                          key={id}
                          className={recordGroup === id ? 'active' : ''}
                          onClick={() => setRecordGroup(id)}
                        >
                          {t}
                        </button>
                      ))}
                    </div>
                    <div className="filter-pills">
                      {[
                        ['all', 'Tất cả'],
                        ['pending', 'Chờ xác minh'],
                        ['warning', 'Cảnh báo'],
                        ['verified', 'Đã xác minh'],
                      ].map(([fid, flabel]) => (
                        <button
                          key={fid}
                          className={'pill-btn ' + (recordFilter === fid ? 'active' : '')}
                          onClick={() => setRecordFilter(fid)}
                        >
                          {flabel}
                        </button>
                      ))}
                    </div>
                  </div>

                  {recordGroup === 'field' ? (
                    <div className="review-grid">
                      {reviewRecords.map(recordCard)}
                      {!reviewRecords.length && (
                        <div className="empty">
                          Không có bản ghi trường dữ liệu nào khớp bộ lọc hiện tại.
                        </div>
                      )}
                    </div>
                  ) : (
                    recordTable(recordGroup)
                  )}
                </>
              )}

              {tab === 'comparison' && (
                <>
                  <div className="section-title">
                    <div>
                      <h2>Đối chiếu cùng chỉ tiêu, cùng phạm vi</h2>
                      <p className="muted">
                        {unresolved.length} mục cần xử lý · Kết quả Khớp chỉ phản ánh các nguồn trùng nhau sau chuẩn hóa, vẫn cần nhân viên xác minh. Ghi chú xử lý sai lệch được lưu audit và không tự động sửa đè nguồn gốc.
                      </p>
                    </div>
                    <div className="filter-pills">
                      {[
                        ['all', `Tất cả (${current.checks.length})`],
                        ['unresolved', `Cần xử lý (${unresolved.length})`],
                        ['Mismatch', `Sai lệch (${current.checks.filter((c: Any) => c.result === 'Mismatch').length})`],
                        ['Missing', `Thiếu (${current.checks.filter((c: Any) => c.result === 'Missing').length})`],
                        [
                          'Needs Verification',
                          `Cần kiểm tra (${current.checks.filter((c: Any) => c.result === 'Needs Verification').length})`,
                        ],
                        ['Matched', `Khớp (${current.checks.filter((c: Any) => c.result === 'Matched').length})`],
                        ['resolved', `Đã xử lý (${current.checks.filter((c: Any) => c.resolution).length})`],
                      ].map(([cid, clabel]) => (
                        <button
                          key={cid}
                          className={'pill-btn ' + (checkFilter === cid ? 'active' : '')}
                          onClick={() => setCheckFilter(cid)}
                        >
                          {clabel}
                        </button>
                      ))}
                    </div>
                  </div>
                  <section className="surface">
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Chỉ tiêu / quy tắc</th>
                            <th>Giá trị và nguồn đối chiếu</th>
                            <th>Kết quả</th>
                            <th>Giải thích & hành động xử lý</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredChecks.map((c: Any) => {
                            const meta = humanCheckTitle(c.key, dict.fields, current.documents);
                            const isClassification = c.key.startsWith('classification:');
                            const isReading = c.key.startsWith('reading:');
                            const isDocCheck = c.key.startsWith('document:');
                            const isMissingField = c.key.startsWith('missing:');
                            const canResolveByNote =
                              ['Mismatch', 'Needs Verification'].includes(c.result) &&
                              !isClassification &&
                              !isReading;
                            return (
                              <tr key={c.id}>
                                <td>
                                  <span className="badge neutral" style={{ marginBottom: 4 }}>
                                    {meta.category}
                                  </span>
                                  <strong style={{ display: 'block' }}>{meta.title}</strong>
                                  <small>{c.key}</small>
                                </td>
                                <td>
                                  {c.detail.sources?.length ? (
                                    c.detail.sources.map((s: Any, sIdx: number) => {
                                      const docObj = current.documents.find((d: Any) => d.name === s.document);
                                      const uText = s.page ? ' · ' + unitLabel(docObj || s.type, s.page) : '';
                                      return (
                                        <div key={s.id || sIdx} className="compare-source-item">
                                          <button
                                            className="text-btn"
                                            onClick={() => {
                                              const r = current.records.find((x: Any) => x.id === s.id);
                                              if (r) chooseSource(r);
                                              else if (docObj) {
                                                setSelectedDoc(docObj.id);
                                                setPage(s.page || 1);
                                                setTab('documents');
                                              }
                                            }}
                                          >
                                            {s.document}
                                            {uText}
                                          </button>
                                          <div>{textValue(s.value)}</div>
                                        </div>
                                      );
                                    })
                                  ) : (
                                    <span className="muted">Chưa có bản ghi nguồn</span>
                                  )}
                                </td>
                                <td>
                                  <Badge status={c.result} />
                                  {c.resolution && (
                                    <small className="good-text">Đã ghi nhận căn cứ xử lý (giữ nguyên nguồn gốc)</small>
                                  )}
                                </td>
                                <td>
                                  <p>{c.detail.reason}</p>
                                  {c.resolution && <blockquote>Căn cứ xử lý: {c.resolution}</blockquote>}
                                  <div className="row" style={{ marginTop: 8 }}>
                                    {isClassification && c.result !== 'Matched' && (
                                      <button
                                        className="btn small primary"
                                        onClick={() => {
                                          const docId = c.key.slice('classification:'.length);
                                          const dObj = current.documents.find((d: Any) => d.id === docId);
                                          if (dObj) {
                                            update(
                                              () => patch('/documents/' + dObj.id + '/classification', { type: dObj.type }),
                                              'Đã xác nhận loại ' + dObj.name
                                            );
                                          }
                                        }}
                                      >
                                        <Check size={14} />
                                        Xác nhận loại ngay
                                      </button>
                                    )}
                                    {isReading && (
                                      <button
                                        className="btn small"
                                        onClick={() => {
                                          const docId = c.key.slice('reading:'.length);
                                          setSelectedDoc(docId);
                                          setTab('documents');
                                        }}
                                      >
                                        Mở chứng từ để đọc lại
                                      </button>
                                    )}
                                    {isDocCheck && c.result === 'Missing' && (
                                      <button
                                        className="btn small"
                                        onClick={() => {
                                          const docKind = c.key.slice('document:'.length);
                                          setDialog({
                                            kind: 'requirement',
                                            documentType: docKind,
                                            required: false,
                                            note: '',
                                          });
                                        }}
                                      >
                                        Đặt Không bắt buộc (có lý do)
                                      </button>
                                    )}
                                    {isMissingField && c.result === 'Missing' && (
                                      <button
                                        className="btn small"
                                        onClick={() => {
                                          const sub = c.key.slice('missing:'.length);
                                          if (sub === 'items') {
                                            setDialog({ kind: 'record', recordKind: 'item', value: {}, note: '' });
                                          } else if (sub === 'containers') {
                                            setDialog({ kind: 'record', recordKind: 'container', value: {}, note: '' });
                                          } else {
                                            setDialog({
                                              kind: 'record',
                                              recordKind: 'field',
                                              defaultKey: sub,
                                              value: '',
                                              note: '',
                                            });
                                          }
                                        }}
                                      >
                                        <Plus size={14} />
                                        Nhập bổ sung có căn cứ
                                      </button>
                                    )}
                                    {canResolveByNote && (
                                      <button
                                        className="btn small"
                                        onClick={() => setDialog({ kind: 'resolve', check: c })}
                                      >
                                        {c.resolution ? 'Sửa lý do xử lý' : 'Ghi lý do xử lý'}
                                      </button>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                      {!filteredChecks.length && (
                        <div className="empty">Không có mục đối chiếu nào khớp bộ lọc hiện tại.</div>
                      )}
                    </div>
                  </section>
                </>
              )}

              {tab === 'customs' && (
                <>
                  <div className="alert info">
                    <ShieldCheck size={20} />
                    <div>
                      <strong>Chuẩn bị dữ liệu nghiệp vụ & phân biệt miễn chứng từ với dữ liệu cốt lõi</strong>
                      <p>
                        Checklist bên dưới quản lý yêu cầu có mặt <strong>tệp chứng từ</strong> trong bộ hồ sơ FCL. Nếu tắt một chứng từ sang “Không bắt buộc” kèm lý do, các chỉ tiêu cốt lõi thuộc chứng từ đó sẽ chuyển sang “Cần kiểm tra” để bạn nhập từ nguồn thay thế hoặc xác nhận miễn áp dụng. Mã HS, loại hình, mã địa điểm, thuế suất và trị giá hải quan cần nhân viên có nghiệp vụ tra cứu và ghi rõ căn cứ.
                      </p>
                    </div>
                  </div>
                  <section className="surface padded">
                    <h2>Checklist theo điều kiện hồ sơ</h2>
                    <div className="requirements">
                      {Object.entries(current.case.requirements).map(([kind, rule]: Any) => (
                        <div className="requirement" key={kind}>
                          <div>
                            <div className="row" style={{ gap: 8 }}>
                              <strong>{kind}</strong>
                              <span className={'badge ' + (rule.required ? 'info' : 'neutral')}>
                                {rule.required ? 'Bắt buộc trong checklist' : 'Đã miễn có lý do'}
                              </span>
                            </div>
                            <small>{rule.note}</small>
                          </div>
                          <button
                            className="btn small"
                            onClick={() =>
                              setDialog({
                                kind: 'requirement',
                                documentType: kind,
                                required: !rule.required,
                                note: '',
                              })
                            }
                          >
                            {rule.required ? 'Đang yêu cầu' : 'Không bắt buộc'}
                          </button>
                        </div>
                      ))}
                    </div>
                  </section>
                  <section className="surface padded">
                    <div className="section-title">
                      <h2>Chỉ tiêu cần nhập / tra cứu</h2>
                      <button
                        className="btn"
                        onClick={() => setDialog({ kind: 'record', recordKind: 'field', defaultKey: 'hs_code', value: '', note: '' })}
                      >
                        <Plus size={16} />
                        Bổ sung chỉ tiêu
                      </button>
                    </div>
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Chỉ tiêu</th>
                            <th>Nhóm</th>
                            <th>Tình trạng</th>
                            <th>Hướng xử lý</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.values(dict.fields)
                            .filter((f: Any) => ['C', 'D'].includes(f.class))
                            .map((f: Any) => (
                              <tr key={f.id}>
                                <td>
                                  <strong>{f.label}</strong>
                                  <small>{f.id}</small>
                                </td>
                                <td>{f.class === 'C' ? 'Nhóm C · Danh mục mã' : 'Nhóm D · Quyết định chuyên môn'}</td>
                                <td>
                                  {current.records
                                    .filter((r: Any) => r.key === f.id)
                                    .map((r: Any) => (
                                      <div key={r.id}>
                                        {textValue(r.value)} <Badge status={r.status} />
                                      </div>
                                    ))}
                                  {!current.records.some((r: Any) => r.key === f.id) && (
                                    <Badge status="Missing" />
                                  )}
                                </td>
                                <td>
                                  <div className="row" style={{ justifyContent: 'space-between' }}>
                                    <span>Tra cứu nguồn chính thức và ghi căn cứ áp dụng.</span>
                                    <button
                                      className="btn small"
                                      onClick={() =>
                                        setDialog({
                                          kind: 'record',
                                          recordKind: 'field',
                                          defaultKey: f.id,
                                          value: '',
                                          note: '',
                                        })
                                      }
                                    >
                                      Nhập {f.label}
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    </div>
                  </section>
                </>
              )}

              {tab === 'export' && (
                <>
                  <div className="export-layout">
                    <section className="surface padded">
                      <div className="export-icon">
                        <FileSpreadsheet size={28} />
                      </div>
                      <h2>Xuất hồ sơ làm việc</h2>
                      <p className="muted">
                        7 sheet tiêu chuẩn, giữ nguyên mọi nguồn, số zero đầu và trạng thái xác minh. Không tự ghi đè nguồn đang xung đột.
                      </p>
                      <label className="form-label">
                        Loại workbook
                        <select
                          aria-label="Loại workbook"
                          value={workbookType}
                          onChange={(e) => setWorkbookType(e.target.value)}
                        >
                          <option value="A">A · Workbook kiểm tra nội bộ</option>
                          <option value="B">B · Chuẩn bị dữ liệu khai báo</option>
                        </select>
                      </label>
                      <label className="form-label">
                        Phiên bản
                        <select
                          aria-label="Phiên bản"
                          value={exportMode}
                          onChange={(e) => setExportMode(e.target.value)}
                        >
                          <option value="Draft">Draft</option>
                          <option value="Reviewed">Reviewed</option>
                        </select>
                      </label>
                      <div className={'alert ' + (exportMode === 'Draft' ? 'warn' : 'info')}>
                        <div>
                          <strong>
                            {exportMode === 'Draft'
                              ? 'Bản nháp (Draft) — Không đồng nghĩa hồ sơ đã hoàn thành kiểm tra'
                              : 'Bản đã kiểm tra (Reviewed) — Đã qua các cổng kiểm tra nội bộ'}
                          </strong>
                          <p>
                            {exportMode === 'Draft'
                              ? 'Draft cho phép xuất ngay cả khi còn dữ liệu chờ xác minh hoặc cảnh báo sai lệch để nhân viên trao đổi nội bộ. Trạng thái từng nguồn được giữ rõ trong 7 sheet.'
                              : 'Reviewed chỉ xuất được sau khi toàn bộ tài liệu đã xác nhận loại, mọi bản ghi đã xác minh, không còn cảnh báo chặn và hồ sơ đã bấm Hoàn thành kiểm tra.'}
                          </p>
                        </div>
                      </div>
                      <details>
                        <summary>Chọn trường cấp hồ sơ (mặc định tất cả)</summary>
                        <div className="field-choices">
                          {Object.values(dict.fields).map((f: Any) => (
                            <label className="check-label" key={f.id}>
                              <input
                                type="checkbox"
                                checked={selectedFields.includes(f.id)}
                                onChange={(e) =>
                                  setSelectedFields(
                                    e.target.checked
                                      ? [...selectedFields, f.id]
                                      : selectedFields.filter((x) => x !== f.id)
                                  )
                                }
                              />
                              {f.label}
                            </label>
                          ))}
                        </div>
                      </details>
                      <div className="export-actions">
                        {['Draft', 'Reviewed'].map((version) => (
                          <button key={version} className={'btn full ' + (version === 'Reviewed' ? 'primary' : '')}
                            disabled={loading || !current.records.some((r: Any) => r.status !== 'rejected') || (version === 'Reviewed' && (current.blockers.length > 0 || !current.case.reviewed_at))}
                            onClick={() => run(async () => {
                              const result = await post('/cases/' + current.case.id + '/export', { mode: version, workbook_type: workbookType, selected: selectedFields.length ? selectedFields : null });
                              setExportMode(version);
                              replace(await api('/cases/' + current.case.id));
                              await refresh();
                              const anchor = document.createElement('a');
                              anchor.href = result.download;
                              anchor.download = '';
                              anchor.click();
                              notify('Đã tạo Excel ' + version);
                            })}>
                            <Download size={17} />{version === 'Draft' ? 'Xuất bản nháp (.xlsx)' : 'Xuất bản đã duyệt (.xlsx)'}
                          </button>
                        ))}
                        {(!current.case.reviewed_at || current.blockers.length > 0) && <p className="muted">Bản đã duyệt đang khóa: còn {current.blockers.length} điều kiện chặn hoặc chưa hoàn thành kiểm tra hồ sơ. Bản nháp vẫn xuất được khi có dữ liệu.</p>}
                      </div>
                    </section>

                    <section className="surface padded">
                      <div className="section-title">
                        <h2>Xem trước nội dung</h2>
                        <Badge status={exportMode} />
                      </div>
                      <div className="export-counts">
                        <div>
                          <strong>
                            {current.records.filter((r: Any) => r.kind === 'field' && r.status !== 'rejected').length}
                          </strong>
                          <span>Trường dữ liệu</span>
                        </div>
                        <div>
                          <strong>
                            {current.records.filter((r: Any) => r.kind === 'item' && r.status !== 'rejected').length}
                          </strong>
                          <span>Dòng hàng độc lập</span>
                        </div>
                        <div>
                          <strong>
                            {containerStats.physicalCount} <small style={{ display: 'inline', fontSize: 14 }}>vật lý</small>
                          </strong>
                          <span>Container ({containerStats.sourceRecordCount} bản ghi nguồn)</span>
                        </div>
                      </div>
                      <div className="workbook-sheets">
                        {[
                          'Tổng quan hồ sơ',
                          'Thông tin khai báo',
                          'Chi tiết hàng hóa',
                          'Container vận chuyển',
                          'Đối chiếu chứng từ',
                          'Thiếu và cần xác minh',
                          'Nguồn và lịch sử',
                        ].map((s, i) => (
                          <div key={s}>
                            <FileSpreadsheet size={17} />
                            <span>
                              {i + 1}. {s}
                            </span>
                          </div>
                        ))}
                      </div>
                      <div className="table-wrap">
                        <table>
                          <thead>
                            <tr>
                              <th>Chỉ tiêu</th>
                              <th>Giá trị</th>
                              <th>Nguồn</th>
                              <th>Trạng thái</th>
                            </tr>
                          </thead>
                          <tbody>
                            {current.records
                              .filter(
                                (r: Any) =>
                                  r.kind === 'field' &&
                                  r.status !== 'rejected' &&
                                  (!selectedFields.length || selectedFields.includes(r.key))
                              )
                              .slice(0, 20)
                              .map((r: Any) => {
                                const docObj = current.documents.find((d: Any) => d.id === r.document_id);
                                return (
                                  <tr key={r.id}>
                                    <td>{dict.fields[r.key]?.label}</td>
                                    <td>{textValue(r.value)}</td>
                                    <td className="muted">
                                      {docObj?.name || 'Nhập tay'}
                                      {r.page ? ' · ' + unitLabel(docObj || r.method, r.page) : ''}
                                    </td>
                                    <td>
                                      <Badge status={r.status} />
                                    </td>
                                  </tr>
                                );
                              })}
                          </tbody>
                        </table>
                      </div>
                      <details style={{ marginTop: 12 }}>
                        <summary>Checklist xuất Reviewed ({current.blockers.length} mục còn thiếu)</summary>
                        <ul>
                          {current.blockers.map((s: string) => (
                            <li key={s}>{s}</li>
                          ))}
                        </ul>
                      </details>
                    </section>
                  </div>

                  <section className="surface padded">
                    <h2>Lịch sử phiên bản Excel</h2>
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Phiên bản</th>
                            <th>Loại workbook</th>
                            <th>Độ mới so với hồ sơ</th>
                            <th>Thời gian</th>
                            <th>Download</th>
                          </tr>
                        </thead>
                        <tbody>
                          {current.exports.map((e: Any) => {
                            const isCurrentRev =
                              e.case_revision === undefined || e.case_revision === current.case.revision;
                            return (
                              <tr key={e.id}>
                                <td>
                                  <strong>v{e.version}</strong> · <Badge status={e.mode} />
                                </td>
                                <td>{e.workbook_type}</td>
                                <td>
                                  <span className={'badge ' + (isCurrentRev ? 'good' : 'warn')}>
                                    {isCurrentRev
                                      ? `Khớp bản sửa #${current.case.revision}`
                                      : `Bản cũ (rev #${e.case_revision} · hồ sơ đã sửa sang #${current.case.revision})`}
                                  </span>
                                </td>
                                <td>{date(e.created_at)}</td>
                                <td>
                                  <a className="text-btn" href={'/api/exports/' + e.id}>
                                    Tải XLSX
                                  </a>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                    {!current.exports.length && <p className="muted">Chưa xuất phiên bản nào.</p>}
                  </section>

                  <TemplateCenter
                    current={current}
                    dict={dict}
                    run={run}
                    refresh={async () => replace(await api('/cases/' + current.case.id))}
                  />
                </>
              )}

              {tab === 'case-history' && <AuditTable rows={audit} />}
            </>
          )}

          {view === 'history' && (
            <>
              <div className="page-heading">
                <div>
                  <h1>Lịch sử xử lý</h1>
                  <p>Nhật ký thao tác local với giá trị trước và sau khi thay đổi.</p>
                </div>
              </div>
              <AuditTable rows={audit} />
            </>
          )}

          {view === 'settings' && (
            <SettingsPage health={health} refresh={refresh} run={run} notify={notify} />
          )}

          <footer className="app-footer">
            U&I SMART · Hồ sơ chứng từ nhập khẩu FCL{' '}
            <span>Local first · Nhân viên xác minh cuối cùng</span>
          </footer>
        </main>
      </div>

      {toast && (
        <div className="toast" role="status">
          <Check size={18} />
          <span>{toast}</span>
        </div>
      )}

      {dialog && (
        <div
          className="modal-overlay"
          onClick={(e) => {
            if (e.target === e.currentTarget) setDialog(null);
          }}
        >
          <dialog
            open
            className="modal"
            aria-modal="true"
            aria-label="Thao tác hồ sơ"
            onKeyDown={(e) => {
              if (e.key === 'Escape') setDialog(null);
            }}
          >
            <button
              className="modal-close icon-btn"
              aria-label="Đóng hộp thoại"
              onClick={() => setDialog(null)}
            >
              <X size={20} />
            </button>
            {error && (
              <div className="alert bad" role="alert">
                {error}
              </div>
            )}
            <DialogContent
              key={dialog.kind + ':' + (dialog.record?.id || dialog.defaultKey || 'new')}
              dialog={dialog}
              setDialog={setDialog}
              dict={dict}
              current={current}
              loading={loading}
              submit={async (payload: Any) => {
                if (dialog.kind === 'case') {
                  const b = await run(
                    () => post('/cases', { name: payload.name, customer: payload.customer }),
                    'Đã tạo hồ sơ'
                  );
                  if (b) {
                    setDialog(null);
                    await refresh();
                    await openCase(b.case.id);
                  }
                } else if (dialog.kind === 'record') {
                  const r = dialog.record;
                  const b = await update(
                    () =>
                      r
                        ? patch('/records/' + r.id, {
                            value: payload.value,
                            note: payload.note,
                            version: r.version,
                          })
                        : post('/cases/' + current.case.id + '/records', {
                            kind: dialog.recordKind,
                            key:
                              payload.key ||
                              (dialog.recordKind === 'item' ? 'goods_item' : 'container'),
                            value: payload.value,
                            note: payload.note,
                            document_id: payload.document_id || null,
                            page: payload.page ? Number(payload.page) : null,
                          }),
                    'Đã lưu dữ liệu · cần xác minh'
                  );
                  if (b) setDialog(null);
                } else if (dialog.kind === 'resolve') {
                  const b = await update(
                    () => post('/checks/' + dialog.check.id + '/resolve', { note: payload.note }),
                    'Đã ghi nhận lý do'
                  );
                  if (b) setDialog(null);
                } else if (dialog.kind === 'requirement') {
                  const b = await update(
                    () =>
                      patch(
                        '/cases/' +
                          current.case.id +
                          '/requirements/' +
                          encodeURIComponent(dialog.documentType),
                        { required: dialog.required, note: payload.note }
                      ),
                    'Đã cập nhật checklist'
                  );
                  if (b) setDialog(null);
                } else if (dialog.kind === 'delete-doc') {
                  const b = await update(
                    () => api('/documents/' + dialog.document.id, { method: 'DELETE' }),
                    'Đã xóa chứng từ'
                  );
                  if (b) {
                    setSelectedDoc(b.documents[0]?.id || '');
                    setPage(1);
                    setDialog(null);
                  }
                } else if (dialog.kind === 'delete-case') {
                  const b = await run(
                    () => api('/cases/' + current.case.id, { method: 'DELETE' }),
                    'Đã xóa hồ sơ'
                  );
                  if (b) {
                    setDialog(null);
                    setCurrent(null);
                    setView('cases');
                    location.hash = '';
                    await refresh();
                  }
                }
              }}
            />
          </dialog>
        </div>
      )}
    </div>
  );
}

function AuditTable({ rows }: Any) {
  return (
    <section className="surface">
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Thời gian / người thực hiện</th>
              <th>Thao tác</th>
              <th>Giá trị trước → sau</th>
              <th>Lý do</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r: Any) => (
              <tr key={r.id}>
                <td>
                  {date(r.created_at)}
                  <small>{r.actor}</small>
                </td>
                <td>
                  {r.action}
                  <small>{r.case_id}</small>
                </td>
                <td>
                  <details>
                    <summary>Xem thay đổi</summary>
                    <pre>{r.before_json}</pre>
                    <ArrowRight size={14} />
                    <pre>{r.after_json}</pre>
                  </details>
                </td>
                <td>{r.reason || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!rows.length && <div className="empty">Chưa có thao tác được ghi nhận.</div>}
      </div>
    </section>
  );
}

function DialogContent({ dialog, dict, current, loading, submit }: Any) {
  const [name, setName] = useState('');
  const [customer, setCustomer] = useState('');
  const [fieldKey, setFieldKey] = useState(dialog.record?.key || dialog.defaultKey || 'invoice_number');
  const [value, setValue] = useState<Any>(
    dialog.record?.kind === 'field' ? textValue(dialog.record.value) : dialog.value || {}
  );
  const [note, setNote] = useState(dialog.note || '');
  const [source, setSource] = useState('');
  const [page, setPage] = useState('1');
  const kind = dialog.kind;
  const item = dialog.recordKind === 'item';
  const properties = item
    ? ['line_number', 'product_code', 'description', 'quantity', 'unit', 'unit_price', 'line_amount', 'currency', 'origin', 'hs_code']
    : ['container_number', 'seal_number', 'container_type', 'packages', 'gross_weight', 'cbm', 'bl_number'];
  const titles: Any = {
    line_number: 'STT',
    product_code: 'Mã hàng',
    description: 'Mô tả hàng',
    quantity: 'Số lượng (không dấu nhóm nghìn)',
    unit: 'Đơn vị',
    unit_price: 'Đơn giá',
    line_amount: 'Thành tiền',
    currency: 'Tiền tệ',
    origin: 'Xuất xứ',
    hs_code: 'Mã HS đã có căn cứ',
    container_number: 'Số container (4 chữ + 7 số)',
    seal_number: 'Seal',
    container_type: 'Loại container',
    packages: 'Số kiện',
    gross_weight: 'Gross Weight',
    cbm: 'CBM',
    bl_number: 'Số B/L',
  };
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        submit({
          name,
          customer,
          key: fieldKey,
          value: dialog.recordKind === 'field' ? (typeof value === 'string' ? value : '') : value,
          note,
          document_id: source,
          page: source ? page : null,
        });
      }}
    >
      <h2>
        {kind === 'case'
          ? 'Tạo hồ sơ mới'
          : kind === 'record'
          ? 'Kiểm tra và nhập dữ liệu'
          : kind === 'resolve'
          ? 'Ghi nhận xử lý sai lệch'
          : kind === 'requirement'
          ? 'Điều chỉnh checklist chứng từ'
          : 'Xác nhận xóa'}
      </h2>
      {kind === 'case' ? (
        <>
          <p className="muted">Một hồ sơ lưu nhiều tài liệu, dòng hàng và container.</p>
          <label className="form-label">
            Tên hồ sơ
            <input
              autoFocus
              required
              maxLength={160}
              placeholder="VD: Lô thiết bị tháng 10"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
          <label className="form-label">
            Khách hàng (tùy chọn)
            <input
              maxLength={160}
              value={customer}
              onChange={(e) => setCustomer(e.target.value)}
            />
          </label>
        </>
      ) : kind === 'record' ? (
        <>
          {dialog.recordKind === 'field' ? (
            <>
              <label className="form-label">
                Chỉ tiêu
                <select
                  disabled={!!dialog.record}
                  value={dialog.record?.key || fieldKey}
                  onChange={(e) => setFieldKey(e.target.value)}
                >
                  {Object.values(dict.fields).map((f: Any) => (
                    <option key={f.id} value={f.id}>
                      {f.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="form-label">
                Giá trị
                <input
                  required
                  value={typeof value === 'string' ? value : ''}
                  onChange={(e) => setValue(e.target.value)}
                />
              </label>
            </>
          ) : (
            <div className="form-grid">
              {properties.map((k) => (
                <label className="form-label" key={k}>
                  {titles[k]}
                  <input
                    required={k === 'description' || k === 'container_number'}
                    value={value[k] || ''}
                    onChange={(e) => setValue({ ...value, [k]: e.target.value })}
                  />
                </label>
              ))}
            </div>
          )}
          {!dialog.record && (
            <div className="form-grid">
              <label className="form-label">
                Chứng từ nguồn
                <select value={source} onChange={(e) => setSource(e.target.value)}>
                  <option value="">Nhập tay · ghi căn cứ</option>
                  {current.documents.map((d: Any) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </label>
              {source && (
                <label className="form-label">
                  Đơn vị / Trang nguồn
                  <input
                    type="number"
                    min={1}
                    max={100}
                    value={page}
                    onChange={(e) => setPage(e.target.value)}
                  />
                </label>
              )}
            </div>
          )}
          <label className="form-label">
            Ghi chú / căn cứ (bắt buộc)
            <textarea
              required
              minLength={3}
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </label>
        </>
      ) : kind === 'resolve' || kind === 'requirement' ? (
        <>
          <p>
            {kind === 'resolve'
              ? dialog.check.detail.reason
              : `${dialog.documentType}: ${dialog.required ? 'Yêu cầu bổ sung' : 'Không áp dụng'}. Ghi căn cứ theo hồ sơ thực tế.`}
          </p>
          <label className="form-label">
            Lý do và căn cứ
            <textarea
              autoFocus
              required
              minLength={5}
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </label>
        </>
      ) : (
        <p>
          {kind === 'delete-doc' ? dialog.document.name : current.case.name} sẽ bị xóa cùng dữ liệu liên quan. Thao tác này không có hoàn tác; tạo backup trước nếu cần.
        </p>
      )}
      <div className="modal-actions">
        <button
          type="button"
          className="btn"
          onClick={() => {
            document.querySelector<HTMLButtonElement>('.modal-close')?.click();
          }}
        >
          Hủy
        </button>
        <button
          className={'btn ' + (kind.startsWith('delete') ? 'destructive' : 'primary')}
          disabled={loading}
        >
          {loading ? <Loader2 size={16} className="spin" /> : null}
          {kind === 'case' ? 'Tạo hồ sơ' : kind.startsWith('delete') ? 'Xóa' : 'Lưu'}
        </button>
      </div>
    </form>
  );
}

function SettingsPage({ health, refresh, run, notify }: Any) {
  const [key, setKey] = useState('');
  const [model, setModel] = useState(health?.ai.model || 'gpt-4.1-mini');
  const [show, setShow] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [saving, setSaving] = useState(false);
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Cài đặt không gian làm việc</h1>
          <p>Kiểm tra dịch vụ local và kết nối AI khi cần.</p>
        </div>
      </div>
      <section className="surface padded">
        <h2>Trạng thái hệ thống</h2>
        <div className="health-grid">
          {[
            ['Backend', health?.ok ? 'Đã kết nối' : 'Chưa kết nối'],
            ['SQLite', health?.database_ready ? 'Sẵn sàng' : 'Chưa kiểm tra'],
            [
              'OCR local',
              health?.ocr.ready
                ? 'Sẵn sàng · ' + health.ocr.languages.join(', ')
                : 'Chưa cài Tesseract',
            ],
            [
              'OpenAI',
              health?.ai.connected
                ? 'Đã kiểm tra kết nối'
                : health?.ai.configured
                ? 'Đã cấu hình · chưa kiểm tra'
                : 'Chưa cấu hình',
            ],
          ].map(([s, t]) => (
            <div key={s}>
              <span>{s}</span>
              <strong>{t}</strong>
            </div>
          ))}
        </div>
        <button className="btn" onClick={() => run(refresh)}>
          Kiểm tra lại
        </button>
      </section>
      <section className="surface padded settings-ai">
        <div className="section-title">
          <div>
            <h2>Kết nối OpenAI</h2>
            <p className="muted">AI hỗ trợ từ bước 3. Local vẫn dùng được khi chưa có key.</p>
          </div>
          <Link2 size={22} />
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setSaving(true);
            run(async () => {
              try {
                await post('/ai/configure', { api_key: key.trim(), model: model.trim() });
                setKey('');
                await refresh();
                notify('Đã lưu cấu hình trong bộ nhớ phiên backend');
              } finally { setSaving(false); }
            });
          }}
        >
          <label className="form-label">
            API key
            <div className="password-input">
              <input
                aria-label="API key"
                autoComplete="off"
                type={show ? 'text' : 'password'}
                value={key}
                disabled={connecting || saving}
                onChange={(e) => setKey(e.target.value)}
                placeholder="Nhập key trực tiếp tại đây"
              />
              <button className="text-btn" type="button" onClick={() => setShow(!show)}>
                {show ? 'Ẩn' : 'Hiện'}
              </button>
            </div>
          </label>
          <label className="form-label">
            Model
            <input aria-label="Model OpenAI" value={model} disabled={connecting || saving} onChange={(e) => setModel(e.target.value)} required />
            <small>Chọn model có quyền truy cập và hỗ trợ Structured Outputs.</small>
          </label>
          <div className="row">
            <button className="btn primary" disabled={connecting || saving}>{saving ? 'Đang lưu…' : 'Lưu cấu hình'}</button>
            <button
              className="btn"
              type="button"
              disabled={connecting || saving || (!health?.ai.configured && !key.trim())}
              onClick={() => {
                setConnecting(true);
                run(async () => {
                  try {
                    if (key.trim() || model.trim() !== health?.ai.model) {
                      await post('/ai/configure', { api_key: key.trim(), model: model.trim() });
                      setKey('');
                    }
                    await post('/ai/test');
                    notify('OpenAI đã trả kết quả thử thành công');
                  } finally {
                    try { await refresh(); } finally { setConnecting(false); }
                  }
                });
              }}
            >
              {connecting && <Loader2 size={16} className="spin" />}
              {connecting ? 'Đang kết nối…' : 'Kiểm tra kết nối'}
            </button>
            <button
              className="text-btn danger"
              type="button"
              disabled={connecting || saving || !health?.ai.configured}
              onClick={() =>
                run(async () => {
                  await api('/ai/configure', { method: 'DELETE' });
                  await refresh();
                  notify('Đã xóa key trong phiên backend');
                })
              }
            >
              Xóa key
            </button>
          </div>
        </form>
        <p className="help-inline" role="status">
          {health?.ai.connected ? `Đã kết nối · ${health.ai.model} · đã nhận phản hồi AI có cấu trúc${health.ai.checked_at ? ' · ' + date(health.ai.checked_at) : ''}.` : 'Nhập key rồi bấm Kiểm tra kết nối; app tự lưu cấu hình trước khi thử.'}
        </p>
        <small>Kiểm tra gửi một yêu cầu thử ngắn tới OpenAI, có thể tính phí API; không gửi chứng từ của hồ sơ.</small>
        <p className="help-inline">
          Key nằm trong bộ nhớ backend, không được lưu vào trình duyệt, SQLite hay Excel. Khởi động lại cần nhập lại nếu không cấu hình bằng biến môi trường.
        </p>
        <a
          className="text-btn"
          href="https://platform.openai.com/api-keys"
          target="_blank"
          rel="noreferrer"
        >
          Mở trang tạo API key OpenAI <ArrowRight size={14} />
        </a>
        <div className="usage-strip">
          <span>Yêu cầu API: {health?.ai.usage.requests || 0}</span>
          <span>Input: {health?.ai.usage.input_tokens || 0} token</span>
          <span>Output: {health?.ai.usage.output_tokens || 0} token</span>
          <span>Chi phí: chưa tính</span>
        </div>
      </section>
      <section className="surface padded">
        <h2>Backup dữ liệu local</h2>
        <p className="muted">
          Bao gồm SQLite, chứng từ gốc, Excel và template; không chứa API key.
        </p>
        <button
          className="btn"
          onClick={() =>
            run(async () => {
              const b = await post('/backup');
              const a = document.createElement('a');
              a.href = b.download;
              a.click();
              notify('Đã tạo backup local');
            })
          }
        >
          <Download size={16} />
          Tạo & tải backup
        </button>
        <p className="muted">
          Khôi phục bằng restore-local.ps1 khi backend đã dừng. Backup chứa dữ liệu thương mại; lưu ở nơi bạn quản lý.
        </p>
      </section>
      <section className="surface padded">
        <h2>Phạm vi tích hợp</h2>
        <p className="muted">
          ONP / TMS / WMS và template import phần mềm khai báo: chưa kết nối. Giao diện hiện tại tập trung bộ phận chứng từ FCL.
        </p>
      </section>
    </>
  );
}

if (typeof document !== 'undefined' && document.getElementById('root')) {
  createRoot(document.getElementById('root')!).render(<App />);
}

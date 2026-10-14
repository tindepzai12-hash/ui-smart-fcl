import React, { useEffect, useState } from 'react';
import { api, post, textValue, label, unitLabel } from './api';
import { Upload, Plus, Download, Trash2, FileSpreadsheet } from 'lucide-react';

export function TemplateCenter({ current, dict, run, refresh }: any) {
  const [templates, setTemplates] = useState<any[]>([]);
  const [template, setTemplate] = useState<any>(null);
  const [mapping, setMapping] = useState<any[]>([]);

  useEffect(() => {
    api('/templates')
      .then((list: any[]) => {
        if (Array.isArray(list)) setTemplates(list);
      })
      .catch(() => {});
  }, [current?.case?.id]);

  async function load(file: File) {
    const fd = new FormData();
    fd.append('file', file);
    await run(async () => {
      const t = await api('/templates', { method: 'POST', body: fd });
      setTemplate(t);
      setMapping([]);
      const list = await api('/templates').catch(() => []);
      if (Array.isArray(list)) setTemplates(list);
    });
  }

  function selectSavedTemplate(id: string) {
    const found = templates.find((t: any) => t.id === id);
    if (!found) {
      setTemplate(null);
      setMapping([]);
      return;
    }
    setTemplate(found);
    const validIds = new Set(
      (current?.records || [])
        .filter((r: any) => r.kind === 'field' && r.status !== 'rejected')
        .map((r: any) => r.id)
    );
    const restored = Array.isArray(found.mapping)
      ? found.mapping.filter((m: any) => validIds.has(m.record_id))
      : [];
    setMapping(restored);
  }

  const records = (current?.records || []).filter((r: any) => r.kind === 'field' && r.status !== 'rejected');

  return (
    <section className="surface padded">
      <div className="section-title">
        <div>
          <h2>Mapping vào template XLSX của bạn</h2>
          <p className="muted">
            Chọn nguồn và ô đích cụ thể. Bản xuất là file làm việc Draft (kèm sheet truy vết <code>UI_SMART_NGUON</code>); chưa xác minh tương thích phần mềm khai báo bên ngoài (VNACCS/ECUS).
          </p>
        </div>
        <span className="badge neutral">Chỉ hỗ trợ ô đơn (scalar) · Nội bộ</span>
      </div>
      <div className="row" style={{ marginTop: 14 }}>
        <label className="btn upload-btn">
          <Upload size={16} />
          Chọn template XLSX
          <input
            aria-label="Tải template XLSX"
            type="file"
            accept=".xlsx"
            hidden
            onChange={(e) => {
              if (e.target.files?.[0]) load(e.target.files[0]);
              e.target.value = '';
            }}
          />
        </label>
        {templates.length > 0 && (
          <select
            aria-label="Chọn template đã lưu"
            value={template?.id || ''}
            onChange={(e) => selectSavedTemplate(e.target.value)}
          >
            <option value="">— Chọn mẫu XLSX đã tải trước đây ({templates.length}) —</option>
            {templates.map((t: any) => (
              <option key={t.id} value={t.id}>
                {t.name || t.id}
              </option>
            ))}
          </select>
        )}
        {template && (
          <>
            <span className="badge good">Template đã đọc</span>
            <button
              className="btn"
              onClick={() =>
                setMapping([
                  ...mapping,
                  { sheet: Object.keys(template.sheets)[0], cell: '', record_id: '' },
                ])
              }
            >
              <Plus size={16} />
              Thêm ô mapping
            </button>
          </>
        )}
      </div>
      {template && (
        <>
          <details style={{ marginTop: 14 }}>
            <summary>Xem danh sách sheet và ô tiêu đề trong template để xác định ô đích</summary>
            <div className="template-preview-grid">
              {Object.entries(template.sheets || {}).map(([sheetName, cells]: any) => (
                <div key={sheetName} className="template-sheet-box">
                  <strong>
                    <FileSpreadsheet size={14} /> Sheet: {sheetName}
                  </strong>
                  <div className="template-cells">
                    {(cells || []).map((c: any) => (
                      <span key={c.cell} className="badge neutral">
                        {c.cell}: {c.header}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </details>
          <div className="table-wrap" style={{ marginTop: 12 }}>
            <table>
              <thead>
                <tr>
                  <th>Sheet</th>
                  <th>Ô đích (vd: B3)</th>
                  <th>Bản ghi và nguồn cụ thể</th>
                  <th>Xóa</th>
                </tr>
              </thead>
              <tbody>
                {mapping.map((m, i) => (
                  <tr key={i}>
                    <td>
                      <select
                        aria-label={'Sheet mapping ' + (i + 1)}
                        value={m.sheet}
                        onChange={(e) =>
                          setMapping(mapping.map((v, j) => (j === i ? { ...v, sheet: e.target.value } : v)))
                        }
                      >
                        {Object.keys(template.sheets).map((s) => (
                          <option key={s}>{s}</option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <input
                        aria-label={'Ô đích ' + (i + 1)}
                        placeholder="B3"
                        value={m.cell}
                        onChange={(e) =>
                          setMapping(
                            mapping.map((v, j) =>
                              j === i ? { ...v, cell: e.target.value.toUpperCase().trim() } : v
                            )
                          )
                        }
                      />
                    </td>
                    <td>
                      <select
                        aria-label={'Nguồn mapping ' + (i + 1)}
                        value={m.record_id}
                        onChange={(e) =>
                          setMapping(
                            mapping.map((v, j) => (j === i ? { ...v, record_id: e.target.value } : v))
                          )
                        }
                      >
                        <option value="">Chọn nguồn cụ thể</option>
                        {records.map((r: any) => {
                          const docObj = current.documents.find((d: any) => d.id === r.document_id);
                          const docName = docObj?.name || 'Nhập tay';
                          const uLabel = r.page ? ' · ' + unitLabel(docObj || r.method, r.page) : '';
                          const fieldTitle = dict?.fields?.[r.key]?.label ? `${dict.fields[r.key].label} (${r.key})` : r.key;
                          return (
                            <option key={r.id} value={r.id}>
                              {r.key} = {textValue(r.value)} · {docName}
                              {uLabel} · {label(r.status)} ({fieldTitle})
                            </option>
                          );
                        })}
                      </select>
                    </td>
                    <td>
                      <button
                        className="icon-btn danger"
                        aria-label={'Xóa mapping ' + (i + 1)}
                        onClick={() => setMapping(mapping.filter((_, j) => i !== j))}
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!mapping.length && (
              <div className="empty compact">
                Bấm “Thêm ô mapping” để gán một trường dữ liệu từ chứng từ nguồn vào ô đích trong file XLSX.
              </div>
            )}
          </div>
          <div className="row" style={{ marginTop: 14 }}>
            <button
              className="btn primary"
              disabled={!mapping.length || mapping.some((m) => !m.cell || !m.record_id)}
              onClick={() =>
                run(async () => {
                  const r = await post('/templates/' + template.id + '/export', {
                    case_id: current.case.id,
                    mapping,
                  });
                  const a = document.createElement('a');
                  a.href = r.download;
                  a.click();
                  await refresh();
                })
              }
            >
              <Download size={16} />
              Xuất bản mapping nội bộ
            </button>
          </div>
        </>
      )}
    </section>
  );
}

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const ts = (await import('typescript')).default;
const React = (await import('react')).default;
const { renderToStaticMarkup } = await import('react-dom/server');
const compileTsx = (code, filename = 'mod.tsx') => ts.transpileModule(code, {
  fileName: filename,
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.React },
}).outputText;

const apiSource = fs.readFileSync(path.join(root, 'frontend/api.ts'), 'utf8');
const apiJs = compileTsx(apiSource, 'api.ts');
const helper = await import('data:text/javascript;base64,' + Buffer.from(apiJs).toString('base64'));

const mainSource = fs.readFileSync(path.join(root, 'frontend/main.tsx'), 'utf8');
const strippedMain = mainSource
  .replace(/^\s*import\s+[\s\S]*?from\s+['"][^'"]+['"];?\s*$/gm, '')
  .replace(/^\s*import\s+['"][^'"]+['"];?\s*$/gm, '')
  .replace(/if\s*\(typeof document[\s\S]*$/, '');

const componentModuleSource = `
const React = globalThis.__TEST_REACT__;
const { useState, useEffect } = React;
const createRoot = () => ({ render: () => {} });
const IconStub = (name) => (props) => React.createElement('svg', { 'data-icon': name, ...props });
const LayoutDashboard = IconStub('LayoutDashboard'), FolderOpen = IconStub('FolderOpen'),
  FileCheck2 = IconStub('FileCheck2'), History = IconStub('History'), Settings = IconStub('Settings'),
  PanelLeftClose = IconStub('PanelLeftClose'), Plus = IconStub('Plus'), ArrowRight = IconStub('ArrowRight'),
  FileText = IconStub('FileText'), Upload = IconStub('Upload'), ChevronLeft = IconStub('ChevronLeft'),
  ChevronRight = IconStub('ChevronRight'), Search = IconStub('Search'), Check = IconStub('Check'),
  AlertTriangle = IconStub('AlertTriangle'), Download = IconStub('Download'), RotateCw = IconStub('RotateCw'),
  ZoomIn = IconStub('ZoomIn'), ZoomOut = IconStub('ZoomOut'), ShieldCheck = IconStub('ShieldCheck'),
  X = IconStub('X'), Loader2 = IconStub('Loader2'), Trash2 = IconStub('Trash2'),
  Undo2 = IconStub('Undo2'), Eye = IconStub('Eye'), FileSpreadsheet = IconStub('FileSpreadsheet'),
  HardDrive = IconStub('HardDrive'), Link2 = IconStub('Link2');
const { api, post, patch, textValue, label, tone, unitLabel, physicalContainerStats, humanCheckTitle, computeStepStates } = globalThis.__TEST_HELPER__;
const TemplateCenter = () => null;
${compileTsx(strippedMain, 'main.tsx')}
`;

globalThis.__TEST_REACT__ = React;
globalThis.__TEST_HELPER__ = helper;
const components = await import(
  'data:text/javascript;base64,' + Buffer.from(componentModuleSource).toString('base64')
);

test('Show normalized number/unit, preserve leading zero text, and format container/item values cleanly', () => {
  assert.equal(helper.textValue({ number: '1000', unit: 'KG' }), '1000 KG');
  assert.equal(helper.textValue({ text: '000123-A' }), '000123-A');
  assert.equal(
    helper.textValue({ container_number: 'CSNU7654321', seal_number: 'SEAL02', container_type: '40HC' }),
    'CSNU7654321 · Seal: SEAL02 · Loại: 40HC'
  );
});

test('Status label/tone distinguishes extracted pending from verified, Draft from Reviewed, and save states', () => {
  assert.equal(helper.label('pending'), 'Chờ xác minh');
  assert.equal(helper.tone('pending'), 'warn');
  assert.equal(helper.tone('verified'), 'good');
  assert.equal(helper.tone('Mismatch'), 'bad');
  assert.equal(helper.label('Draft'), 'Bản nháp (Draft)');
  assert.equal(helper.label('Reviewed'), 'Đã kiểm tra (Reviewed)');
  assert.equal(helper.label('saving'), 'Đang lưu…');
  assert.equal(helper.label('save_error'), 'Lưu lỗi');
});

test('API errors surface domain error and mutation header is supplied', async () => {
  const before = global.fetch;
  global.fetch = async (_url, opts) => {
    assert.equal(opts.headers['X-UI-Smart'], 'local');
    return { ok: false, json: async () => ({ detail: 'Hồ sơ chưa được xác minh' }) };
  };
  try {
    await assert.rejects(() => helper.post('/cases/id/review'), /chưa được xác minh/);
  } finally {
    global.fetch = before;
  }
});

test('unitLabel distinguishes Excel sheets, Word blocks, and Text units from PDF print pages', () => {
  assert.equal(helper.unitLabel({ ext: '.pdf' }, 2, 5), 'Trang 2/5');
  assert.equal(helper.unitLabel({ ext: '.xlsx' }, 1, 3), 'Sheet 1/3');
  assert.equal(helper.unitLabel({ ext: '.docx' }, 1, 1), 'Khối Word 1/1');
  assert.equal(helper.unitLabel({ ext: '.txt' }, 1), 'Khối văn bản 1');
});

test('physicalContainerStats distinguishes 2 physical containers from 4 source records and flags seal mismatch', () => {
  const docs = [
    { id: 'd1', name: 'packing.txt' },
    { id: 'd2', name: 'bl.txt' },
  ];
  const records = [
    { kind: 'container', status: 'pending', document_id: 'd1', value: { container_number: 'MSCU1234567', seal_number: 'SEAL01', container_type: '20GP' } },
    { kind: 'container', status: 'pending', document_id: 'd1', value: { container_number: 'CSNU7654321', seal_number: 'SEAL02', container_type: '40HC' } },
    { kind: 'container', status: 'pending', document_id: 'd2', value: { container_number: 'MSCU1234567', seal_number: 'SEAL01', container_type: '20GP' } },
    { kind: 'container', status: 'pending', document_id: 'd2', value: { container_number: 'CSNU7654321', seal_number: 'WRONG02', container_type: '40HC' } },
  ];
  const stats = helper.physicalContainerStats(records, docs);
  assert.equal(stats.physicalCount, 2);
  assert.equal(stats.sourceRecordCount, 4);
  assert.equal(stats.groups.find((g) => g.container_number === 'MSCU1234567').hasConflict, false);
  assert.equal(stats.groups.find((g) => g.container_number === 'CSNU7654321').hasConflict, true);
});

test('Physical IDs ignore whitespace/case, retain unknown source count, and steps require current Reviewed export', () => {
  const stats = helper.physicalContainerStats([
    {kind:'container',status:'pending',value:{container_number:' mscu 1234567 '}},
    {kind:'container',status:'pending',value:{container_number:'MSCU1234567'}},
    {kind:'container',status:'pending',value:{container_number:''}},
  ]);
  assert.equal(stats.physicalCount, 1);
  assert.equal(stats.sourceRecordCount, 3);
  const bundle = {case:{id:'c1',revision:4,reviewed_at:'now',status:'Exported'},blockers:[],exports:[{mode:'Reviewed',case_revision:3}]};
  assert.equal(helper.computeStepStates(bundle)[7].done, false);
  bundle.exports.push({mode:'Reviewed',case_revision:4});
  assert.equal(helper.computeStepStates(bundle)[7].done, true);
  assert.deepEqual(helper.computeStepStates(bundle).map(s=>s.label), ['Tạo hồ sơ','Nạp chứng từ','Đọc & nhận diện','Xác minh trường','Đối chiếu chéo','Chuẩn bị bảng kê','Kiểm tra xuất file','Xuất Excel']);
  const markup=renderToStaticMarkup(React.createElement(components.StepTracker,{current:bundle}));
  assert.equal((markup.match(/<button/g)||[]).length,8);
  assert.ok(markup.includes('aria-label="Bước 5: Đối chiếu chéo"'));
});

test('Network and malformed validation failures use Vietnamese messages without dumping internals', async () => {
  const before=global.fetch;
  try {
    global.fetch=async()=>{throw new TypeError('Failed to fetch')};
    await assert.rejects(()=>helper.api('/health'), /Không kết nối được máy chủ/);
    global.fetch=async()=>({ok:false,status:422,json:async()=>({detail:[{loc:['body','note'],msg:'internal-secret-validator'}]})});
    await assert.rejects(()=>helper.api('/cases'), e=>e.message.includes('Thông tin nhập chưa hợp lệ')&&!e.message.includes('internal-secret'));
  } finally {global.fetch=before;}
});

test('Real UI components (HighlightedText, Badge, ContainerSummaryBanner, StepTracker) escape untrusted input and prevent Draft export false completion', () => {
  const escaped = renderToStaticMarkup(
    React.createElement(components.HighlightedText, {
      text: 'Invoice <script>steal()</script> 000123-A',
      query: '000123-A',
    })
  );
  assert.ok(escaped.includes('&lt;script&gt;steal()&lt;/script&gt;'));
  assert.ok(!escaped.includes('<script>'));
  assert.ok(escaped.includes('<mark>000123-A</mark>'));

  const draftCaseBundle = {
    case: { status: 'Needs verification', revision: 2, reviewed_at: null },
    documents: [{ id: 'd1', name: 'invoice.txt', status: 'read', type_verified: 0 }],
    records: [{ id: 'r1', kind: 'field', status: 'pending', value: { text: '000123-A' } }],
    checks: [{ key: 'classification:d1', result: 'Needs Verification', resolution: '' }],
    blockers: ['1 bản ghi chưa được xác minh'],
    exports: [{ id: 'e1', version: 1, mode: 'Draft', case_revision: 2 }],
  };
  const stepStates = helper.computeStepStates(draftCaseBundle);
  const step8 = stepStates.find((s) => s.index === 8);
  assert.equal(step8.done, false, 'Draft export must never mark Step 8 as done');
  assert.equal(step8.partial, true, 'Draft export shows partial/draft indicator');

  const stepMarkup = renderToStaticMarkup(
    React.createElement(components.StepTracker, { current: draftCaseBundle })
  );
  assert.ok(stepMarkup.includes('Mới xuất bản Draft'));

  const bannerMarkup = renderToStaticMarkup(
    React.createElement(components.ContainerSummaryBanner, {
      documents: [{ id: 'd1', name: 'packing.txt' }, { id: 'd2', name: 'bl.txt' }],
      records: [
        { kind: 'container', status: 'pending', document_id: 'd1', value: { container_number: 'MSCU1234567', seal_number: 'SEAL01' } },
        { kind: 'container', status: 'pending', document_id: 'd2', value: { container_number: 'MSCU1234567', seal_number: 'SEAL01' } },
      ],
    })
  );
  assert.ok(bannerMarkup.includes('1 container vật lý duy nhất · 2 bản ghi nguồn'));
});

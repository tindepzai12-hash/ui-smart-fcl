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

test('Extraction warnings show excluded attempts, matched rows are green, and untrusted text is escaped',async()=>{
  const moduleUrl=js=>'data:text/javascript;base64,'+Buffer.from(js).toString('base64');
  const resolveImports=js=>js.replace(/from ['"]react['"]/g,`from '${import.meta.resolve('react')}'`)
    .replace(/from ['"]lucide-react['"]/g,`from '${import.meta.resolve('lucide-react')}'`);
  const viewer=moduleUrl(resolveImports(compileTsx(fs.readFileSync('frontend/SourceImageViewer.tsx','utf8'))));
  const workbench=moduleUrl(resolveImports(compileTsx(fs.readFileSync('frontend/DiscrepancyWorkbench.tsx','utf8')))
    .replace("from './api'",`from '${moduleUrl(apiJs)}'`).replace("from './SourceImageViewer'",`from '${viewer}'`)
    .replace("from './review'",`from '${moduleUrl(compileTsx(fs.readFileSync('frontend/review.ts','utf8'),'review.ts'))}'`));
  const {DiscrepancyWorkbench,SourceCard}=await import(workbench);
  const loading=renderToStaticMarkup(React.createElement(SourceCard,{source:{id:'r1',document_id:'d1',document:'scan.pdf',page:2,value:{text:'1200'}},record:{id:'r1',document_id:'d1',page:2,value:{text:'1200'},raw:'1200',version:1}}));
  assert.ok(loading.includes('src="/api/documents/d1/preview/2"'));
  assert.ok(loading.includes('Đang đánh dấu vùng nguồn'));
  assert.ok(loading.includes('Kính lúp'));
  const render=issue=>renderToStaticMarkup(React.createElement(DiscrepancyWorkbench,{current:{records:[],consistency:{issues:[issue],gaps:[],matched:[],single_source:[],open_count:1,mismatch_count:0,ai_state:'completed'}},dict:{fields:{}},onDocuments:()=>{}}));
  const warning=render({key:'reading:doc',result:'Needs Verification',detail:{reason:'Thiếu bằng chứng',sources:[{id:'diagnostic:doc:1',document:'scan.pdf',page:2,diagnostic:true,field_label:'Tổng tiền',attempted_value:'<script>999</script>'}]}});
  assert.ok(warning.includes('Xem lỗi đọc &amp; bản gốc'));
  assert.ok(warning.includes('&lt;script&gt;999&lt;/script&gt; (đã loại)'));
  assert.ok(!warning.includes('<script>999'));
  const legacy=render({key:'reading:old',result:'Needs Verification',detail:{reason:'Cần đọc lại',sources:[{id:'doc',document:'old.pdf',value:{text:'old.pdf'}}]}});
  assert.ok(legacy.includes('Cảnh báo đọc tệp; xem chi tiết'));
  assert.ok(!legacy.includes('<strong>old.pdf</strong>'));
  const matched=render({key:'field:booking',result:'Matched',detail:{reason:'Khớp',sources:[]}});
  assert.ok(matched.includes('exception-row is-matched')&&matched.includes('badge good'));
  const uncertain=render({key:'field:gross_weight',result:'Needs Verification',detail:{reason:'Dấu phân cách chưa rõ',category:'difference',sources:[]}});
  assert.ok(!uncertain.includes('exception-row is-mismatch'));
  assert.ok(!uncertain.includes('Sai lệch / khác phạm vi'));
  assert.ok(uncertain.includes('badge warn'));
  const actualMismatch=render({key:'field:volume',result:'Mismatch',detail:{reason:'Hai ô nguồn khác nhau',sources:[]}});
  assert.ok(actualMismatch.includes('exception-row is-mismatch'));
  const stale=renderToStaticMarkup(React.createElement(DiscrepancyWorkbench,{current:{documents:[{needs_reprocess:true}],records:[],consistency:{issues:[],gaps:[],matched:[],single_source:[],open_count:0,mismatch_count:0,ai_state:'stale'}},dict:{fields:{}},onDocuments:()=>{}}));
  assert.ok(stale.includes('1 tài liệu cần đọc lại sau cập nhật.'));
  assert.ok(stale.includes('Mở chứng từ để đọc lại'));
});

test('Staff sees the precise save prerequisite; number formatting is an explicit suggestion only',async()=>{
  const js=compileTsx(fs.readFileSync('frontend/review.ts','utf8'),'review.ts');
  const {numberFormatSuggestion,reviewBlockReason,diagnosticBlockReason}=await import('data:text/javascript;base64,'+Buffer.from(js).toString('base64'));
  const ready={busy:false,saving:false,checked:true,note:'Đã đối chiếu bản gốc',unclear:false};
  assert.equal(reviewBlockReason(ready),'');
  assert.equal(reviewBlockReason({...ready,note:''}),'');
  assert.match(reviewBlockReason({...ready,checked:false}),/Đánh dấu/);
  assert.match(reviewBlockReason({...ready,unclear:true}),/từng nguồn/);
  assert.match(reviewBlockReason({...ready,busy:true}),/Chờ/);
  const attempted={kind:'field',draft:'BK-123',scope:'invoice',checked:true,hasSource:true,busy:false,saving:false};
  assert.equal(diagnosticBlockReason(attempted),'');
  assert.match(diagnosticBlockReason({...attempted,draft:'  '}),/không được để trống/);
  assert.match(diagnosticBlockReason({...attempted,checked:false}),/Tích/);
  assert.match(diagnosticBlockReason({...attempted,kind:'item',draft:{description:'Bolts',quantity:'10',unit:'PCS'}}),/đơn giá, thành tiền, tiền tệ/);
  assert.equal(diagnosticBlockReason({...attempted,kind:'item',scope:'packing',draft:{description:'Bolts',quantity:'10',unit:'PCS'}}),'');
  assert.equal(numberFormatSuggestion('19,560 KGS'),'19560 KGS');
  assert.equal(numberFormatSuggestion('16,200 KG'),'16200 KG');
  for(const v of ['19,56 KG','19.560 KG','19,560','19,560.00 KGS','Chưa đọc được'])assert.equal(numberFormatSuggestion(v),null);
});

test('Shipment flow focuses exceptions and allows an honest report without verifying every field',()=>{
  const current={case:{revision:2},documents:[{status:'read',type_verified:false}],records:[{status:'pending'}],
    consistency:{ai_state:'completed',open_count:1},exports:[]};
  let steps=helper.computeStepStates(current);
  assert.equal(steps.length,4);assert.equal(steps[1].done,true);
  assert.equal(steps[2].partial,true);assert.equal(steps[3].done,false);
  current.consistency.open_count=0;current.exports=[{case_revision:2,mode:'Draft'}];
  steps=helper.computeStepStates(current);
  assert.equal(steps[2].done,true);assert.equal(steps[3].done,true);
  current.consistency.ai_state='stale';
  assert.equal(helper.computeStepStates(current)[1].done,false);
});

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

test('Commercial profile has five steps and never treats Draft as completed review/export', () => {
  const current = {case:{id:'DEMO',requirements:{Booking:{required:true},Contract:{required:true}},revision:2},documents:[{status:'read',type_verified:true}],records:[{kind:'field',status:'verified'}],checks:[],blockers:[],exports:[{mode:'Draft',case_revision:2}]};
  const steps=helper.computeStepStates(current);
  assert.equal(steps.length,5);
  assert.deepEqual(steps.map(s=>s.tab),['documents','review','comparison','customs','export']);
  assert.equal(steps[4].done,false);
  assert.equal(steps[4].detail,'Đã xuất bản nháp');
  current.case.reviewed_at='2026-10-15';
  current.exports.push({mode:'Reviewed',case_revision:2});
  assert.equal(helper.computeStepStates(current)[4].done,true);
});

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
    global.fetch=async(url,options)=>{assert.ok(options.signal);throw new DOMException('timed out','TimeoutError')};
    await assert.rejects(()=>helper.api('/records/r1/source'),/Định vị nguồn quá thời gian chờ/);
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

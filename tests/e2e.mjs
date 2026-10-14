import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
const base=process.env.UI_SMART_URL||'http://127.0.0.1:8765';
let browser;
try {
 browser=await chromium.launch({channel:'msedge',headless:true});
} catch {
 browser=await chromium.launch({headless:true});
}
const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
const page=await context.newPage();const errors=[];const external=[];
page.on('pageerror',e=>errors.push(e.message));
await context.route('**/*',route=>{const url=route.request().url();if(url.startsWith(base)||url.startsWith('data:')||url.startsWith('blob:'))return route.continue();external.push(url);return route.abort()});
fs.mkdirSync('qa/screenshots',{recursive:true});
async function checkOverflow(name){const result=await page.evaluate(()=>({body:document.body.scrollWidth,width:innerWidth}));assert.ok(result.body<=result.width+1,name+' horizontal body overflow '+JSON.stringify(result))}
async function shot(name){await page.screenshot({path:'qa/screenshots/'+name+'.png',fullPage:true});await checkOverflow(name)}
let caseId='';
try{
 await page.goto(base);await page.getByRole('heading',{name:'Tổng quan hồ sơ',exact:true}).waitFor();await shot('overview-1440');
 await page.getByRole('button',{name:'Tạo hồ sơ',exact:true}).first().click();
 await page.getByLabel('Tên hồ sơ',{exact:true}).fill('QA · Bộ hồ sơ mẫu FCL');await page.getByLabel('Khách hàng (tùy chọn)').fill('Synthetic test company');await page.getByRole('dialog').getByRole('button',{name:'Tạo hồ sơ',exact:true}).click();
 await page.getByRole('heading',{name:'QA · Bộ hồ sơ mẫu FCL',exact:true}).waitFor();caseId=new URLSearchParams(await page.evaluate(()=>location.hash.replace('#',''))).get('case');assert.ok(caseId);
 await page.getByRole('button',{name:'Bộ mẫu sai lệch',exact:true}).click();
 await page.getByRole('button',{name:'Đọc & trích xuất',exact:true}).waitFor();await page.waitForFunction(()=>document.querySelectorAll('.document-item').length===3);
 await page.getByRole('button',{name:'Đọc & trích xuất',exact:true}).click();await page.getByText('Đã xử lý. Kiểm tra nguồn và xác minh từng giá trị.',{exact:true}).waitFor({timeout:30000});
 assert.equal(await page.locator('.field-card').count()>0,true);await shot('workspace-1440');
 await page.getByRole('button',{name:'Bước 4: Xác minh trường',exact:true}).focus();await page.keyboard.press('Enter');await page.getByRole('heading',{name:/bản ghi cần xác minh/}).waitFor();
 await page.getByRole('button',{name:'Bước 3: Đọc & nhận diện',exact:true}).focus();await page.keyboard.press('Space');await page.getByLabel('Tìm trường hoặc giá trị',{exact:true}).waitFor();
 await page.getByLabel('Tìm trường hoặc giá trị',{exact:true}).fill('Người mua');assert.equal(await page.locator('.fields-scroll .field-card').count(),1);
 const buyer=page.locator('.field-card').filter({has:page.getByRole('button',{name:'Người mua',exact:true})}).first();
 await page.route('**/api/records/*',async route=>{if(route.request().method()==='PATCH')await new Promise(resolve=>setTimeout(resolve,250));await route.continue()});
 await buyer.locator('input').fill('Công ty Kiểm thử UI');const verified=page.waitForResponse(r=>r.url().endsWith('/verify')&&r.request().method()==='POST');await buyer.getByRole('button',{name:'Xác minh',exact:true}).click();assert.equal((await verified).status(),200,'Immediate save+verify must use the new revision');
 await page.getByLabel('Tìm trường hoặc giá trị',{exact:true}).fill('');
 await page.reload();await page.getByRole('heading',{name:'QA · Bộ hồ sơ mẫu FCL',exact:true}).waitFor();assert.equal(await page.locator('.field-card').filter({has:page.getByRole('button',{name:'Người mua',exact:true})}).first().locator('input').inputValue(),'Công ty Kiểm thử UI');
 await page.getByRole('button',{name:/^Đối chiếu/}).click();await page.getByText('Sai lệch',{exact:true}).first().waitFor();await shot('comparison-1440');
 await page.getByRole('button',{name:'Xuất Excel',exact:true}).last().click();
 await page.getByLabel('Phiên bản',{exact:true}).selectOption('Reviewed');assert.equal(await page.getByRole('button',{name:'Xuất bản đã duyệt (.xlsx)',exact:true}).isDisabled(),true);
 await page.getByLabel('Phiên bản',{exact:true}).selectOption('Draft');
 const downloadEvent=page.waitForEvent('download');await page.getByRole('button',{name:'Xuất bản nháp (.xlsx)',exact:true}).click();const downloaded=await downloadEvent;await downloaded.saveAs('qa/e2e-draft.xlsx');assert.ok(fs.statSync('qa/e2e-draft.xlsx').size>5000);
 const step8Class=await page.locator('.steps > button').nth(7).getAttribute('class');assert.ok(step8Class?.includes('partial')&&!step8Class?.includes('done'),'Draft export must not mark step 8 as done');
 await shot('export-1440');
 await page.getByLabel('Tải template XLSX',{exact:true}).setInputFiles(path.resolve('samples/internal-template.xlsx'));
 await page.getByText('Template đã đọc',{exact:true}).waitFor();await page.getByRole('button',{name:'Thêm ô mapping',exact:true}).click();
 await page.getByLabel('Ô đích 1',{exact:true}).fill('B3');
 const option=await page.getByLabel('Nguồn mapping 1',{exact:true}).locator('option').filter({hasText:'invoice_number = 000123-A'}).first().getAttribute('value');assert.ok(option);
 await page.getByLabel('Nguồn mapping 1',{exact:true}).selectOption(option);
 const mappedDownload=page.waitForEvent('download');await page.getByRole('button',{name:'Xuất bản mapping nội bộ',exact:true}).click();await (await mappedDownload).saveAs('qa/e2e-mapped.xlsx');
 for(const width of [1366,1180,1179,768,390]){
  await page.setViewportSize({width,height:1000});await shot('export-'+width);
  await page.getByRole('button',{name:'Chứng từ',exact:true}).click();await shot('workspace-'+width);
  const direction=await page.locator('.workspace').evaluate(el=>getComputedStyle(el).display);
  assert.equal(direction,width>=1180?'grid':'flex','Pane layout switches at 1180px');
  await page.getByRole('button',{name:/^Đối chiếu/}).click();await shot('comparison-'+width);
  await page.getByRole('button',{name:'Chuẩn bị khai báo',exact:true}).click();await shot('customs-'+width);
  await page.getByRole('button',{name:'Xuất Excel',exact:true}).last().click();
 }
 await page.setViewportSize({width:1440,height:1000});
 // Finish the synthetic case through the real API, then exercise the UI review gate/download.
 const headers={'X-UI-Smart':'local'};
 const getBundle=async()=>await (await page.request.get(base+'/api/cases/'+caseId)).json();
 let b=await getBundle();
 for(const d of b.documents){const res=await page.request.patch(base+'/api/documents/'+d.id+'/classification',{headers,data:{type:d.type}});assert.equal(res.status(),200)}
 b=await getBundle();
 for(const r of b.records.filter(r=>r.status==='pending')){const res=await page.request.post(base+'/api/records/'+r.id+'/verify',{headers,data:{status:'verified',version:r.version,note:'Kiểm tra từng bản ghi trong bộ dữ liệu giả lập'}});assert.equal(res.status(),200)}
 b=await getBundle();
 for(const c of b.checks.filter(c=>['Mismatch','Needs Verification'].includes(c.result)&&!c.resolution)){const res=await page.request.post(base+'/api/checks/'+c.id+'/resolve',{headers,data:{note:'Bộ mẫu sai lệch có chủ đích; ghi nhận căn cứ xử lý cho kiểm thử'}});assert.equal(res.status(),200)}
 b=await getBundle();assert.deepEqual(b.blockers,[]);
 await page.reload();await page.getByRole('button',{name:'Bước 7: Kiểm tra xuất file',exact:true}).click();await page.getByRole('button',{name:'Hoàn thành kiểm tra',exact:true}).click();await page.getByText('Đã hoàn thành kiểm tra hồ sơ',{exact:true}).waitFor();
 await page.getByRole('button',{name:'Xuất Excel',exact:true}).last().click();
 const reviewedDownload=page.waitForEvent('download');await page.getByRole('button',{name:'Xuất bản đã duyệt (.xlsx)',exact:true}).click();await (await reviewedDownload).saveAs('qa/e2e-reviewed.xlsx');
 await page.waitForFunction(()=>document.querySelectorAll('.steps>button')[7].classList.contains('done'));await shot('reviewed-export-1440');
 await page.getByRole('button',{name:'Cài đặt',exact:true}).click();await page.getByRole('heading',{name:'Kết nối OpenAI',exact:true}).waitFor();await shot('settings-1440');
 await page.getByLabel('API key',{exact:true}).fill('synthetic-key-never-use');await page.getByRole('button',{name:'Lưu cấu hình',exact:true}).click();await page.getByText('Đã lưu cấu hình trong bộ nhớ phiên backend',{exact:true}).waitFor();assert.equal(await page.getByLabel('API key',{exact:true}).inputValue(),'');
 assert.equal(await page.evaluate(()=>localStorage.length),0);assert.equal(await page.evaluate(()=>sessionStorage.length),0);
 await page.getByRole('button',{name:'Xóa key',exact:true}).click();await page.getByText('Đã xóa key trong phiên backend',{exact:true}).waitFor();
 await page.getByRole('button',{name:'Hồ sơ logistics',exact:true}).click();await page.getByRole('button',{name:'Tạo hồ sơ',exact:true}).first().click();
 await page.getByLabel('Tên hồ sơ',{exact:true}).fill('Focus test');await page.keyboard.press('Escape');assert.equal(await page.getByRole('dialog').count(),0);
 assert.deepEqual(errors,[],'Browser runtime errors');assert.deepEqual(external,[],'Local flow attempted external request');
 fs.writeFileSync('qa/e2e-report.json',JSON.stringify({passed:true,caseId,viewports:[1440,1366,1180,1179,768,390],screens:['overview','workspace','comparison','export','customs','settings','reviewed-export'],checks:['sample loading','keyboard steps','field search','immediate edit+verify','draft gate','reviewed gate','1180px pane switch'],pageErrors:errors,externalRequests:external,draftBytes:fs.statSync('qa/e2e-draft.xlsx').size,reviewedBytes:fs.statSync('qa/e2e-reviewed.xlsx').size},null,2));
 console.log('E2E passed: create/upload/process/evidence/edit/reload/conflicts/export/key/keyboard/responsive; no external requests.');
}catch(error){await page.screenshot({path:'qa/screenshots/failure.png',fullPage:true});console.error(await page.locator('body').innerText());throw error;}finally{
 if(caseId)await page.request.delete(base+'/api/cases/'+caseId,{headers:{'X-UI-Smart':'local'}});
 await browser.close();
}

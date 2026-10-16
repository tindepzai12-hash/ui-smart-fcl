// Suggestions require an explicit staff action; they never save or verify data.
export function numberFormatSuggestion(value:string){
  const m=value.trim().match(/^(\d{1,3}(?:,\d{3})+)\s+([A-Za-z]{2,8})$/);
  return m?m[1].replaceAll(',','')+' '+m[2]:null;
}

export function reviewBlockReason({busy,saving,checked,note,unclear}:{busy:boolean,saving:boolean,checked:boolean,note:string,unclear:boolean}){
  if(saving)return 'Đang lưu kết quả kiểm tra…';
  if(busy)return 'Chờ tác vụ đang chạy hoàn tất.';
  if(unclear)return 'Còn ô chưa rõ định dạng. Sửa giá trị tại từng nguồn và bấm “Lưu & đối chiếu lại” trước.';
  if(!checked)return 'Đánh dấu đã đối chiếu các nguồn để xác nhận.';
  return '';
}

export function diagnosticBlockReason({kind,draft,scope,checked,hasSource,busy,saving}:any){
  if(saving)return 'Đang lưu kết quả kiểm tra…';
  if(busy)return 'Chờ tác vụ đang chạy hoàn tất.';
  if(!kind)return 'Đọc lại bằng OpenAI để lấy các ô dữ liệu có thể xác nhận.';
  if(!hasSource)return 'Chờ bản gốc tải xong trước khi xác nhận.';
  if(kind==='field'&&!String(draft||'').trim())return 'Nhập giá trị đã đọc trên bản gốc. Ô này không được để trống dù đã tích kiểm tra.';
  if(kind==='item'){
    const required=scope==='invoice'?['description','quantity','unit','unit_price','line_amount','currency']:['description','quantity','unit'];
    const titles:any={description:'mô tả hàng',quantity:'số lượng',unit:'đơn vị',unit_price:'đơn giá',line_amount:'thành tiền',currency:'tiền tệ'};
    const missing=required.filter(k=>!String(draft?.[k]??'').trim());
    if(missing.length)return 'Nhập đủ '+missing.map(k=>titles[k]).join(', ')+' từ bản gốc trước khi lưu.';
  }
  if(!checked)return 'Tích đã kiểm tra bản gốc để bật nút lưu.';
  return '';
}

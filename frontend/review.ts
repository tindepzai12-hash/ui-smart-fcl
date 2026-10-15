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

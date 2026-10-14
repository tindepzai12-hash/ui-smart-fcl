"""Generate an offline help page from the shipped guide's own text."""
import re,html
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=(root/'frontend/UserGuide.tsx').read_text(encoding='utf-8')
steps=re.findall(r"\['([^']+)','([^']+)'\]",source)
assert len(steps)==8
problems=re.findall(r'<dt>(.*?)</dt><dd>(.*?)</dd>',source)
intro='Hướng dẫn cho nhân viên chứng từ của FWD xử lý hồ sơ nhập khẩu FCL đường biển. Làm lần lượt từ tải chứng từ đến kiểm tra nguồn và xuất bảng kê. AI hỗ trợ đọc, nhân viên xác minh cuối cùng.'
body='<h1>Hướng dẫn sử dụng U&amp;I SMART</h1><p>'+intro+'</p><ol>'
for title,text in steps:body+=f'<li><h2>{html.escape(title)}</h2><p>{html.escape(text)}</p></li>'
body+='</ol><h2>Khi có vấn đề</h2><dl>'
for title,text in problems:body+=f'<dt>{html.escape(title)}</dt><dd>{html.escape(text)}</dd>'
body+='</dl><p>Không tự kết luận mã HS, thuế, giấy phép hoặc điều kiện ưu đãi C/O. Phiên bản hướng dẫn ngày 15 tháng 10 năm 2026.</p>'
document='<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hướng dẫn sử dụng U&amp;I SMART</title><style>body{font:16px/1.75 Arial,sans-serif;color:#172033;max-width:820px;margin:32px auto;padding:0 24px}h1{font-size:28px}h2{font-size:19px;margin:24px 0 6px}li{padding-left:6px;margin:24px 0}dt{font-weight:bold;margin-top:20px}dd{margin:6px 0}p{margin:8px 0}@media print{body{font-size:11pt;margin:0;max-width:none}li{break-inside:avoid}}</style><main>'+body+'</main></html>'
public=root/'public';public.mkdir(exist_ok=True)
(public/'huong-dan.html').write_text(document,encoding='utf-8')
out=root.parent/'output';out.mkdir(exist_ok=True)
(out/'HUONG_DAN_UI_SMART.html').write_text(document,encoding='utf-8')
md='# Hướng dẫn sử dụng U&I SMART\n\n'+intro+'\n\n'
for i,(title,text) in enumerate(steps,1):md+=f'## {i} {title}\n\n{text}\n\n'
for title,text in problems:md+=f'## {title}\n\n{text}\n\n'
(root/'docs/USER_GUIDE.md').write_text(md,encoding='utf-8')
print('Generated guide: 8 steps and 4 troubleshooting entries.')

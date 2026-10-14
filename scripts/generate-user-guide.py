"""Generate the printable/offline guide from the same content used in the app."""
import json,html
from pathlib import Path
root=Path(__file__).resolve().parents[1]
g=json.loads((root/'frontend/guide-content.json').read_text(encoding='utf-8'))
esc=html.escape
title='Hướng dẫn nhân viên xử lý hồ sơ U&I SMART'
body=f'<h1>{title}</h1><p>{esc(g["intro"])}</p><p>{esc(g["scope"])}</p>'
md=f'# {title}\n\n{g["intro"]}\n\n{g["scope"]}\n\n'
s=g['scenario']
body+=f'<section><h2>{esc(s["title"])}</h2><p>{esc(s["notice"])}</p><dl>'
md+=f'## {s["title"]}\n\n{s["notice"]}\n\n'
for label,value in s['facts']:
    body+=f'<dt>{esc(label)}</dt><dd>{esc(value)}</dd>'
    md+=f'- **{label}:** {value}\n'
body+='</dl></section><nav aria-label="Các bước xử lý hồ sơ"><h2>Nhân viên làm theo thứ tự</h2><ol>'
for i,s in enumerate(g['steps'],1):body+=f'<li><a href="#guide-{esc(s["id"])}">Bước {i}: {esc(s["title"])}</a></li>'
body+='</ol></nav>'
labels=[('task','Việc nhân viên làm'),('action','Thao tác trên web'),('check','Kiểm tra trong ví dụ sầu riêng'),('done','Khi nào chuyển bước?'),('problem','Nếu chưa đạt')]
for i,s in enumerate(g['steps'],1):
    body+=f'<section id="guide-{esc(s["id"])}"><h2>Bước {i}. {esc(s["title"])}</h2><dl>'
    md+=f'\n\n## Bước {i}. {s["title"]}\n\n'
    for key,label in labels:
        body+=f'<dt>{label}</dt><dd>{esc(s[key])}</dd>'
        md+=f'**{label}:** {s[key]}\n\n'
    body+='</dl></section>'
body+='<section><h2>Ba tình huống để biết phải xử lý thế nào</h2><dl>'
md+='## Ba tình huống để biết phải xử lý thế nào\n\n'
for s in g['examples']:
    body+=f'<dt>{esc(s["title"])}</dt><dd>{esc(s["action"])}</dd>'
    md+=f'### {s["title"]}\n\n{s["action"]}\n\n'
body+='</dl></section><section><h2>Phần việc thực hiện bên ngoài U&I SMART</h2><ul>'
md+='## Phần việc thực hiện bên ngoài U&I SMART\n\n'
for text in g['external']:
    body+=f'<li>{esc(text)}</li>';md+=f'- {text}\n'
source=g['source']
body+=f'</ul><p>{esc(g["limitation"])}</p><p>Nguồn nghiệp vụ: <a href="{esc(source["url"],quote=True)}">{esc(source["title"])}</a>. {esc(source["note"])}</p></section>'
md+=f'\n{g["limitation"]}\n\nNguồn: [{source["title"]}]({source["url"]}). {source["note"]}\n\n'
body+='<section><h2>Khi gặp vấn đề với web</h2><dl>';md+='## Khi gặp vấn đề với web\n\n'
for title,text in g['problems']:
    body+=f'<dt>{esc(title)}</dt><dd>{esc(text)}</dd>';md+=f'### {title}\n\n{text}\n\n'
body+='</dl></section>'
document='<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hướng dẫn nhân viên — U&amp;I SMART</title><style>body{font:16px/1.75 Arial,sans-serif;color:#172033;max-width:820px;margin:32px auto;padding:0 24px}h1{font-size:28px}h2{font-size:21px;margin:24px 0 8px}section,nav{padding:16px 0;border-bottom:1px solid #d9e1ea;scroll-margin-top:16px}dt{font-weight:bold;margin-top:18px}dd{margin:6px 0}li{margin:10px 0}a{color:#174ea6;overflow-wrap:anywhere}p{margin:8px 0}@media print{body{font-size:11pt;margin:0;max-width:none}nav{display:none}dt,h2{break-after:avoid}dd{break-inside:avoid}}</style><main>'+body+'</main></html>'
(root/'public/huong-dan.html').write_text(document,encoding='utf-8')
out=root.parent/'output';out.mkdir(exist_ok=True)
(out/'HUONG_DAN_UI_SMART.html').write_text(document,encoding='utf-8')
(root/'docs/USER_GUIDE.md').write_text(md,encoding='utf-8')
print('Generated staff guide: 8 steps, durian scenario, 3 worked examples and external responsibilities.')

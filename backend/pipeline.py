"""Content-addressed pipeline identity and safe, source-free trace fingerprints."""
import hashlib
import json
import os
import platform
import subprocess
from functools import lru_cache
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

@lru_cache(maxsize=4)
def manifest(scope='extraction'):
    names = ['reader', 'extraction', 'normalize', 'validation', 'dictionary', 'ai', 'ai_guidance', 'pipeline']
    if scope == 'reader':
        names = ['reader', 'extraction', 'pipeline']
    if scope == 'review':
        names += ['consistency']
    files = {name: hashlib.sha256((ROOT/'backend'/f'{name}.py').read_bytes()).hexdigest() for name in names}
    packages = {}
    for name in ['PyMuPDF', 'pypdf', 'pdfplumber', 'pypdfium2', 'Pillow', 'pytesseract', 'python-docx', 'openpyxl', 'xlrd', 'pydantic', 'openai']:
        try: packages[name] = version(name)
        except PackageNotFoundError: packages[name] = None
    from . import reader
    status = reader.ocr_status()
    ocr = {'ready': status['ready'], 'languages': sorted(status['languages']), 'version': None, 'data': {}}
    if status['ready']:
        try:
            result = subprocess.run([status['cmd'], '--version'], capture_output=True, text=True, timeout=8,
                                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            ocr['version'] = result.stdout.splitlines()[0] if result.stdout else None
        except (OSError, subprocess.SubprocessError): pass
        directory = Path(os.environ.get('TESSDATA_PREFIX') or Path(status['cmd']).parent/'tessdata')
        for language in ['eng', 'vie']:
            path = directory/(language+'.traineddata')
            if path.is_file(): ocr['data'][language] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {'files': files, 'packages': packages, 'python': platform.python_version(), 'os': platform.system(), 'ocr': ocr}

def fingerprint(scope='extraction'):
    return digest(manifest(scope))

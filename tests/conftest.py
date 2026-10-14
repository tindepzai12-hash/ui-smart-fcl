import os,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'vendor'),str(ROOT)]
tempfile.tempdir=str(ROOT/'tmp')
Path(tempfile.tempdir).mkdir(exist_ok=True)
os.environ['UI_SMART_DATA']=tempfile.mkdtemp(prefix='ui-smart-tests-')
os.environ.pop('OPENAI_API_KEY',None)

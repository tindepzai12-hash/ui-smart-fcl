import os,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'vendor'),str(ROOT)]
tempfile.tempdir=os.getenv('UI_SMART_TEST_TMP',str(ROOT/'tmp'))
Path(tempfile.tempdir).mkdir(parents=True,exist_ok=True)
os.environ['UI_SMART_DATA']=tempfile.mkdtemp(prefix='ui-smart-tests-')
os.environ.pop('OPENAI_API_KEY',None)

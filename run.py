"""Launch from any Python interpreter after setup. Vendor belongs to this project."""
import sys
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'vendor'))
sys.path.insert(0,str(root))
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);args=parser.parse_args()
    import uvicorn
    uvicorn.run('backend.app:app',host='127.0.0.1',port=args.port,log_level='warning',access_log=False)

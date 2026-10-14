import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path[:0]=[str(root/'vendor'),str(root/'tests')]
from fixtures import generate
generate(root/'samples')
print('Synthetic fixtures generated in samples/')

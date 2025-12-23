import sys
from pathlib import Path

# Add src directory to sys.path
src_path = Path(__file__).resolve().parents[1] / 'src'
sys.path.append(str(src_path))

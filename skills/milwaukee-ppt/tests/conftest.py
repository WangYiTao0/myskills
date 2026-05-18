"""pytest fixtures shared across milwaukee-ppt tests."""
from pathlib import Path
import sys

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

"""Unit tests initialization."""

import pytest
import sys
from pathlib import Path

# Add the source directory to the path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

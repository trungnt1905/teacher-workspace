import sys
from pathlib import Path

import pytest

PYTHON_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"

sys.path.insert(0, str(PYTHON_ROOT))


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES

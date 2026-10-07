import os
import tempfile
from pathlib import Path

import pytest

_tmp_dir = tempfile.mkdtemp(prefix="vishwasedge_test_")
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{_tmp_dir}/test.db")
os.environ.setdefault("CHROMA_PERSIST_DIR", f"{_tmp_dir}/chroma")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-only")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEFAULT_ADMIN_USERNAME", "operator")
os.environ.setdefault("DEFAULT_ADMIN_PASSWORD", "changeme123")
os.environ.setdefault("DEFAULT_API_KEY", "dev-local-api-key")


@pytest.fixture(autouse=True, scope="session")
def _test_data_dirs():
    Path(_tmp_dir).mkdir(parents=True, exist_ok=True)
    yield

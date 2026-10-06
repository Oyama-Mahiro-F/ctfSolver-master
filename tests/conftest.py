"""测试公共配置。

关于临时目录（Windows 受限环境下的坑，务必保留这段说明）：

1. 临时目录固定在仓库内（`.pytest-tmp/`），不使用系统 TEMP ——
   受限环境下系统 TEMP 里无法创建文件，sqlite 会直接报
   "unable to open database file"。
2. 目录一律用默认权限创建，绝不使用 `tempfile.mkdtemp()` 或
   `os.mkdir(path, 0o700)`：在本机的受限运行环境中，以 0o700 创建的目录
   随后连 `chmod` 都会被拒绝，目录内无法写入任何文件。
   这也是这里要覆盖 pytest 自带 `tmp_path_factory` 的原因（上游硬编码 0o700）。
"""
import atexit
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT_DIR = os.path.join(REPO_ROOT, "agent")
BACKEND_DIR = os.path.join(REPO_ROOT, "server", "backend")

TEST_TMP_ROOT = os.path.join(REPO_ROOT, ".pytest-tmp")


def _safe_mkdtemp(suffix=None, prefix=None, dir=None):
    """`tempfile.mkdtemp` 的安全替代：一律用默认权限建目录。

    标准库的 mkdtemp 会调用 `os.mkdir(path, 0o700)`，而在本机的受限运行环境中，
    以 0o700 建出来的目录随后既不能写入、也不能 chmod、连 ACL 都读不到 ——
    sqlite、pytest 的缓存目录、测试里起 HTTP 服务的组件都会直接失败。
    这里只改创建方式，并把默认位置收敛到仓库内。
    """
    suffix = suffix or ""
    prefix = prefix or "tmp"
    base = dir or TEST_TMP_ROOT
    os.makedirs(base, exist_ok=True)
    for _ in range(100):
        path = os.path.join(base, prefix + uuid.uuid4().hex[:8] + suffix)
        try:
            os.mkdir(path)
        except FileExistsError:  # pragma: no cover - 碰撞概率极低
            continue
        return path
    raise FileExistsError(f"无法在 {base} 下创建唯一临时目录")


tempfile.mkdtemp = _safe_mkdtemp


def make_test_dir(prefix: str = "tmp-") -> str:
    """在仓库内创建一个默认可写的临时目录，返回其绝对路径。"""
    return tempfile.mkdtemp(prefix=prefix)


class _RepoPathFactory:
    """pytest `tmp_path_factory` 的替代实现：只创建默认权限的目录。"""

    _retention_policy = "all"

    def __init__(self) -> None:
        self._basetemp: Path | None = None

    def getbasetemp(self) -> Path:
        if self._basetemp is None:
            self._basetemp = Path(make_test_dir("basetemp-"))
        return self._basetemp

    def mktemp(self, basename: str, numbered: bool = True) -> Path:
        return Path(make_test_dir(f"{basename}-"))


@atexit.register
def _cleanup_test_tmp_root() -> None:  # pragma: no cover - 进程退出时执行
    shutil.rmtree(TEST_TMP_ROOT, ignore_errors=True)


@pytest.fixture(scope="session")
def tmp_path_factory() -> _RepoPathFactory:
    return _RepoPathFactory()


@pytest.fixture
def repo_tmpdir() -> str:
    """替身 `tmp_path`：同样每个用例一个独立目录，但权限安全。"""
    return make_test_dir("case-")


@pytest.fixture(scope="session")
def agent_path():
    """把 agent/ 放到 sys.path，使 `config` / `utils` / `agents` / `addons` 可导入。"""
    if AGENT_DIR not in sys.path:
        sys.path.insert(0, AGENT_DIR)
    return AGENT_DIR


@pytest.fixture(scope="session")
def backend_client():
    """使用临时 SQLite 库启动 Flask 测试客户端，不触碰仓库自带的数据库。"""
    tmpdir = make_test_dir("backend-")
    # SQLAlchemy 的 SQLite URI 只接受正斜杠：Windows 上写成 sqlite:///C:\... 会被
    # 当成相对路径，直接报 "unable to open database file"。
    db_path = os.path.join(tmpdir, "test.db").replace("\\", "/")
    os.environ["CTF_DATABASE_URI"] = "sqlite:///" + db_path

    if BACKEND_DIR not in sys.path:
        sys.path.insert(0, BACKEND_DIR)

    import app as backend_app

    backend_app.app.config["TESTING"] = True
    with backend_app.app.test_client() as client:
        yield client

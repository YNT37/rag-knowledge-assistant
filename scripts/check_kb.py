"""在源码副本和临时数据中运行知识库回归，不读取开发 .env。"""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ISOLATION_PLUGIN = r'''
import importlib.abc
import os
from pathlib import Path
import socket
import sqlite3
import sys

ROOT = Path(__file__).resolve().parent

def blocked(*args, **kwargs):
    raise AssertionError("隔离回归禁止真实模型、MySQL或外部网络调用")

class BlockModels(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"torch", "sentence_transformers", "transformers"}:
            blocked()

sys.meta_path.insert(0, BlockModels())

import dotenv
dotenv.load_dotenv = lambda *args, **kwargs: False
import pymysql.connections
pymysql.connections.Connection.connect = blocked

def network_guard(event, args):
    if event == "socket.connect":
        address = args[1]
        # Windows asyncio的socketpair通过本机临时端口实现；不开放服务端口。
        if (isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}
                and address[1] not in {3306, 8000, 5173, 6333, 6334}):
            return
        blocked()
    if event == "socket.getaddrinfo":
        if args[0] not in {None, "127.0.0.1", "::1", "localhost"}:
            blocked()

sys.addaudithook(network_guard)

original_sqlite_connect = sqlite3.connect
def isolated_sqlite_connect(database, *args, **kwargs):
    if str(database) != ":memory:":
        resolved = Path(database).resolve()
        if not resolved.is_relative_to(ROOT):
            raise AssertionError("SQLite文件必须位于本次隔离目录")
    return original_sqlite_connect(database, *args, **kwargs)
sqlite3.connect = isolated_sqlite_connect

from app.services import llm_service
llm_service.ask_llm = blocked
llm_service.ask_chat = blocked
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, help="可选的JUnit报告保存目录")
    arguments = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    report_dir = arguments.report_dir.resolve() if arguments.report_dir else None
    if report_dir:
        report_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="knowledge-base-check-") as temporary:
        snapshot = Path(temporary).resolve()
        for package in ("app", "tests"):
            for source in (project / package).rglob("*.py"):
                if "__pycache__" in source.parts:
                    continue
                destination = snapshot / source.relative_to(project)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
        for relative in ("main.py", "practice/rag_document_practice.py", "practice/__init__.py"):
            source = project / relative
            if source.is_file():
                destination = snapshot / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)

        (snapshot / "documents").mkdir()
        (snapshot / "conftest.py").write_text(ISOLATION_PLUGIN, encoding="utf-8")
        environment = os.environ.copy()
        for key in list(environment):
            if key.startswith(("DB_", "LLM_", "RAG_", "KB_", "EMBEDDING_")):
                del environment[key]
        environment.update({
            "DB_USER": "isolated_test",
            "DB_PASSWORD": "isolated_test_only",
            "DB_HOST": "127.0.0.1",
            "DB_PORT": "1",
            "DB_NAME": "isolated_test",
            "LLM_API_KEY": "isolated_test_only",
            "LLM_BASE_URL": "https://example.invalid",
            "LLM_MODEL": "isolated_test",
            "EMBEDDING_MODEL_PATH": str(snapshot / "nonexistent-model"),
            "KB_DOCUMENTS_DIR": str(snapshot / "documents"),
            "PYTHON_DOTENV_DISABLED": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "PYTHONPATH": str(snapshot),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "TMP": str(snapshot),
            "TEMP": str(snapshot),
        })
        command = [
            sys.executable, "-B", "-m", "pytest",
            "tests/test_kb_p0.py", "tests/test_main.py", "tests/test_cloud_embedding.py", "-q",
            "--rootdir", str(snapshot), "--confcutdir", str(snapshot),
            "--basetemp", str(snapshot / "pytest-temp"),
        ]
        if report_dir:
            command.append(f"--junitxml={report_dir / 'pytest-results.xml'}")
        print("Running isolated tests: development .env/data excluded; MySQL/models/network blocked.", flush=True)
        return subprocess.run(command, cwd=snapshot, env=environment, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())

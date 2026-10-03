from __future__ import annotations

from pathlib import Path

import pytest

from repowise.core.analysis.dead_code import DeadCodeAnalyzer, DeadCodeKind
from tests.unit.dead_code._helpers import _build_graph


def _unused_file() -> dict:
    return {
        "is_entry_point": False,
        "is_test": False,
        "is_api_contract": False,
        "symbol_count": 1,
        "symbols": [
            {
                "name": "unused_helper",
                "kind": "function",
                "visibility": "public",
                "decorators": [],
                "start_line": 1,
                "end_line": 2,
                "language": "python",
            }
        ],
    }


@pytest.mark.parametrize(
    "path",
    ["docs/examples/demo.py", "docs_src/tutorial/demo.py", "examples/demo.py"],
)
def test_docs_examples_not_reported_without_repo_root(path: str):
    graph = _build_graph({path: _unused_file(), "pkg/orphan.py": _unused_file()})

    report = DeadCodeAnalyzer(graph).analyze(
        {"min_confidence": 0.0, "detect_zombie_packages": False}
    )

    assert all(f.file_path != path for f in report.findings)
    assert {f.kind for f in report.findings if f.file_path == "pkg/orphan.py"} == {
        DeadCodeKind.UNREACHABLE_FILE,
        DeadCodeKind.UNUSED_EXPORT,
    }


def test_config_backed_docs_project_not_reported(tmp_path: Path):
    writerside = tmp_path / "documentation-website" / "Writerside"
    writerside.mkdir(parents=True)
    (writerside / "writerside.cfg").write_text(
        '<ihp version="2.0"><topics dir="topics"/></ihp>', encoding="utf-8"
    )
    path = "documentation-website/Writerside/snippets/demo/src/sample.py"
    graph = _build_graph({path: _unused_file(), "pkg/orphan.py": _unused_file()})

    report = DeadCodeAnalyzer(graph, repo_root=tmp_path).analyze(
        {"min_confidence": 0.0, "detect_zombie_packages": False}
    )

    assert all(f.file_path != path for f in report.findings)
    assert {f.kind for f in report.findings if f.file_path == "pkg/orphan.py"} == {
        DeadCodeKind.UNREACHABLE_FILE,
        DeadCodeKind.UNUSED_EXPORT,
    }


@pytest.mark.parametrize(
    "path",
    [
        "src/pkg/examples/service.py",
        "src/doc/service.py",
        "documentation-website/src/service.py",
        "docs-api/src/service.py",
    ],
)
def test_production_code_with_docs_or_examples_name_still_reported(path: str, tmp_path: Path):
    graph = _build_graph({path: _unused_file()})

    report = DeadCodeAnalyzer(graph, repo_root=tmp_path).analyze(
        {"min_confidence": 0.0, "detect_zombie_packages": False}
    )

    assert {f.kind for f in report.findings if f.file_path == path} == {
        DeadCodeKind.UNREACHABLE_FILE,
        DeadCodeKind.UNUSED_EXPORT,
    }

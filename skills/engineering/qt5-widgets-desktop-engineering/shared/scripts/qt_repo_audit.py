#!/usr/bin/env python3
"""Audit a local Qt/C++ repository for Qt5 Widgets desktop-tool maturity signals.

Usage:
    python qt_repo_audit.py /path/to/repo
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List


EXCLUDED_DIRS = {
    ".git",
    "build",
    "cmake-build-debug",
    "cmake-build-release",
    "cmake-build-relwithdebinfo",
    "out",
    "dist",
    "bin",
}


def has_any(root: Path, names: List[str]) -> bool:
    return any((root / name).exists() for name in names)


def read_small_text(path: Path) -> str:
    try:
        if path.is_file() and path.stat().st_size <= 1_000_000:
            return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    return ""


def walk_files(root: Path, limit: int = 4000) -> List[Path]:
    files: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for name in filenames:
            files.append(Path(dirpath) / name)
            if len(files) >= limit:
                return files
    return files


def detect_qt_version(text: str) -> str:
    lowered = text.lower()
    if "find_package(qt6" in lowered or re.search(r"\bqt6\b", lowered):
        return "Qt6"
    if "find_package(qt5" in lowered or re.search(r"\bqt5\b", lowered):
        if "5.12" in lowered:
            return "Qt5.12-signaled"
        return "Qt5"
    if "greaterthan(qt_major_version, 4)" in lowered or "qt += widgets" in lowered:
        return "Qt5-likely"
    return "unknown"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python qt_repo_audit.py /path/to/repo", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    if not root.exists() or not root.is_dir():
        print(json.dumps({"error": f"Repository path not found: {root}"}, indent=2, ensure_ascii=False))
        return 1

    files = walk_files(root)
    names = {p.name for p in files}
    rels = {str(p.relative_to(root)).replace('\\', '/') for p in files}

    top_level_dirs = sorted([p.name for p in root.iterdir() if p.is_dir()])
    top_level_files = sorted([p.name for p in root.iterdir() if p.is_file()])

    cmake_text = "\n".join(read_small_text(p) for p in files if p.name == "CMakeLists.txt")
    pro_text = "\n".join(read_small_text(p) for p in files if p.suffix == ".pro")
    pri_text = "\n".join(read_small_text(p) for p in files if p.suffix == ".pri")
    build_text = "\n".join([cmake_text, pro_text, pri_text])

    qml_present = any(p.suffix.lower() == ".qml" for p in files)
    ui_forms_present = any(p.suffix.lower() == ".ui" for p in files)
    qrc_present = any(p.suffix.lower() == ".qrc" for p in files)
    widget_module_signal = "widgets" in build_text.lower() or ui_forms_present
    model_signals = any("QAbstractItemModel" in read_small_text(p) for p in files if p.suffix.lower() in {".h", ".hpp", ".cpp", ".cc"})
    qtablewidget_heavy = sum("QTableWidget" in read_small_text(p) for p in files if p.suffix.lower() in {".h", ".hpp", ".cpp", ".cc"})
    qtreewidget_heavy = sum("QTreeWidget" in read_small_text(p) for p in files if p.suffix.lower() in {".h", ".hpp", ".cpp", ".cc"})
    mainwindow_present = any(p.name.lower() in {"mainwindow.h", "mainwindow.cpp", "mainwindow.ui"} for p in files)
    qsettings_present = any("QSettings" in read_small_text(p) for p in files if p.suffix.lower() in {".h", ".hpp", ".cpp", ".cc"})
    qthread_present = any("QThread" in read_small_text(p) for p in files if p.suffix.lower() in {".h", ".hpp", ".cpp", ".cc"})
    process_or_network_present = any(
        any(token in read_small_text(p) for token in ["QProcess", "QNetworkAccessManager", "QFile", "QSaveFile"])
        for p in files if p.suffix.lower() in {".h", ".hpp", ".cpp", ".cc"}
    )

    build_system = "CMake" if cmake_text else ("qmake" if pro_text or pri_text else "unknown")
    qt_version = detect_qt_version(build_text)

    findings: Dict[str, object] = {
        "repository": str(root),
        "build_system": build_system,
        "qt_version_signal": qt_version,
        "widgets_signals_present": widget_module_signal,
        "qml_present": qml_present,
        "ui_forms_present": ui_forms_present,
        "mainwindow_present": mainwindow_present,
        "model_view_signals_present": model_signals,
        "qsettings_present": qsettings_present,
        "threading_signals_present": qthread_present,
        "process_or_network_signals_present": process_or_network_present,
        "top_level_dirs": top_level_dirs,
        "top_level_files": top_level_files,
        "maturity_signals": {
            "src": "src" in top_level_dirs,
            "tests": has_any(root, ["tests", "test"]),
            "docs": has_any(root, ["docs", "doc"]),
            "packaging": has_any(root, ["packaging", "installer", "deploy", "dist"]),
            "scripts": "scripts" in top_level_dirs,
            "cmake_dir": "cmake" in top_level_dirs,
            "resources_qrc": qrc_present,
            "ci": has_any(root, [".github", ".gitlab-ci.yml", "appveyor.yml", ".azure-pipelines"]),
            "formatting_config": any(name in names for name in {".clang-format", ".editorconfig"}),
        },
        "risks": [],
        "recommendations": [],
    }

    risks: List[str] = []
    recs: List[str] = []

    if build_system == "unknown":
        risks.append("No obvious CMake or qmake entry point was found.")
        recs.append("Add an explicit build entry point. For Qt 5.12 repositories, qmake is acceptable in legacy code and CMake is preferred for new modules.")

    if qt_version == "Qt6":
        recs.append("This repository signals Qt6. If you use this skill against it, explicitly switch off the default Qt 5.12 assumptions.")
    elif qt_version == "unknown":
        risks.append("No explicit Qt version signal was detected. Verify that recommendations remain Qt 5.12 compatible.")

    ms = findings["maturity_signals"]
    assert isinstance(ms, dict)

    if not ms["src"]:
        risks.append("No top-level src directory detected; source layout may be ad hoc.")
        recs.append("Create a stable source root such as src/ and split UI, core services, and models deliberately.")
    if not ms["tests"]:
        risks.append("No tests directory detected.")
        recs.append("Add tests for service logic and model/view behavior before attempting large UI refactors.")
    if not ms["docs"]:
        recs.append("Add docs/ for build instructions, deployment notes, and architectural boundaries.")
    if qml_present and widget_module_signal:
        recs.append("The repository mixes Widgets and QML. Make the boundary explicit rather than letting presentation and business logic drift across both stacks.")
    if widget_module_signal and not model_signals and (qtablewidget_heavy > 0 or qtreewidget_heavy > 0):
        risks.append("Widget-item classes appear present without model/view signals. Complex data screens may be storing state directly in widgets.")
        recs.append("For operational tables and trees, consider migrating toward QAbstractItemModel plus proxy models and delegates.")
    if process_or_network_present and not qthread_present:
        recs.append("The codebase appears to do filesystem, process, or network work. Verify that these paths do not block the GUI thread.")
    if not qsettings_present and mainwindow_present:
        recs.append("Consider QSettings for geometry, window state, recent files, and user preferences.")
    if not ms["resources_qrc"]:
        recs.append("Consider a .qrc file for icons, translations, and bundled UI assets.")
    if not ms["packaging"]:
        recs.append("If this is a user-facing desktop tool, add packaging or deployment scripts. On Windows, verify a clean-machine run with windeployqt.")

    findings["risks"] = risks
    findings["recommendations"] = recs
    print(json.dumps(findings, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Calibre-Web Automated – fork of Calibre-Web
# Copyright (C) 2018-2026 Calibre-Web contributors
# Copyright (C) 2024-2026 Calibre-Web Automated contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# See CONTRIBUTORS for full list of authors.

"""Regression pins for cover/metadata enforcement on unsupported formats."""

import ast
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "cover_enforcer.py"


def _method_source(name: str) -> str:
    source = SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    pytest.fail(f"{name} not found in cover_enforcer.py")


@pytest.mark.unit
def test_unsupported_format_writes_opf_and_reports_embedding_skip():
    """PDF-only books still get their format-independent OPF backup."""
    helper = _method_source("_write_metadata_backup_for_unsupported")
    assert "replace_old_metadata" in helper
    assert "metadata.opf updated" in helper
    assert "INFO" in helper
    assert "embedding" in helper.lower()

    enforce_cover = _method_source("enforce_cover")
    assert "_write_metadata_backup_for_unsupported" in enforce_cover
    assert "record_failed_enforcement" not in enforce_cover

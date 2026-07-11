# -*- coding: utf-8 -*-
# Calibre-Web Automated – fork of Calibre-Web
# Copyright (C) 2024-2026 Calibre-Web-NextGen contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Source-pin tests for the new-UI "Refresh library" button (#780 / #665).

The redesigned SPA shipped without any equivalent of the classic header's
"Refresh Library" action, so users who drop new files into the ingest folder
had no way to trigger a manual re-scan from the new UI (a duplicate cluster:
#780 and #665 both report the same missing action).

The backend contract already existed (cps/cwa_functions.py):
  POST /cwa-library-refresh        -> starts a background scan, 200 {message}
  GET  /cwa-library-refresh/messages -> {messages:[...]} (poll until non-empty)

These tests pin that the library page wires a RefreshCw button to those routes,
polls the messages endpoint, clears the poll interval (no leaked timer / stray
invalidate after unmount), exposes the action to screen readers, and keeps the
new msgid anchored in the catalog so it stays translatable.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "Catalog.tsx"
SPA_STRINGS = REPO_ROOT / "cps" / "spa_strings.py"


def _catalog() -> str:
    return CATALOG_TSX.read_text(encoding="utf-8")


def _spa_strings() -> str:
    return SPA_STRINGS.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# (1) RefreshCw icon button wired to the refresh route
# ---------------------------------------------------------------------------

def test_catalog_imports_refreshcw_icon():
    src = _catalog()
    assert re.search(r"\bRefreshCw\b", src), (
        "Catalog must import + render the lucide RefreshCw icon for the button"
    )


def test_refresh_button_calls_library_refresh_route():
    src = _catalog()
    # The POST that kicks off the background scan (csrf-exempt, NOT under /api/v1).
    assert "/cwa-library-refresh" in src, (
        "the refresh action must POST to the /cwa-library-refresh contract route"
    )
    # The button's onClick must invoke the refresh handler (not be a dead button).
    assert re.search(r"onClick=\{[^}]*\.refresh\(\)", src), (
        "the RefreshCw button onClick must call the refresh handler"
    )


# ---------------------------------------------------------------------------
# (2) Polls the messages endpoint until the scan reports a result
# ---------------------------------------------------------------------------

def test_polls_messages_endpoint():
    src = _catalog()
    assert "/cwa-library-refresh/messages" in src, (
        "must poll GET /cwa-library-refresh/messages for the scan result"
    )


def test_poll_interval_is_cleared():
    """A leaked setInterval would keep polling (and invalidate queries) after
    the catalog unmounts. The poll must be cleared — clearInterval on the stored
    timer, with the cleanup wired to unmount."""
    src = _catalog()
    assert "clearInterval" in src or "AbortController" in src, (
        "the poll interval must be cleared (clearInterval / AbortController) so "
        "it can't leak past unmount"
    )
    # The clear must run on unmount — an effect returning a cleanup arrow. The
    # arrow-return-arrow form is specific to the unmount cleanup (the file's
    # other effects return block bodies), so it pins the wiring without coupling
    # to a helper name.
    assert re.search(r"useEffect\(.+?=>\s*\(\)\s*=>", src, re.DOTALL), (
        "an effect must return a cleanup (arrow-return) wired to component unmount"
    )


def test_poll_is_bounded():
    """The poll must not run forever if the backend never posts a result."""
    src = _catalog()
    assert re.search(r"LIBRARY_REFRESH_MAX_MS\s*=\s*\d{4,6}", src), (
        "the poll must be bounded by a max-duration cap (no infinite polling)"
    )


# ---------------------------------------------------------------------------
# (3) Accessibility: labelled for screen readers
# ---------------------------------------------------------------------------

def test_refresh_button_has_translated_aria_label():
    src = _catalog()
    # The button must carry both a title tooltip and an aria-label, both via t().
    assert re.search(r"aria-label=\{t\('Refresh library'\)\}", src), (
        "the RefreshCw button needs an aria-label of t('Refresh library')"
    )
    assert re.search(r"title=\{t\('Refresh library'\)\}", src), (
        "the RefreshCw button needs a title tooltip of t('Refresh library')"
    )


def test_refresh_status_is_aria_live():
    """The scan's 'please wait' -> 'complete' transition must be announced
    (SC 4.1.3 Status Changes) — an aria-live polite region for the refresh line."""
    src = _catalog()
    assert 'aria-live="polite"' in src, (
        "the refresh status line must be an aria-live=\"polite\" region so the "
        "scan result is announced to assistive tech"
    )


# ---------------------------------------------------------------------------
# (4) i18n anchor — the new msgid stays extractable into messages.pot
# ---------------------------------------------------------------------------

def test_refresh_library_msgid_anchored():
    anchored = _spa_strings()
    assert re.search(r'_\(\s*"Refresh library"\s*\)', anchored), (
        "the new 'Refresh library' msgid must be anchored in cps/spa_strings.py "
        "so pybabel keeps it (it appears only in .tsx, which babel never scans)"
    )

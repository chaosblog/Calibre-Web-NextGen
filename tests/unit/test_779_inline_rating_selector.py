# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.unit
def test_editor_rating_is_inline_half_star_keyboard_control():
    src = (ROOT / "frontend/src/pages/EditBook.tsx").read_text()
    assert "function RatingSelector" in src
    assert 'role="slider"' in src
    assert "rating + 0.5" in src and "rating - 0.5" in src
    assert "Math.ceil" in src and "/ 2" in src
    assert "<StarRating rating={rating * 2}" in src
    assert "<select className={styles.inputNarrow} value={form.rating}" not in src
    assert "Clear rating" in src

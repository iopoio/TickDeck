"""test_profile_loader.py — load·save·delete cycle 영역 검증."""

from __future__ import annotations

import sys
from pathlib import Path

# 영역 = tests/ sibling 영역 (code/) sys.path 등록
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tickdeck_v2.profile.profile_loader import INPUT_KEYS, ProfileLoader


def test_profile_loader_load_save_delete_cycle():
    loader = ProfileLoader(session_id="pytest")

    # 1) 초기 영역 = profile 없음
    assert loader.load() is None
    assert loader.exists() is False
    assert loader.session_dir.exists()

    # 2) save = 6 인풋 정합·markdown 자국
    inputs = {
        "industry": "automotive",
        "audience": "외부 클라이언트",
        "tone": "정장",
        "source_policy": "각주 strict",
        "length": "15장",
        "language": "한국어",
    }
    path = loader.save(inputs)
    assert path == loader.profile_path
    assert path.exists()
    assert loader.exists() is True

    # 3) load = 6 인풋 영역 모두 markdown 영역 포함
    md = loader.load()
    assert md is not None
    for key in INPUT_KEYS:
        assert inputs[key] in md, f"{key} 값 누락"
    assert loader.session_id in md

    # 4) delete = 파일·세션 폴더 삭제·idempotent
    loader.delete()
    assert loader.exists() is False
    assert loader.load() is None
    assert not loader.session_dir.exists()

    # delete 재호출 = 에러 X
    loader.delete()

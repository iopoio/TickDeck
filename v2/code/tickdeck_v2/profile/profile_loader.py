"""profile_loader.py — 세션 임시 profile 저장·종료 시 자동 삭제.

claude-for-legal `claude-init` 사상 정합. DB X · 계정 X · 세션 종료 시 cleanup.
"""

from __future__ import annotations

import atexit
import shutil
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Mapping, Optional

PROFILE_FILENAME = "tickdeck_profile.md"
TEMPLATE_FILENAME = "tickdeck_profile.md.template"
INPUT_KEYS = (
    "industry",
    "audience",
    "tone",
    "source_policy",
    "length",
    "language",
)


def _template_path() -> Path:
    return Path(__file__).parent / TEMPLATE_FILENAME


class ProfileLoader:
    """세션 1개 = ProfileLoader 1개. tempfile 영역에 profile 자국·종료 시 삭제.

    사용:
        loader = ProfileLoader()
        loader.save({"industry": "automotive", ...})
        md = loader.load()
        loader.delete()  # 명시 종료 (atexit도 자동 등록)
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or uuid.uuid4().hex[:12]
        self._session_dir = Path(
            tempfile.mkdtemp(prefix=f"tickdeck_session_{self.session_id}_")
        )
        self._profile_path = self._session_dir / PROFILE_FILENAME
        atexit.register(self.delete)

    @property
    def profile_path(self) -> Path:
        return self._profile_path

    @property
    def session_dir(self) -> Path:
        return self._session_dir

    def render(self, inputs: Mapping[str, str]) -> str:
        """template 영역 6 인풋 채워서 markdown 영역 반환. 미지정 = '미지정'."""
        template = _template_path().read_text(encoding="utf-8")
        values = {key: inputs.get(key, "미지정") for key in INPUT_KEYS}
        values["created_at"] = datetime.now().isoformat(timespec="seconds")
        values["session_id"] = self.session_id
        return template.format(**values)

    def save(self, inputs: Mapping[str, str]) -> Path:
        """6 인풋 영역 받아서 profile 영역 저장. 반환 = 저장 경로."""
        md = self.render(inputs)
        self._profile_path.write_text(md, encoding="utf-8")
        return self._profile_path

    def load(self) -> Optional[str]:
        """저장된 profile markdown 반환. 미저장 시 None."""
        if not self._profile_path.exists():
            return None
        return self._profile_path.read_text(encoding="utf-8")

    def exists(self) -> bool:
        return self._profile_path.exists()

    def delete(self) -> None:
        """profile 파일 + 세션 폴더 삭제. idempotent."""
        if self._session_dir.exists():
            shutil.rmtree(self._session_dir, ignore_errors=True)

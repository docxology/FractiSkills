"""Hermetic contract tests for the deterministic cover renderer."""

from pathlib import Path

from fractiskills.cover import build_cover


def _minimal_analysis() -> dict:
    """Synthesize the smallest analysis record build_cover consumes."""
    return {
        "sections": [
            {"section": "A", "pages": 3, "words": 100},
            {"section": "B", "pages": 5, "words": 200},
        ],
        "skills": {"count": 8},
        "inventory": {"discovered_pages": 8},
        "augmentation": {"ok": 2, "attempts": 3},
    }


def test_build_cover_writes_valid_png(tmp_path) -> None:
    """build_cover writes a nonzero PNG under {output_dir}/figures."""
    out_path = Path(build_cover(_minimal_analysis(), str(tmp_path)))
    assert out_path == Path(tmp_path, "figures", "cover.png")
    payload = out_path.read_bytes()
    assert payload.startswith(b"\x89PNG")
    assert len(payload) > 0


def test_build_cover_is_deterministic(tmp_path) -> None:
    """Two renders from the same analysis record agree byte-for-byte."""
    first = Path(build_cover(_minimal_analysis(), str(tmp_path / "a")))
    second = Path(build_cover(_minimal_analysis(), str(tmp_path / "b")))
    assert first.read_bytes() == second.read_bytes()

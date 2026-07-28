from pathlib import Path

from app.static_files import resolve_static_dir


def test_resolve_static_dir_prefers_explicit_setting(tmp_path: Path) -> None:
    explicit = tmp_path / "explicit"
    explicit.mkdir()
    (explicit / "index.html").write_text("<html>explicit</html>", encoding="utf-8")
    assert resolve_static_dir(str(explicit)) == explicit.resolve()


def test_resolve_static_dir_falls_back_to_frontend_dist() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    dist = repo_root / "frontend" / "dist"
    if not (dist / "index.html").is_file():
        return
    assert resolve_static_dir("") == dist.resolve()

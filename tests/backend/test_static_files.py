from pathlib import Path

from app.static_files import mount_frontend
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_mount_frontend_serves_index_and_spa_routes(tmp_path: Path) -> None:
    static_dir = tmp_path / "static"
    assets_dir = static_dir / "assets"
    assets_dir.mkdir(parents=True)
    (static_dir / "index.html").write_text("<html>Cashier</html>", encoding="utf-8")
    (assets_dir / "app.js").write_text("console.log('ok');", encoding="utf-8")

    app = FastAPI()
    mount_frontend(app, static_dir)
    client = TestClient(app)

    root = client.get("/")
    assert root.status_code == 200
    assert "Cashier" in root.text

    asset = client.get("/assets/app.js")
    assert asset.status_code == 200

    admin = client.get("/admin/login")
    assert admin.status_code == 200
    assert "Cashier" in admin.text


def test_mount_frontend_skips_api_paths(tmp_path: Path) -> None:
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<html>ok</html>", encoding="utf-8")

    app = FastAPI()

    @app.get("/api/v1/demo")
    def demo() -> dict[str, str]:
        return {"ok": "yes"}

    mount_frontend(app, static_dir)
    client = TestClient(app)

    assert client.get("/api/v1/demo").json() == {"ok": "yes"}

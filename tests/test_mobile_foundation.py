import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "web" / "public"


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def test_manifest_declares_valid_install_icons():
    manifest = json.loads((PUBLIC / "manifest.webmanifest").read_text())
    assert manifest["name"].startswith("DatArg")
    assert manifest["display"] == "standalone"
    assert manifest["start_url"].startswith("/")

    icons = {icon["sizes"]: icon for icon in manifest["icons"]}
    for size in (192, 512):
        icon = icons[f"{size}x{size}"]
        path = PUBLIC / icon["src"].removeprefix("/")
        assert path.exists()
        assert png_dimensions(path) == (size, size)


def test_mobile_runtime_has_offline_and_remote_data_paths():
    index = (ROOT / "index.html").read_text()
    service_worker = (PUBLIC / "sw.js").read_text()
    data_client = (ROOT / "web" / "src" / "data-client.js").read_text()

    assert 'rel="manifest"' in index
    assert 'rel="apple-touch-icon"' in index
    assert "'/offline.html'" in service_worker
    assert "html.matchAll" in service_worker
    assert "url.pathname.startsWith('/data/')" in service_worker
    assert "https://dat-arg.vercel.app/data" in data_client


def test_capacitor_uses_the_shared_production_bundle():
    config = json.loads((ROOT / "capacitor.config.json").read_text())
    package = json.loads((ROOT / "package.json").read_text())

    assert config["appName"] == "DatArg"
    assert config["appId"] == "ar.fausto.datarg"
    assert config["webDir"] == "dist"
    assert package["dependencies"]["@capacitor/core"].startswith("^8.")
    assert package["scripts"]["native:sync"] == "npm run build && cap sync"

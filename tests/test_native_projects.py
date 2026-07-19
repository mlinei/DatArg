import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def test_android_project_has_identity_network_and_brand_assets():
    build = (ROOT / "android" / "app" / "build.gradle").read_text()
    manifest = (ROOT / "android" / "app" / "src" / "main" / "AndroidManifest.xml").read_text()
    styles = (ROOT / "android" / "app" / "src" / "main" / "res" / "values" / "styles.xml").read_text()
    variables = (ROOT / "android" / "variables.gradle").read_text()
    config = json.loads((ROOT / "capacitor.config.json").read_text())
    foreground = ROOT / "android" / "app" / "src" / "main" / "res" / "mipmap-xxxhdpi" / "ic_launcher_foreground.png"

    assert 'applicationId "com.mlinei.datarg"' in build
    assert 'android.permission.INTERNET' in manifest
    assert "minSdkVersion = 24" in variables
    assert '<item name="android:windowBackground">#06101F</item>' in styles
    assert '<item name="android:windowLightStatusBar">false</item>' in styles
    assert '<item name="android:windowLightNavigationBar">false</item>' in styles
    assert config["plugins"]["SystemBars"]["style"] == "DARK"
    assert foreground.exists()
    assert png_dimensions(foreground) == (192, 192)


def test_ios_project_has_identity_and_store_sized_assets():
    project = (ROOT / "ios" / "App" / "App.xcodeproj" / "project.pbxproj").read_text()
    app_icon = ROOT / "ios" / "App" / "App" / "Assets.xcassets" / "AppIcon.appiconset" / "AppIcon-512@2x.png"
    splash = ROOT / "ios" / "App" / "App" / "Assets.xcassets" / "Splash.imageset" / "Default@1x~universal~anyany.png"

    assert "PRODUCT_BUNDLE_IDENTIFIER = com.mlinei.datarg;" in project
    assert "IPHONEOS_DEPLOYMENT_TARGET = 15.0;" in project
    assert png_dimensions(app_icon) == (1024, 1024)
    assert png_dimensions(splash) == (2732, 2732)


def test_native_projects_receive_capacitor_plugins():
    expected = {
        "@capacitor/browser",
        "@capacitor/network",
        "@capacitor/splash-screen",
        "@capacitor/status-bar",
    }
    package = json.loads((ROOT / "package.json").read_text())
    assert expected <= package["dependencies"].keys()

    package_swift = (ROOT / "ios" / "App" / "CapApp-SPM" / "Package.swift").read_text()
    android_settings = (ROOT / "android" / "capacitor.settings.gradle").read_text()
    for plugin in ("browser", "network", "splash-screen", "status-bar"):
        assert plugin.replace("-", "") in package_swift.lower().replace("-", "")
        assert plugin.replace("-", "") in android_settings.lower().replace("-", "")

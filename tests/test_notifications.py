from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_mobile_opt_in_and_deep_link_are_present():
    main = (ROOT / "web" / "src" / "main.js").read_text()
    notifications = (ROOT / "web" / "src" / "notifications.js").read_text()

    assert 'id="notification-toggle"' in main
    assert "requestPermissions" in notifications
    assert "subscribeToTopic" in notifications
    assert "notificationActionPerformed" in notifications
    assert "window.location.hash" in notifications


def test_automation_sends_only_after_publishing_data():
    workflow = (ROOT / ".github" / "workflows" / "update-data.yml").read_text()
    commit_position = workflow.index('git commit -m "data: actualización automática"')
    auth_position = workflow.index("google-github-actions/auth@v3")
    notification_position = workflow.index("send-data-notification.mjs")

    assert commit_position < auth_position < notification_position
    assert "id-token: write" in workflow
    assert "workload_identity_provider:" in workflow
    assert "datarg-notifications@datarg.iam.gserviceaccount.com" in workflow
    assert "FIREBASE_SERVICE_ACCOUNT_JSON" not in workflow
    assert "create-data-notification.mjs" in workflow

"""
app_launcher.py
Entry point for RF-DIAG when running as a bundled macOS .app via PyInstaller.

Responsibilities:
  1. Resolve bundled resource paths (templates) for Flask
  2. Call wifi_tool.main() which starts the Flask server
  3. Open http://127.0.0.1:5001 in Safari once the server is ready
  4. Show a macOS notification when the app is ready
"""

import os
import sys
import threading
import time
import subprocess
import webbrowser


def resource_path(relative: str) -> str:
    """Absolute path to a bundled resource. Works in both dev and .app."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


# Wire up Flask template folder BEFORE importing wifi_tool
os.environ.setdefault("RFDIAG_TEMPLATES", resource_path("templates"))


def _request_location_permission():
    """
    Explicitly request CoreLocation permission so RF-DIAG appears in
    System Settings > Privacy & Security > Location Services.
    Must be called before the Flask server starts.
    """
    try:
        import AppKit
        from CoreLocation import (
            CLLocationManager,
            kCLAuthorizationStatusNotDetermined,
            kCLAuthorizationStatusAuthorizedWhenInUse,
            kCLAuthorizationStatusAuthorizedAlways,
        )
        # An NSApplication context is required for the permission dialog
        app = AppKit.NSApplication.sharedApplication()
        app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)

        mgr = CLLocationManager.alloc().init()
        status = CLLocationManager.authorizationStatus()
        print(f"[Location] Authorization status: {status}")

        if status == kCLAuthorizationStatusNotDetermined:
            print("[Location] Requesting permission — please respond to the dialog...")
            mgr.requestWhenInUseAuthorization()
            # Poll the run loop until permission is determined (up to 60 s)
            deadline = AppKit.NSDate.dateWithTimeIntervalSinceNow_(60.0)
            while True:
                AppKit.NSRunLoop.currentRunLoop().runUntilDate_(
                    AppKit.NSDate.dateWithTimeIntervalSinceNow_(0.5)
                )
                status = CLLocationManager.authorizationStatus()
                if status != kCLAuthorizationStatusNotDetermined:
                    break
                if AppKit.NSDate.date().compare_(deadline) != -1:  # NSOrderedAscending
                    print("[Location] Timed out waiting for permission.")
                    break

        granted = status in (
            kCLAuthorizationStatusAuthorizedWhenInUse,
            kCLAuthorizationStatusAuthorizedAlways,
        )
        print(f"[Location] Permission {'granted' if granted else 'denied or undetermined'} (status={status})")
        return mgr   # keep reference alive
    except Exception as e:
        print(f"[Location] Permission request failed: {e}")
        return None


def _open_browser_when_ready():
    """Wait for Flask to respond, then open the web UI and send a notification."""
    url = "http://127.0.0.1:5001"
    import urllib.request
    for _ in range(40):          # up to 20 s
        time.sleep(0.5)
        try:
            urllib.request.urlopen(url, timeout=1)
            break
        except Exception:
            continue

    webbrowser.open(url)   # cross-platform: works on macOS, Windows, Linux

    # macOS notification (no-op on other platforms)
    if sys.platform == "darwin":
        try:
            subprocess.run(
                ["osascript", "-e",
                 'display notification "RF-DIAG is ready. Browser opened." '
                 'with title "RF-DIAG"'],
                check=False,
            )
        except Exception:
            pass


if __name__ == "__main__":
    _loc_mgr = _request_location_permission()   # triggers the system dialog

    threading.Thread(target=_open_browser_when_ready, daemon=True).start()

    import wifi_tool
    wifi_tool.main()

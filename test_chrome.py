"""
Chrome automation from WSL using CDP (Chrome DevTools Protocol).

This approach works reliably in WSL by:
1. Starting Chrome on Windows with remote debugging enabled
2. Connecting to it via WebSocket from Playwright
"""

import subprocess
import time
import socket
from playwright.sync_api import sync_playwright

DEBUG_PORT = 9222


def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def start_chrome_with_debugging():
    """Start Chrome with remote debugging enabled using cmd.exe."""
    if is_port_in_use(DEBUG_PORT):
        print(f"Chrome already running on port {DEBUG_PORT}")
        return None

    print("Starting Chrome with remote debugging...")
    # Use cmd.exe to launch Chrome - more reliable from WSL
    cmd = (
        'cmd.exe /c start "" '
        '"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" '
        f'--remote-debugging-port={DEBUG_PORT} '
        '--no-first-run '
        '--no-default-browser-check '
        '--user-data-dir=C:\\temp\\chrome-debug'
    )
    subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Wait for Chrome to start
    print("Waiting for Chrome to start...")
    for i in range(20):
        if is_port_in_use(DEBUG_PORT):
            print(f"Chrome started on port {DEBUG_PORT}")
            return True
        time.sleep(0.5)
        if i % 4 == 3:
            print(f"  Still waiting... ({(i+1)/2}s)")

    print("Warning: Chrome may not have started correctly")
    return False


def main():
    print("=" * 50)
    print("Chrome Automation Test (WSL via CDP)")
    print("=" * 50)

    # Start Chrome with debugging
    started = start_chrome_with_debugging()

    if not started and not is_port_in_use(DEBUG_PORT):
        print("\nChrome failed to start. Please:")
        print("1. Close any existing Chrome windows")
        print("2. Run this in Windows PowerShell:")
        print('   & "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222')
        print("3. Then run this script again")
        return

    try:
        with sync_playwright() as p:
            print("\n1. Connecting to Chrome via CDP...")
            browser = p.chromium.connect_over_cdp(f"http://localhost:{DEBUG_PORT}")

            print("2. Getting browser context...")
            context = browser.contexts[0] if browser.contexts else browser.new_context()

            print("3. Creating new page...")
            page = context.new_page()

            print("4. Navigating to example.com...")
            page.goto("https://example.com")

            print(f"5. Page title: {page.title()}")

            print("6. Taking screenshot...")
            page.screenshot(path="test_screenshot.png")

            print("\n" + "=" * 50)
            print("SUCCESS! Chrome automation is working!")
            print("=" * 50)
            print(f"\nScreenshot saved to: test_screenshot.png")

    except Exception as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("1. Close ALL Chrome windows and try again")
        print("2. Or start Chrome manually with debugging:")
        print('   In PowerShell: & "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222')


if __name__ == "__main__":
    main()

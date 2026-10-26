import os
import time
from typing import List, Dict, Any, Tuple, Optional
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from config import Config

class BrowserSession:
    """
    Manages Playwright browser lifecycle, console listeners,
    network tracking, and full-page visual captures.
    """
    def __init__(self, headless: Optional[bool] = None):
        self.headless = Config.HEADLESS if headless is None else headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        self.console_errors: List[str] = []
        self.failed_requests: List[str] = []

    def start(self) -> Page:
        self.playwright = sync_playwright().start()
        launch_args = ["--disable-blink-features=AutomationControlled"]
        if not self.headless:
            launch_args.extend(["--start-maximized", "--no-sandbox"])

        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=launch_args
        )
        self.context = self.browser.new_context(
            viewport=None if not self.headless else {"width": Config.VIEWPORT_WIDTH, "height": Config.VIEWPORT_HEIGHT},
            user_agent=Config.USER_AGENT
        )
        self.page = self.context.new_page()
        
        if not self.headless:
            try:
                self.page.bring_to_front()
            except Exception:
                pass

        # Attach listeners
        self.page.on("console", self._handle_console)
        self.page.on("pageerror", self._handle_page_error)
        self.page.on("response", self._handle_response)

        return self.page

    def _handle_console(self, msg):
        if msg.type in ["error", "warning"]:
            self.console_errors.append(f"[{msg.type.upper()}] {msg.text}")

    def _handle_page_error(self, exc):
        self.console_errors.append(f"[UNCAUGHT JS EXCEPTION] {str(exc)}")

    def _handle_response(self, response):
        if response.status >= 400:
            self.failed_requests.append(f"HTTP {response.status}: {response.url}")

    def navigate(self, url: str) -> Tuple[bool, str]:
        """Navigates to URL, checks HTTP status, and waits for network stabilization."""
        if not (url.startswith("http://") or url.startswith("https://") or url.startswith("file://")):
            url = "https://" + url
            
        try:
            response = self.page.goto(url, wait_until="domcontentloaded", timeout=Config.DEFAULT_TIMEOUT_MS)
            
            # Check if navigation failed or returned error HTTP status
            if response is None:
                return False, f"Could not reach '{url}'. The server did not respond."

            if response.status == 404:
                return False, f"Website does not exist (HTTP 404 Not Found). The URL '{url}' is not hosted or has been removed."
            elif response.status >= 400:
                return False, f"Website returned an error (HTTP {response.status} {response.status_text or 'Error'})."

            # Give short settling time for dynamic client hydration
            time.sleep(1.0)

            # In headful demo mode, perform smooth visual scroll so viewers can watch the audit
            if not self.headless:
                self.simulate_visual_inspection()

            return True, self.page.title()
        except Exception as e:
            err_msg = str(e)
            if "ERR_NAME_NOT_RESOLVED" in err_msg or "ERR_CONNECTION_REFUSED" in err_msg:
                return False, f"Domain does not exist or cannot be resolved: '{url}'"
            return False, f"Navigation failed: {err_msg}"

    def simulate_visual_inspection(self):
        """Smoothly scrolls the page in headful mode so viewers can watch the audit in real-time."""
        try:
            self.page.evaluate("""
                async () => {
                    await new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = 300;
                        const timer = setInterval(() => {
                            const scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;
                            if (totalHeight >= scrollHeight) {
                                clearInterval(timer);
                                resolve();
                            }
                        }, 100);
                    });
                }
            """)
            time.sleep(0.5)
            self.page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'});")
            time.sleep(0.5)
        except Exception:
            pass

    def capture_screenshot(self, filename: str) -> str:
        """Captures full-page visual screenshot for audit evidence."""
        filepath = os.path.join(Config.REPORTS_DIR, filename)
        self.page.screenshot(path=filepath, full_page=True)
        return filepath

    def close(self, pause_seconds: float = 0.0):
        try:
            if not self.headless and pause_seconds > 0:
                time.sleep(pause_seconds)
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass

"""
VOLAURA Web Checker — Batch Playwright-based page tester.
MVP (Phase 1): Single-threaded, deployed to Railway.
Reuses browser instance across tasks.
"""

import asyncio
import json
import base64
from typing import Optional
from dataclasses import dataclass, asdict
from playwright.async_api import async_playwright, Page

@dataclass
class Assertion:
    """Single test condition: does selector match expectation?"""
    selector: str
    expect: str
    ok: Optional[bool] = None
    details: Optional[str] = None

@dataclass
class Task:
    """Single page/flow to check."""
    url: str
    flow: Optional[str] = None
    assertions: Optional[list[dict]] = None

@dataclass
class CheckResult:
    """Result for one task."""
    url: str
    flow: Optional[str]
    status: str  # "ok" or "failed"
    checks: list[dict]
    screenshot_base64: Optional[str] = None
    error: Optional[str] = None

class VolauraChecker:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None

    async def start(self):
        """Initialize browser once at startup."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()

    async def stop(self):
        """Cleanup."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def check_page(self, task: dict) -> CheckResult:
        """Check single page/flow."""
        url = task.get("url")
        flow = task.get("flow", "unnamed")
        assertions = task.get("assertions", [])

        try:
            page = await self.context.new_page()
            await page.set_viewport_size({"width": 1280, "height": 800})
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Run assertions
            checks = []
            failed = False

            for assertion in assertions:
                selector = assertion.get("selector")
                expect = assertion.get("expect")

                try:
                    # Try to find element
                    element = await page.query_selector(selector)

                    if element:
                        text = await element.text_content() if expect else None
                        ok = expect in text if expect and text else bool(element)
                        details = f"Found: {text[:100]}" if text else "Element exists"
                    else:
                        ok = False
                        details = "Selector not found"

                except Exception as e:
                    ok = False
                    details = f"Error: {str(e)[:100]}"

                checks.append({
                    "selector": selector,
                    "expect": expect,
                    "ok": ok,
                    "details": details
                })

                if not ok:
                    failed = True

            # Screenshot if failed
            screenshot_base64 = None
            if failed:
                screenshot_bytes = await page.screenshot()
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode()

            status = "failed" if failed else "ok"
            result = CheckResult(
                url=url,
                flow=flow,
                status=status,
                checks=checks,
                screenshot_base64=screenshot_base64
            )

            await page.close()
            return result

        except Exception as e:
            result = CheckResult(
                url=url,
                flow=flow,
                status="failed",
                checks=[],
                error=str(e)[:200]
            )
            try:
                await page.close()
            except:
                pass
            return result

    async def check_batch(self, tasks: list[dict]) -> dict:
        """Process multiple tasks (serial in MVP)."""
        results = []
        passed = []
        failed = []

        for task in tasks:
            result = await self.check_page(task)
            results.append(asdict(result))

            if result.status == "ok":
                passed.append(result.url)
            else:
                failed.append(result.url)

        return {
            "results": results,
            "summary": {
                "total": len(tasks),
                "passed": len(passed),
                "failed": len(failed),
                "passed_urls": passed,
                "failed_urls": failed
            }
        }


# Global instance
checker = VolauraChecker()


async def check_volaura(payload: dict) -> dict:
    """Entry point: accepts {tasks: [...], max_parallel, return_screenshots}."""
    tasks = payload.get("tasks", [])
    return_screenshots = payload.get("return_screenshots", True)

    if not tasks:
        return {"error": "No tasks provided"}

    result = await checker.check_batch(tasks)

    # Strip base64 if not needed
    if not return_screenshots:
        for item in result["results"]:
            item.pop("screenshot_base64", None)

    return result

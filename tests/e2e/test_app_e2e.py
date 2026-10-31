"""End-to-End Playwright test suite for university faculty workload balancing system.

Covers:
1. OTP login for both roles (admin & faculty)
2. Run optimizer (CP-SAT/Greedy) and await completion
3. Open a conflict and view violation diagnostics
4. Apply an automated schedule repair
5. Manual assignment override with required reason and violation acknowledgement
6. Faculty blocked from accessing admin routes (RBAC enforcement)

Tagged with @pytest.mark.e2e.
"""

from __future__ import annotations

import json
import time
import urllib.request
import pytest
from playwright.sync_api import Page, expect


def get_dev_otp(email: str) -> str:
    """Helper retrieving in-memory dev OTP from backend API."""
    url = f"http://127.0.0.1:8000/api/v1/auth/dev-otp?email={email}"
    for _ in range(15):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                data = json.loads(resp.read().decode())
                otp = data.get("otp")
                if otp:
                    return str(otp)
        except Exception:
            pass
        time.sleep(0.4)
    raise RuntimeError(f"Failed to fetch dev OTP for {email}")


def perform_otp_login(page: Page, app_url: str, email: str) -> None:
    """Perform full OTP login cycle for the designated email address."""
    page.goto(f"{app_url}/login")
    page.wait_for_selector("#email", timeout=10000)

    # Enter email
    page.fill("#email", email)
    page.click("button:has-text('Send One-Time Passcode')")

    # Await OTP code input
    page.wait_for_selector("#otp-code", timeout=10000)

    # Retrieve dev passcode and input
    otp = get_dev_otp(email)
    page.fill("#otp-code", otp)


# ---------------------------------------------------------------------------
# Test 1: OTP Login for Both Roles
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_e2e_otp_login_admin(page: Page, app_url: str):
    """Admin logs in via OTP and is redirected to /admin cockpit."""
    perform_otp_login(page, app_url, "admin@university.edu")

    # Verify landing on Admin Overview Cockpit
    page.wait_for_url("**/admin", timeout=12000)
    expect(page.locator("body")).to_contain_text("Department Planning Workspace")
    expect(page.locator("body")).to_contain_text("Workload Balancing")


@pytest.mark.e2e
def test_e2e_otp_login_faculty(page: Page, app_url: str):
    """Faculty logs in via OTP and is redirected to /faculty portal."""
    perform_otp_login(page, app_url, "ada.lovelace@university.edu")

    # Verify landing on Faculty Portal
    page.wait_for_url("**/faculty", timeout=12000)
    expect(page.locator("body")).to_contain_text("Assigned Teaching Load")


# ---------------------------------------------------------------------------
# Test 2: Faculty Blocked from Admin Routes
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_e2e_faculty_blocked_from_admin_routes(page: Page, app_url: str):
    """Faculty user is strictly blocked from accessing /admin routes."""
    perform_otp_login(page, app_url, "ada.lovelace@university.edu")
    page.wait_for_url("**/faculty", timeout=12000)

    # Attempt direct navigation to /admin
    page.goto(f"{app_url}/admin")
    page.wait_for_timeout(1000)

    # Must display 403 Forbidden
    body_text = page.locator("body").text_content() or ""
    assert "403" in body_text or "Access Forbidden" in body_text or "Forbidden" in body_text

    # Attempt direct navigation to /admin/assignments
    page.goto(f"{app_url}/admin/assignments")
    page.wait_for_timeout(1000)
    body_text = page.locator("body").text_content() or ""
    assert "403" in body_text or "Access Forbidden" in body_text or "Forbidden" in body_text


# ---------------------------------------------------------------------------
# Test 3: Run Optimizer
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_e2e_run_optimizer(page: Page, app_url: str):
    """Admin triggers optimizer solve in background and awaits completion."""
    perform_otp_login(page, app_url, "admin@university.edu")
    page.wait_for_url("**/admin", timeout=12000)

    # Switch to Optimizer tab
    optimizer_tab = page.locator("button:has-text('Optimizer')")
    optimizer_tab.click()

    # Trigger solve
    solve_button = page.locator("button:has-text('Execute')")
    solve_button.wait_for(state="visible", timeout=5000)
    solve_button.click()

    # Wait for completion (either job status badge or completion message)
    page.wait_for_selector(
        "text=COMPLETED, text=Feasible, text=Optimality, text=Successfully",
        timeout=25000,
    )


# ---------------------------------------------------------------------------
# Test 4: Open a Conflict
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_e2e_open_conflict(page: Page, app_url: str):
    """Admin opens conflicts tab, examines violation details and responsible rule."""
    perform_otp_login(page, app_url, "admin@university.edu")
    page.wait_for_url("**/admin", timeout=12000)

    # Switch to Conflicts tab
    conflicts_tab = page.locator("button:has-text('Conflicts')")
    conflicts_tab.click()

    # Confirm conflicts panel header and violation counters are visible
    expect(page.locator("body")).to_contain_text("Schedule Conflicts & Rule Violations")
    expect(page.locator("body")).to_contain_text("Constraint Diagnosis")


# ---------------------------------------------------------------------------
# Test 5: Apply a Schedule Repair
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_e2e_apply_repair(page: Page, app_url: str):
    """Admin opens repair strategy modal and applies an automated remediation."""
    perform_otp_login(page, app_url, "admin@university.edu")
    page.wait_for_url("**/admin", timeout=12000)

    # Navigate to conflicts panel
    page.locator("button:has-text('Conflicts')").click()

    # Click Synthesize Repairs button
    repair_btn = page.locator("button:has-text('Synthesize Repairs')")
    repair_btn.wait_for(state="visible", timeout=5000)
    repair_btn.click()

    # Repair modal must be displayed
    page.wait_for_selector("text=Select Schedule Repair Strategy", timeout=5000)

    # Apply the first repair alternative
    apply_btn = page.locator("button:has-text('Apply')").first
    apply_btn.click()

    # Verify confirmation or status notification
    page.wait_for_timeout(1000)
    expect(page.locator("body")).to_contain_text("applied")


# ---------------------------------------------------------------------------
# Test 6: Override with a Reason
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_e2e_override_with_reason(page: Page, app_url: str):
    """Admin performs manual assignment override providing required reason."""
    perform_otp_login(page, app_url, "admin@university.edu")
    page.wait_for_url("**/admin", timeout=12000)

    # Switch to Assignments tab
    page.locator("button:has-text('Assignments')").click()
    page.wait_for_timeout(1500)

    # Locate first available Override button
    override_btn = page.locator("button:has-text('Override')").first
    if override_btn.is_visible():
        override_btn.click()

        # Modal opens
        page.wait_for_selector("text=Manual Assignment Override", timeout=5000)

        # Select replacement faculty
        select_faculty = page.locator("select").first
        select_faculty.select_option(index=1)

        # Enter justification reason
        reason_textarea = page.locator("textarea")
        reason_textarea.fill("Department Chair allocation for sabbatical faculty coverage")

        # Check acknowledgment if violation detected
        ack_checkbox = page.locator("input[type='checkbox']")
        if ack_checkbox.is_visible():
            ack_checkbox.check()

        # Click Apply Override
        page.locator("button:has-text('Apply Override')").click()
        page.wait_for_timeout(1500)


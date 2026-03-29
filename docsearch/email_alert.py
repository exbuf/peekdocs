"""Email alert notifications for docsearch suite auto-runs."""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def send_suite_alert(config, suite_name, folder, results, run_time,
                     passed, total, verdict, report_path=None):
    """Send an email alert for a completed suite auto-run.

    Args:
        config: dict with keys smtp_host, smtp_port, smtp_user, smtp_password,
                email_from, email_to, email_on (\"failure\" or \"always\").
        suite_name: Name of the suite that ran.
        folder: Search folder path.
        results: List of per-test result dicts.
        run_time: Formatted timestamp string.
        passed: Number of tests that passed.
        total: Total number of tests.
        verdict: \"PASSED\" or \"FAILED\".
        report_path: Optional path to the .docx suite report.

    Returns:
        None on success, error message string on failure.
    """
    # Validate required config
    smtp_host = config.get("smtp_host", "").strip()
    smtp_port = config.get("smtp_port", "587").strip()
    smtp_user = config.get("smtp_user", "").strip()
    smtp_password = config.get("smtp_password", "").strip()
    email_from = config.get("email_from", "").strip()
    email_to = config.get("email_to", "").strip()
    email_on = config.get("email_on", "failure").strip().lower()

    if not smtp_host or not email_to:
        return None  # Email not configured — silently skip

    # Check if we should send based on email_on setting
    if email_on == "failure" and verdict == "PASSED":
        return None  # Only alert on failures

    if not email_from:
        email_from = smtp_user or f"docsearch@{smtp_host}"

    try:
        smtp_port = int(smtp_port)
    except ValueError:
        smtp_port = 587

    # Build subject line
    subject = f"docsearch suite {verdict}: {suite_name} — {passed}/{total} passed"

    # Build body
    lines = [
        f"Suite: {suite_name}",
        f"Folder: {folder}",
        f"Date: {run_time}",
        f"Result: {passed} of {total} tests passed — {verdict}",
        "",
        "Details:",
        "-" * 40,
    ]

    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        pc = r.get("pass_criteria", {"op": ">=", "n": 1})
        lines.append(f"  [{status}] {r['name']} — {r['match_count']} match(es) (need {pc['op']} {pc['n']})")

    lines.append("")
    lines.append("-" * 40)

    if report_path:
        lines.append(f"Suite report: {report_path}")

    lines.append("")
    lines.append("This is an automated notification from docsearch.")
    lines.append("To disable, set Email Alerts to Off in the docsearch GUI.")

    body = "\n".join(lines)

    # Build message
    msg = MIMEMultipart()
    msg["From"] = email_from
    msg["To"] = email_to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Send
    try:
        context = ssl.create_default_context()
        if smtp_port == 465:
            # SSL
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=15) as server:
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
        else:
            # STARTTLS (port 587) or plain (port 25)
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                if smtp_port == 587:
                    server.starttls(context=context)
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
        return None  # Success
    except Exception as e:
        return f"Email alert failed: {e}"

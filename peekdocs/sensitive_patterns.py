"""Sensitive data scan patterns — PII and security-relevant regex definitions."""

SENSITIVE_PATTERNS = [
    # (category, regex, severity, description)
    # severity: "high" (red), "moderate" (yellow), "info" (blue)
    (
        "Social Security Numbers",
        r"(?<![\d\-/a-zA-Z_.])\d{3}-\d{2}-\d{4}(?![\d\-/a-zA-Z_])",
        "high",
        "SSN patterns (XXX-XX-XXXX)",
    ),
    (
        "Credit Card Numbers",
        r"(?<![\d/a-zA-Z_\-.])(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6(?:011|5\d{2}))[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{1,4}(?![\d/a-zA-Z_])",
        "high",
        "Visa, Mastercard, Amex, Discover patterns",
    ),
    (
        "Tax ID / EIN",
        r"(?<!\d)\d{2}-\d{7}(?!\d)",
        "high",
        "Employer Identification Numbers (XX-XXXXXXX)",
    ),
    (
        "Email Addresses",
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        "moderate",
        "Email address patterns",
    ),
    (
        "Phone Numbers",
        r"(?<!\d)(?:\(\d{3}\)\s?\d{3}[-.\s]\d{4}|\d{3}[-.\s]\d{3}[-.\s]\d{4})(?!\d)",
        "moderate",
        "US phone number patterns",
    ),
    (
        "Passwords / Secrets",
        r"(?i)(?:password|passwd|pwd|secret|api[_-]?key|token)\s*[:=]\s*\S+",
        "moderate",
        "Lines containing password, secret, or API key assignments",
    ),
    (
        "Dates of Birth",
        r"(?i)(?:dob|date\s+of\s+birth|born)\s*[:=]?\s*\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}",
        "moderate",
        "Date-of-birth patterns",
    ),
    (
        "Dollar Amounts",
        r"\$[\d,]+(?:\.\d{2})?",
        "info",
        "Dollar amounts in a user-specified range (see Min/Max fields)",
    ),
]

SEVERITY_COLORS = {
    "high": {"bg": "#FF4444", "fg": "white", "label": "HIGH"},
    "moderate": {"bg": "#FFB800", "fg": "black", "label": "MODERATE"},
    "info": {"bg": "#4488FF", "fg": "white", "label": "INFO"},
}

SEVERITY_ORDER = ["high", "moderate", "info"]

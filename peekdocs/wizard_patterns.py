"""Search Wizard pattern definitions for general-purpose regex presets.

The presets that ship with peekdocs are deliberately generic — dates, phone
numbers, dollar amounts, invoices, etc. peekdocs does not ship presets named
after personal-identifier categories or named after specific industries.
Users who need a pattern that isn't here can add their own through the
Regex Search collection editor.
"""

WIZARD_PATTERNS = {
    "Common / General": [
        ("Date (MM/DD/YYYY)", r"\d{1,2}/\d{1,2}/\d{2,4}"),
        ("Date (YYYY-MM-DD)", r"\d{4}-\d{1,2}-\d{1,2}"),
        ("Dollar Amount", r"\$[\d,]+\.?\d*"),
        ("Percentage", r"\d+\.?\d*\s*%"),
        ("Phone Number", r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}"),
        ("Email Address", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
        ("6-digit Number", r"\d{6}"),
    ],
    "Business / Finance": [
        ("Invoice Number", r"INV[-\s]?\d{4,}"),
        ("Purchase Order", r"PO[-\s]?\d{4,}"),
        ("Dollar Amount", r"\$[\d,]+\.?\d*"),
        ("Account Number", r"[Aa]cct?\.?\s*#?\s*\d{4,}"),
        ("Date (MM/DD/YYYY)", r"\d{1,2}/\d{1,2}/\d{2,4}"),
    ],
    "Legal": [
        ("Case Number", r"\d{2}-[A-Z]{2}-\d{4,}"),
        ("Statute Reference", r"§\s*\d+"),
        ("Dollar Amount", r"\$[\d,]+\.?\d*"),
        ("Date (MM/DD/YYYY)", r"\d{1,2}/\d{1,2}/\d{2,4}"),
        ("Bates Number", r"[A-Z]{2,}\d{6,}"),
        ("Court Docket", r"[Nn]o\.\s*\d{2}-\d{4,}"),
    ],
    "Engineering / Technical": [
        ("Part Number", r"[A-Z]{2,3}-\d{4,}"),
        ("Revision Number", r"[Rr]ev\.?\s*[A-Z0-9]+"),
        ("Measurement", r"\d+\.?\d*\s*(mm|cm|m|in|ft|kg|lb|psi|MPa)"),
        ("Serial Number", r"S/?N[: ]?\s*[A-Z0-9-]{4,}"),
        ("Tolerance", r"[±+\-]\s*\d+\.?\d*"),
        ("Drawing Number", r"DWG[-\s]?\d{4,}"),
    ],
    "Real Estate": [
        ("Parcel / APN", r"\d{3}-\d{3}-\d{3}"),
        ("Dollar Amount", r"\$[\d,]+\.?\d*"),
        ("Square Footage", r"[\d,]+\s*sq\.?\s*ft"),
        ("Lot/Block", r"[Ll]ot\s+\d+"),
        ("Date (MM/DD/YYYY)", r"\d{1,2}/\d{1,2}/\d{2,4}"),
        ("MLS Number", r"MLS[#\s]?\d{5,}"),
    ],
    "HR / Admin": [
        ("Employee ID", r"[Ee]mp\.?\s*#?\s*\d{4,}"),
        ("Phone Number", r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}"),
        ("Email Address", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
        ("Date (MM/DD/YYYY)", r"\d{1,2}/\d{1,2}/\d{2,4}"),
        ("Dollar Amount", r"\$[\d,]+\.?\d*"),
    ],
}

WIZARD_CATEGORY_ORDER = [
    "Common / General",
    "Business / Finance",
    "Legal",
    "Engineering / Technical",
    "Real Estate",
    "HR / Admin",
]

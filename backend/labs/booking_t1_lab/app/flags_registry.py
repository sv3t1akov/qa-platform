"""
Registry of all 13 Booking T1 bug flags. Values must match seed_bugs.sql exactly (UPPERCASE).
Format: FLAG{BUG_ID_XXXXXXXX}
Based on BOOKING_T1_SPEC_v2.md
"""

FLAGS = {
    # Mission 1: Properties & Rooms API (3 flags)
    "NEGATIVE_ID": "FLAG{NEGATIVE_ID_3f7a9c2d}",
    "BOUNDARY_OVERFLOW": "FLAG{BOUNDARY_OVERFLOW_8b4e2f1a}",
    "HIDDEN_FIELDS": "FLAG{HIDDEN_FIELDS_9a1f5d3c}",
    
    # Mission 2: Availability API (4 flags)
    "DATE_PAST": "FLAG{DATE_PAST_4f8a2c6e}",
    "DATE_REVERSED": "FLAG{DATE_REVERSED_7d3b9a1f}",
    "ZERO_DURATION": "FLAG{ZERO_DURATION_1c5e9b3d}",
    "CAPACITY_EXCEEDED": "FLAG{CAPACITY_EXCEEDED_9d1a5f7e}",
    
    # Mission 3: Bookings API (4 flags)
    "MISSING_REQUIRED": "FLAG{MISSING_REQUIRED_5b1e3c9a}",
    "PRICE_OVERRIDE": "FLAG{PRICE_OVERRIDE_2f6a8d4e}",
    "WRONG_STATUS_CODE": "FLAG{WRONG_STATUS_CODE_6c2d8a4f}",
    "IDOR_ACCESS": "FLAG{IDOR_ACCESS_8c4e2a6f}",
    
    # Mission 4: Guest Profile API (2 flags)
    "TYPE_COERCION": "FLAG{TYPE_COERCION_4a3c7e9b}",
    "INVALID_FORMAT": "FLAG{INVALID_FORMAT_1b5e9c3f}",
}


def get_flag(bug_id: str) -> str:
    """Return flag string for bug_id or empty string if unknown."""
    return FLAGS.get(bug_id, "")

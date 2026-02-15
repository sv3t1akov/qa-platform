"""
Registry of all 17 Social T1 bug flags.
Values must match seed_social_t1_bugs.sql exactly (UPPERCASE).
Based on SOCIAL_T1_INTERNAL_FLAGS.md
"""

FLAGS = {
    # Mission 1: User Profile API (4 flags)
    "MISSING_REQUIRED": "FLAG{MISSING_REQUIRED_4b6d8e2a}",
    "WRONG_TYPE": "FLAG{WRONG_TYPE_9c1f3a5b}",
    "OVERFLOW_MAXLENGTH": "FLAG{OVERFLOW_MAXLENGTH_2e7d4c6f}",
    "MASS_ASSIGNMENT": "FLAG{MASS_ASSIGNMENT_6a8b2c4d}",
    # Mission 2: Posts API (4 flags)
    "EMPTY_CONTENT": "FLAG{EMPTY_CONTENT_3b5d7f9a}",
    "INVALID_ENUM": "FLAG{INVALID_ENUM_6e8a2c4d}",
    "OVERFLOW_ARRAY": "FLAG{OVERFLOW_ARRAY_9f1b3d5e}",
    "WRONG_DELETE_CODE": "FLAG{WRONG_DELETE_CODE_1a3c5e7b}",
    # Mission 3: Comments API (4 flags)
    "ORPHAN_COMMENT": "FLAG{ORPHAN_COMMENT_4c6e8a2b}",
    "WRONG_CREATE_CODE": "FLAG{WRONG_CREATE_CODE_2a4c6e8f}",
    "INTEGER_OVERFLOW": "FLAG{INTEGER_OVERFLOW_5b7d9f1a}",
    "EXTRA_FIELDS": "FLAG{EXTRA_FIELDS_8c2e4a6b}",
    # Mission 4: Feed & Social Graph API (5 flags)
    "MISSING_AUTH": "FLAG{MISSING_AUTH_4b6d8e2a}",
    "INVALID_QUERY_ENUM": "FLAG{INVALID_QUERY_ENUM_7c9e1a3b}",
    "LIMIT_OVERFLOW": "FLAG{LIMIT_OVERFLOW_2d4f6b8a}",
    "FOLLOW_SELF": "FLAG{FOLLOW_SELF_3a5c7e9b}",
    "FOLLOW_DUPLICATE": "FLAG{FOLLOW_DUPLICATE_6b8d2f4a}",
}


def get_flag(bug_id: str) -> str:
    """Return flag string for bug_id or empty string if unknown."""
    return FLAGS.get(bug_id, "")

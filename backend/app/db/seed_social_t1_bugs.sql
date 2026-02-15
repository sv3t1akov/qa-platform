-- Social T1 Bugs (Flags)
-- Based on SOCIAL_T1_INTERNAL_FLAGS.md
-- Execute this file AFTER seed_social_t1_missions.sql
-- IMPORTANT: All flags must be in UPPERCASE, as the validation system converts them to UPPER()

INSERT INTO bugs (id, mission_id, title, description, flag, points, difficulty, sort_order, active) VALUES
-- Mission 1: User Profile API (4 flags)
('social-t1-user-profile-MISSING_REQUIRED', 'social-t1-user-profile', 'Missing Required', 'Required field username not validated on server', 'FLAG{MISSING_REQUIRED_4b6d8e2a}', 75, 'Medium', 1, true),
('social-t1-user-profile-WRONG_TYPE', 'social-t1-user-profile', 'Wrong Type', 'Type coercion accepts number instead of string for displayName', 'FLAG{WRONG_TYPE_9c1f3a5b}', 75, 'Medium', 2, true),
('social-t1-user-profile-OVERFLOW_MAXLENGTH', 'social-t1-user-profile', 'Overflow MaxLength', 'maxLength: 160 constraint not enforced on bio', 'FLAG{OVERFLOW_MAXLENGTH_2e7d4c6f}', 50, 'Easy', 3, true),
('social-t1-user-profile-MASS_ASSIGNMENT', 'social-t1-user-profile', 'Mass Assignment', 'Protected field isVerified can be modified by user', 'FLAG{MASS_ASSIGNMENT_6a8b2c4d}', 100, 'Hard', 4, true),

-- Mission 2: Posts API (4 flags)
('social-t1-posts-EMPTY_CONTENT', 'social-t1-posts', 'Empty Content', 'minLength: 1 not enforced, empty posts allowed', 'FLAG{EMPTY_CONTENT_3b5d7f9a}', 75, 'Medium', 1, true),
('social-t1-posts-INVALID_ENUM', 'social-t1-posts', 'Invalid Enum', 'Enum validation missing for visibility field', 'FLAG{INVALID_ENUM_6e8a2c4d}', 50, 'Easy', 2, true),
('social-t1-posts-OVERFLOW_ARRAY', 'social-t1-posts', 'Overflow Array', 'maxItems: 4 constraint not enforced for mediaUrls', 'FLAG{OVERFLOW_ARRAY_9f1b3d5e}', 75, 'Medium', 3, true),
('social-t1-posts-WRONG_DELETE_CODE', 'social-t1-posts', 'Wrong Delete Code', 'DELETE returns 200 OK instead of 204 No Content', 'FLAG{WRONG_DELETE_CODE_1a3c5e7b}', 100, 'Easy', 4, true),

-- Mission 3: Comments API (4 flags)
('social-t1-comments-ORPHAN_COMMENT', 'social-t1-comments', 'Orphan Comment', 'Foreign key constraint not enforced, comment created for non-existent post', 'FLAG{ORPHAN_COMMENT_4c6e8a2b}', 75, 'Medium', 1, true),
('social-t1-comments-WRONG_CREATE_CODE', 'social-t1-comments', 'Wrong Create Code', 'POST returns 200 instead of 201 Created', 'FLAG{WRONG_CREATE_CODE_2a4c6e8f}', 50, 'Easy', 2, true),
('social-t1-comments-INTEGER_OVERFLOW', 'social-t1-comments', 'Integer Overflow', 'Large integers in comment ID cause 500 error exposing internal details', 'FLAG{INTEGER_OVERFLOW_5b7d9f1a}', 75, 'Medium', 3, true),
('social-t1-comments-EXTRA_FIELDS', 'social-t1-comments', 'Extra Fields', 'Extra fields blindly accepted and stored (loose parsing)', 'FLAG{EXTRA_FIELDS_8c2e4a6b}', 100, 'Medium', 4, true),

-- Mission 4: Feed & Social Graph API (5 flags)
('social-t1-feed-social-MISSING_AUTH', 'social-t1-feed-social', 'Missing Auth', 'Feed endpoint accessible without authentication', 'FLAG{MISSING_AUTH_4b6d8e2a}', 100, 'Hard', 1, true),
('social-t1-feed-social-INVALID_QUERY_ENUM', 'social-t1-feed-social', 'Invalid Query Enum', 'Query parameter filter enum not validated', 'FLAG{INVALID_QUERY_ENUM_7c9e1a3b}', 50, 'Easy', 2, true),
('social-t1-feed-social-LIMIT_OVERFLOW', 'social-t1-feed-social', 'Limit Overflow', 'maximum: 100 constraint not enforced on limit parameter', 'FLAG{LIMIT_OVERFLOW_2d4f6b8a}', 75, 'Medium', 3, true),
('social-t1-feed-social-FOLLOW_SELF', 'social-t1-feed-social', 'Follow Self', 'Self-follow business rule not enforced', 'FLAG{FOLLOW_SELF_3a5c7e9b}', 75, 'Easy', 4, true),
('social-t1-feed-social-FOLLOW_DUPLICATE', 'social-t1-feed-social', 'Follow Duplicate', 'Duplicate follows allowed, no unique constraint', 'FLAG{FOLLOW_DUPLICATE_6b8d2f4a}', 100, 'Medium', 5, true)

ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    flag = EXCLUDED.flag,
    points = EXCLUDED.points,
    difficulty = EXCLUDED.difficulty,
    sort_order = EXCLUDED.sort_order,
    active = EXCLUDED.active;

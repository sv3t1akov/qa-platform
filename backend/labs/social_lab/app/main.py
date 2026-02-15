"""
Social Media T1 Lab: User Profile, Posts, Comments, Feed & Social Graph API
==========================================================================
4 missions, 17 bugs. One FastAPI app.
Based on SOCIAL_T1_INTERNAL_FLAGS.md and SOCIAL_T1_STUDENT_THEORY.md
"""
import os
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any, Union

from fastapi import FastAPI, HTTPException, Query, Path, Body, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from app.flags_registry import get_flag, FLAGS

# ═══════════════════════════════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════════════════════════════
class Settings:
    PORT: int = int(os.getenv("PORT", "8080"))
    MISSION_ID: str = os.getenv("MISSION_ID", "social-t1-lab")
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "true").lower() == "true"

settings = Settings()

# ═══════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS (permissive for bug triggers)
# ═══════════════════════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

class UserUpdate(BaseModel):
    displayName: Optional[Union[str, int, float, bool]] = None
    bio: Optional[str] = None
    website: Optional[str] = None
    isVerified: Optional[bool] = None  # Protected - mass assignment bug

class PostCreate(BaseModel):
    content: Optional[str] = None
    visibility: Optional[str] = "public"
    mediaUrls: Optional[List[str]] = None

class CommentCreate(BaseModel):
    content: Optional[str] = None
    likesCount: Optional[int] = None  # Extra field - strict parsing bug
    isPinned: Optional[bool] = None  # Extra field

# ═══════════════════════════════════════════════════════════════════════════
# IN-MEMORY DATABASE
# ═══════════════════════════════════════════════════════════════════════════

class Database:
    def __init__(self):
        self.users: Dict[str, dict] = {}
        self.posts: Dict[str, dict] = {}
        self.comments: Dict[str, dict] = {}
        self.follows: Dict[tuple, dict] = {}  # (follower_id, following_id) -> {}
        self.user_counter = 1
        self.post_counter = 1
        self.comment_counter = 1
        self._seed()

    def _seed(self):
        # 10+ users
        for i in range(1, 12):
            uid = f"user-{i}"
            self.users[uid] = {
                "id": uid,
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "displayName": f"User {i}",
                "bio": f"Bio for user {i}"[:80],
                "website": f"https://user{i}.example.com",
                "isVerified": i <= 3,  # First 3 verified
            }

        # 30+ posts
        for i in range(1, 35):
            pid = f"post-{i}"
            author_id = f"user-{(i % 10) + 1}"
            self.posts[pid] = {
                "id": pid,
                "authorId": author_id,
                "content": f"Post content {i} - Lorem ipsum dolor sit amet.",
                "visibility": ["public", "friends", "private"][i % 3],
                "mediaUrls": [f"https://cdn.example.com/{i}.jpg"] if i % 4 == 0 else [],
                "createdAt": "2026-02-13T10:00:00Z",
            }

        # 50+ comments
        for i in range(1, 55):
            cid = f"comment-{i}"
            post_id = f"post-{(i % 20) + 1}"
            author_id = f"user-{(i % 10) + 1}"
            self.comments[cid] = {
                "id": cid,
                "postId": post_id,
                "authorId": author_id,
                "content": f"Comment {i}",
                "likesCount": i % 5,
                "isPinned": False,
                "createdAt": "2026-02-13T10:00:00Z",
            }

        # Follows: user-1 follows user-2, user-3; user-2 follows user-1 (for FOLLOW_DUPLICATE test)
        for (f, t) in [(1, 2), (1, 3), (2, 1), (2, 3), (3, 1), (4, 5), (5, 4)]:
            self.follows[(f"user-{f}", f"user-{t}")] = {"createdAt": "2026-02-13T10:00:00Z"}

    def create_user(self, username: Optional[str], email: str, password: str) -> dict:
        uid = f"user-new-{self.user_counter}"
        self.user_counter += 1
        user = {
            "id": uid,
            "username": username,
            "email": email,
            "displayName": username or "",
            "bio": "",
            "website": "",
            "isVerified": False,
        }
        self.users[uid] = user
        return user

    def update_user(self, user_id: str, data: dict) -> dict:
        if user_id not in self.users:
            return {}
        self.users[user_id].update({k: v for k, v in data.items() if v is not None})
        return self.users[user_id]

    def get_user(self, user_id: str) -> Optional[dict]:
        return self.users.get(user_id)

    def create_post(self, author_id: str, content: str, visibility: str, media_urls: List[str]) -> dict:
        pid = f"post-{self.post_counter}"
        self.post_counter += 1
        post = {
            "id": pid,
            "authorId": author_id,
            "content": content,
            "visibility": visibility,
            "mediaUrls": media_urls or [],
            "createdAt": "2026-02-13T10:00:00Z",
        }
        self.posts[pid] = post
        return post

    def delete_post(self, post_id: str) -> bool:
        if post_id in self.posts:
            del self.posts[post_id]
            return True
        return False

    def get_post(self, post_id: str) -> Optional[dict]:
        return self.posts.get(post_id)

    def create_comment(self, post_id: str, author_id: str, content: str, extra: dict = None) -> dict:
        cid = f"comment-{self.comment_counter}"
        self.comment_counter += 1
        comment = {
            "id": cid,
            "postId": post_id,
            "authorId": author_id,
            "content": content,
            "likesCount": 0,
            "isPinned": False,
            "createdAt": "2026-02-13T10:00:00Z",
        }
        if extra:
            comment.update(extra)
        self.comments[cid] = comment
        return comment

    def get_comment(self, comment_id: str) -> Optional[dict]:
        return self.comments.get(comment_id)

    def add_follow(self, follower_id: str, following_id: str) -> Optional[dict]:
        key = (follower_id, following_id)
        if key in self.follows:
            return None  # Already exists
        self.follows[key] = {"createdAt": "2026-02-13T10:00:00Z"}
        return {"followerId": follower_id, "followingId": following_id, "createdAt": self.follows[key]["createdAt"]}

    def get_feed_posts(self, user_id: str, limit: int = 20, filter_type: str = "all") -> List[dict]:
        # Simple feed: posts from followed users + own
        followed = {t for (f, t) in self.follows if f == user_id}
        followed.add(user_id)
        posts = [p for p in self.posts.values() if p["authorId"] in followed]
        posts.sort(key=lambda x: x["createdAt"], reverse=True)
        return posts[:limit]

db = Database()

# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def get_current_user_id(authorization: Optional[str] = Header(None, alias="Authorization")) -> str:
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "").strip()
        if token.startswith("user-") and token in db.users:
            return token
        if token in db.users:
            return token
    return "user-1"

# ═══════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Social T1 Lab starting (17 active flags)")
    yield
    print("Social T1 Lab shutdown")

app = FastAPI(title="Social T1 Lab", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health():
    return {"status": "healthy", "mission": settings.MISSION_ID, "bugs": 17}

# ═══════════════════════════════════════════════════════════════════════════
# MISSION 1: User Profile API
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/v1/users")
async def create_user(data: UserCreate = Body(...)):
    """
    Create user. Bug: MISSING_REQUIRED - username not validated.
    """
    # MISSING_REQUIRED: username missing but accepted
    if (data.username is None or data.username == "") and data.email and data.password:
        user = db.create_user(username=None, email=data.email, password=data.password)
        return JSONResponse(status_code=200, content={
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "flag": get_flag("MISSING_REQUIRED"),
            "_debug": {
                "vulnerability": "Required field 'username' not validated on server",
                "lesson": "Server must validate ALL required fields, never trust client validation",
                "prevention": "Implement server-side schema validation with required: [username, email, password]",
            },
        })
    if not data.username or not data.email or not data.password:
        raise HTTPException(status_code=400, detail="username, email, password required")
    user = db.create_user(data.username, data.email, data.password)
    return JSONResponse(status_code=201, content=user)

@app.get("/api/v1/users/me")
async def get_me(authorization: Optional[str] = Header(None, alias="Authorization")):
    user_id = get_current_user_id(authorization)
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/api/v1/users/me")
async def update_me(
    data: UserUpdate = Body(...),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Update profile. Bugs: WRONG_TYPE, OVERFLOW_MAXLENGTH, MASS_ASSIGNMENT.
    """
    user_id = get_current_user_id(authorization)
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # MASS_ASSIGNMENT: isVerified (protected field) accepted
    if data.isVerified is not None:
        user = db.update_user(user_id, {"displayName": data.displayName or user.get("displayName"), "isVerified": data.isVerified})
        return {
            **user,
            "flag": get_flag("MASS_ASSIGNMENT"),
            "_debug": {
                "vulnerability": "Protected field 'isVerified' can be modified by user",
                "lesson": "Use allowlist of updatable fields, not blocklist",
                "prevention": "Define explicit DTO: allowed_fields = ['displayName', 'bio', 'website']",
            },
        }

    # WRONG_TYPE: displayName as number
    if data.displayName is not None and not isinstance(data.displayName, str):
        user = db.update_user(user_id, {"displayName": str(data.displayName)})
        return {
            **user,
            "flag": get_flag("WRONG_TYPE"),
            "_debug": {
                "vulnerability": "Type coercion accepts number instead of string",
                "lesson": "Strict type validation prevents unexpected behavior and potential vulnerabilities",
                "prevention": "Use JSON schema validation with strict type checking",
            },
        }

    # OVERFLOW_MAXLENGTH: bio > 160
    if data.bio is not None and len(data.bio) > 160:
        user = db.update_user(user_id, {"bio": data.bio})
        return {
            **user,
            "flag": get_flag("OVERFLOW_MAXLENGTH"),
            "_debug": {
                "vulnerability": "maxLength: 160 constraint not enforced on server",
                "lesson": "All documented constraints must be validated server-side",
                "prevention": "Add maxLength validation: if len(bio) > 160: raise ValidationError()",
            },
        }

    update_data = {}
    if data.displayName is not None:
        update_data["displayName"] = str(data.displayName)
    if data.bio is not None:
        update_data["bio"] = data.bio[:160]
    if data.website is not None:
        update_data["website"] = data.website
    user = db.update_user(user_id, update_data)
    return user

# ═══════════════════════════════════════════════════════════════════════════
# MISSION 2: Posts API
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/v1/posts")
async def create_post(
    data: PostCreate = Body(...),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Create post. Bugs: EMPTY_CONTENT, INVALID_ENUM, OVERFLOW_ARRAY.
    """
    user_id = get_current_user_id(authorization)

    # EMPTY_CONTENT: content empty
    if data.content is not None and data.content == "":
        post = db.create_post(user_id, "", "public", data.mediaUrls or [])
        return {
            **post,
            "flag": get_flag("EMPTY_CONTENT"),
            "_debug": {
                "vulnerability": "minLength: 1 not enforced, empty posts allowed",
                "lesson": "Empty content creates broken UX and potential spam/abuse vectors",
                "prevention": "Validate: if len(content.strip()) < 1: raise ValidationError()",
            },
        }

    # INVALID_ENUM: visibility not in [public, friends, private]
    allowed_visibility = {"public", "friends", "private"}
    if data.visibility is not None and data.visibility not in allowed_visibility:
        post = db.create_post(user_id, data.content or "Test", data.visibility, data.mediaUrls or [])
        return {
            **post,
            "flag": get_flag("INVALID_ENUM"),
            "_debug": {
                "vulnerability": "Enum validation missing, arbitrary values accepted",
                "lesson": "Enum fields must be validated against allowed values",
                "prevention": "ALLOWED_VISIBILITY = {'public', 'friends', 'private'}; validate visibility in ALLOWED_VISIBILITY",
            },
        }

    # OVERFLOW_ARRAY: mediaUrls > 4
    if data.mediaUrls and len(data.mediaUrls) > 4:
        post = db.create_post(user_id, data.content or "Post with images", data.visibility or "public", data.mediaUrls)
        return {
            **post,
            "flag": get_flag("OVERFLOW_ARRAY"),
            "_debug": {
                "vulnerability": "maxItems: 4 constraint not enforced",
                "lesson": "Array limits prevent resource exhaustion and storage abuse",
                "prevention": "Validate: if len(mediaUrls) > 4: raise ValidationError()",
            },
        }

    if not data.content or len(data.content.strip()) < 1:
        raise HTTPException(status_code=400, detail="content required, min 1 character")
    post = db.create_post(user_id, data.content, data.visibility or "public", data.mediaUrls or [])
    return JSONResponse(status_code=201, content=post)

@app.delete("/api/v1/posts/{post_id}")
async def delete_post(
    post_id: str = Path(...),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Delete post. Bug: WRONG_DELETE_CODE - returns 200 instead of 204.
    """
    user_id = get_current_user_id(authorization)
    post = db.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post["authorId"] != user_id:
        raise HTTPException(status_code=403, detail="Not your post")
    db.delete_post(post_id)
    # WRONG_DELETE_CODE: 200 instead of 204
    return JSONResponse(status_code=200, content={
        "message": "Post deleted",
        "flag": get_flag("WRONG_DELETE_CODE"),
        "_debug": {
            "vulnerability": "DELETE returns 200 OK instead of 204 No Content",
            "lesson": "HTTP semantics matter - 204 means success with no response body",
            "prevention": "Return status code 204 for successful DELETE operations",
        },
    })

# ═══════════════════════════════════════════════════════════════════════════
# MISSION 3: Comments API
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/v1/posts/{post_id}/comments")
async def create_comment(
    post_id: str = Path(...),
    data: CommentCreate = Body(...),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Create comment. Bugs: ORPHAN_COMMENT, WRONG_CREATE_CODE, EXTRA_FIELDS.
    """
    user_id = get_current_user_id(authorization)

    # ORPHAN_COMMENT: post does not exist
    if not db.get_post(post_id):
        comment = db.create_comment(post_id, user_id, data.content or "Comment on nothing")
        return JSONResponse(status_code=200, content={
            **comment,
            "flag": get_flag("ORPHAN_COMMENT"),
            "_debug": {
                "vulnerability": "Foreign key constraint not enforced at API level",
                "lesson": "Always validate parent resource exists before creating child",
                "prevention": "Check: post = Post.find(postId); if not post: raise NotFoundError()",
            },
        })

    # EXTRA_FIELDS: likesCount, isPinned in body
    extra = {}
    if data.likesCount is not None:
        extra["likesCount"] = data.likesCount
    if data.isPinned is not None:
        extra["isPinned"] = data.isPinned
    if extra:
        comment = db.create_comment(post_id, user_id, data.content or "Normal comment", extra)
        return JSONResponse(status_code=200, content={
            **comment,
            "flag": get_flag("EXTRA_FIELDS"),
            "_debug": {
                "vulnerability": "Extra fields blindly accepted and stored (loose parsing)",
                "lesson": "Strict parsing prevents mass assignment and data corruption",
                "prevention": "Use additionalProperties: false in JSON schema or explicit allowlist",
            },
        })

    if not data.content or len(data.content.strip()) < 1:
        raise HTTPException(status_code=400, detail="content required")
    comment = db.create_comment(post_id, user_id, data.content)
    # WRONG_CREATE_CODE: 200 instead of 201
    return JSONResponse(status_code=200, content={
        **comment,
        "flag": get_flag("WRONG_CREATE_CODE"),
        "_debug": {
            "vulnerability": "POST returns 200 instead of 201 Created",
            "lesson": "201 Created indicates new resource was created, 200 is for retrieval/update",
            "prevention": "Return status code 201 and Location header for POST creating resources",
        },
    })

@app.get("/api/v1/comments/{comment_id}")
async def get_comment(
    comment_id: str = Path(...),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Get comment. Bug: INTEGER_OVERFLOW - huge ID causes 500.
    """
    # INTEGER_OVERFLOW: comment_id as huge integer (path param comes as str, but we check numeric)
    try:
        if comment_id.isdigit() and int(comment_id) > 2147483647:
            return JSONResponse(status_code=500, content={
                "error": "Internal Server Error",
                "message": "integer out of range",
                "stack": f'ERROR: value "{comment_id}" is out of range for type integer',
                "flag": get_flag("INTEGER_OVERFLOW"),
                "_debug": {
                    "vulnerability": "Large integers crash database query, exposing internal errors",
                    "lesson": "Validate input range before database operations",
                    "prevention": "Validate: if id > MAX_INT (2147483647): raise ValidationError()",
                },
            })
    except (ValueError, OverflowError):
        pass

    comment = db.get_comment(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment

# ═══════════════════════════════════════════════════════════════════════════
# MISSION 4: Feed & Social Graph API
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/feed")
async def get_feed(
    filter: str = Query("all", alias="filter"),
    limit: int = Query(20, ge=1),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Get feed. Bugs: MISSING_AUTH, INVALID_QUERY_ENUM, LIMIT_OVERFLOW.
    """
    # MISSING_AUTH: no Authorization header
    if not authorization or not authorization.startswith("Bearer "):
        posts = db.get_feed_posts("user-1", limit=min(limit, 50), filter_type=filter)
        return {
            "data": posts,
            "flag": get_flag("MISSING_AUTH"),
            "_debug": {
                "vulnerability": "Authentication middleware not applied to /feed endpoint",
                "lesson": "Protected endpoints must verify auth on every request",
                "prevention": "Add @require_auth decorator or authentication middleware to route",
            },
        }

    user_id = get_current_user_id(authorization)

    # INVALID_QUERY_ENUM: filter not in [all, photos, videos]
    allowed_filter = {"all", "photos", "videos"}
    if filter not in allowed_filter:
        posts = db.get_feed_posts(user_id, limit=20, filter_type=filter)
        return {
            "data": posts,
            "appliedFilter": filter,
            "flag": get_flag("INVALID_QUERY_ENUM"),
            "_debug": {
                "vulnerability": "Query parameter enum not validated",
                "lesson": "All inputs including query params need validation",
                "prevention": "Validate: if filter not in ['all', 'photos', 'videos']: raise ValidationError()",
            },
        }

    # LIMIT_OVERFLOW: limit > 100
    if limit > 100:
        posts = db.get_feed_posts(user_id, limit=limit, filter_type=filter)
        return {
            "data": posts,
            "pagination": {"limit": limit, "returnedCount": len(posts)},
            "flag": get_flag("LIMIT_OVERFLOW"),
            "_debug": {
                "vulnerability": "maximum: 100 constraint not enforced on limit parameter",
                "lesson": "Unbounded limits enable DoS attacks and resource exhaustion",
                "prevention": "Cap limit: limit = min(requested_limit, MAX_LIMIT)",
            },
        }

    posts = db.get_feed_posts(user_id, limit=limit, filter_type=filter)
    return {"data": posts, "pagination": {"limit": limit, "returnedCount": len(posts)}}

@app.post("/api/v1/users/{user_id}/follow")
async def follow_user(
    user_id: str = Path(...),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Follow user. Bugs: FOLLOW_SELF, FOLLOW_DUPLICATE.
    """
    follower_id = get_current_user_id(authorization)
    if not db.get_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    # FOLLOW_SELF: follow self
    if follower_id == user_id:
        db.follows[(follower_id, user_id)] = {"createdAt": "2026-02-13T10:00:00Z"}
        return {
            "followerId": follower_id,
            "followingId": user_id,
            "createdAt": "2026-02-13T10:00:00Z",
            "flag": get_flag("FOLLOW_SELF"),
            "_debug": {
                "vulnerability": "Self-follow business rule not enforced",
                "lesson": "Business rules must be validated at API level",
                "prevention": "Check: if follower_id == following_id: raise BusinessError('Cannot follow yourself')",
            },
        }

    # FOLLOW_DUPLICATE: already following
    key = (follower_id, user_id)
    if key in db.follows:
        return {
            "followerId": follower_id,
            "followingId": user_id,
            "createdAt": db.follows[key]["createdAt"],
            "duplicateEntry": True,
            "flag": get_flag("FOLLOW_DUPLICATE"),
            "_debug": {
                "vulnerability": "Duplicate follows allowed, no unique constraint",
                "lesson": "Unique constraints prevent data corruption and inflated metrics",
                "prevention": "Add UNIQUE(follower_id, following_id) to database and check before insert",
            },
        }

    result = db.add_follow(follower_id, user_id)
    return JSONResponse(status_code=201, content=result)

# ═══════════════════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)

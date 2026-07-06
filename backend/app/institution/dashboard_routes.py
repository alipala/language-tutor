"""
Enhanced Institution Dashboard APIs
Provides analytics, tutor management, and learner management
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId
from io import StringIO, BytesIO
import csv
import secrets
import string

from app.config.feature_flags import feature_flags
from database import database
from auth import create_access_token, SECRET_KEY, ALGORITHM
from redis_client import blocklist_token, is_token_blocklisted


def _generate_temp_password(length: int = 12) -> str:
    """
    Generate a strong, human-shareable temporary password for a newly created
    tutor. Guarantees at least one lower, one upper and one digit so it always
    passes validate_password_strength() (which the tutor must satisfy when they
    change it too). Excludes ambiguous chars (O/0, l/1/I) for legibility.
    """
    lowers = "abcdefghjkmnpqrstuvwxyz"
    uppers = "ABCDEFGHJKMNPQRSTUVWXYZ"
    digits = "23456789"
    pool = lowers + uppers + digits
    # Guarantee category coverage, then fill the rest, then shuffle.
    chars = [
        secrets.choice(lowers),
        secrets.choice(uppers),
        secrets.choice(digits),
    ]
    chars += [secrets.choice(pool) for _ in range(max(0, length - len(chars)))]
    # Fisher–Yates shuffle with secrets for unbiased ordering.
    for i in range(len(chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        chars[i], chars[j] = chars[j], chars[i]
    return "".join(chars)

# ---------------------------------------------------------------------------
# SHARED IMPORT HELPER
# ---------------------------------------------------------------------------
# Column-name aliases: maps every common variant → our canonical field name.
# Matching is case-insensitive and strips whitespace.
_LEARNER_ALIASES: Dict[str, str] = {
    # name
    "name": "name", "full name": "name", "fullname": "name",
    "student name": "name", "learner name": "name",
    "first name": "first_name", "firstname": "first_name", "given name": "first_name",
    "last name": "last_name", "lastname": "last_name", "surname": "last_name",
    "family name": "last_name",
    # email
    "email": "email", "e-mail": "email", "email address": "email",
    "student email": "email", "learner email": "email",
    # language
    "language": "language", "target language": "language", "learning language": "language",
    # level
    "level": "level", "cefr level": "level", "proficiency level": "level",
    "proficiency": "level",
    # tutor
    "tutor_email": "tutor_email", "tutor email": "tutor_email",
    "assigned tutor": "tutor_email", "teacher email": "tutor_email",
}

_TUTOR_ALIASES: Dict[str, str] = {
    # name
    "name": "name", "full name": "name", "fullname": "name",
    "tutor name": "name", "teacher name": "name",
    "first name": "first_name", "firstname": "first_name", "given name": "first_name",
    "last name": "last_name", "lastname": "last_name", "surname": "last_name",
    "family name": "last_name",
    # email
    "email": "email", "e-mail": "email", "email address": "email",
    "tutor email": "email", "teacher email": "email",
    # languages taught (comma-separated) — the only optional column for tutors
    "languages": "languages", "language": "languages", "languages taught": "languages",
    "teaches": "languages", "teaching languages": "languages",
}


def _normalise_row(raw: Dict[str, str], aliases: Dict[str, str]) -> Dict[str, str]:
    """Map raw CSV/XLSX column headers to canonical field names."""
    result: Dict[str, str] = {}
    for key, value in raw.items():
        canonical = aliases.get((key or "").strip().lower())
        if canonical:
            result[canonical] = (value or "").strip()
    # Merge first_name + last_name → name if name absent
    if "name" not in result and ("first_name" in result or "last_name" in result):
        parts = [result.pop("first_name", ""), result.pop("last_name", "")]
        result["name"] = " ".join(p for p in parts if p)
    return result


async def _parse_import_file(
    file: UploadFile,
    aliases: Dict[str, str]
) -> List[Dict[str, str]]:
    """
    Read a CSV or XLSX upload and return a list of normalised row dicts.
    Raises HTTPException(400) on bad format or encoding issues.
    """
    contents: bytes = await file.read()
    filename = (file.filename or "").lower()

    rows: List[Dict[str, str]] = []

    # ── XLSX ────────────────────────────────────────────────────────────────
    if filename.endswith(".xlsx") or filename.endswith(".xls") or \
            file.content_type in (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel",
            ):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(BytesIO(contents), read_only=True, data_only=True)
            ws = wb.active
            all_rows = list(ws.iter_rows(values_only=True))
            if not all_rows:
                raise HTTPException(status_code=400, detail="Excel file is empty")
            # Row 0 = headers
            headers = [str(h).strip() if h is not None else "" for h in all_rows[0]]
            for row_values in all_rows[1:]:
                raw = {headers[i]: str(v).strip() if v is not None else ""
                       for i, v in enumerate(row_values) if i < len(headers)}
                if any(v for v in raw.values()):   # skip blank rows
                    rows.append(_normalise_row(raw, aliases))
            wb.close()
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not read Excel file: {exc}")

    # ── CSV ─────────────────────────────────────────────────────────────────
    else:
        for encoding in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                text = contents.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise HTTPException(status_code=400, detail="Could not decode file — please save as UTF-8 CSV")

        # Detect delimiter (comma or semicolon — common in European locales)
        sample = text[:2048]
        delimiter = ";" if sample.count(";") > sample.count(",") else ","

        reader = csv.DictReader(StringIO(text), delimiter=delimiter)
        for row in reader:
            if any(v.strip() for v in row.values()):
                rows.append(_normalise_row(dict(row), aliases))

    return rows

router = APIRouter(prefix="/institution/dashboard", tags=["institution-dashboard"])
_bearer = HTTPBearer(auto_error=False)

def check_feature_enabled():
    """Check if institutional features are enabled"""
    if not feature_flags.INSTITUTIONAL_FEATURES_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="Institutional features are not enabled"
        )


async def get_current_institution_admin(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> Dict[str, Any]:
    """
    Institution-admin identity guard for sensitive dashboard actions.

    Decodes the institution-admin JWT (minted at /institution/login with
    {sub: admin_email, institution_id, role: "admin", jti}), rejects blocklisted
    (logged-out) tokens, and requires role == "admin". Returns the claims so the
    caller can enforce tenant isolation (institution_id must match the path).

    NOTE: most /institution/dashboard/* routes are currently guarded ONLY by the
    feature flag (a known multi-tenant authz gap). New/sensitive assignment
    endpoints use THIS guard so they can't be abused cross-tenant.
    """
    from jose import jwt as jose_jwt, JWTError

    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jose_jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    jti = payload.get("jti")
    if jti and await is_token_blocklisted(jti):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    if payload.get("role") != "admin" or not payload.get("institution_id"):
        raise HTTPException(status_code=403, detail="Institution admin access required")

    return payload


def _require_tenant(admin: Dict[str, Any], institution_id: str) -> None:
    """Enforce that the authenticated admin owns the institution in the path.
    Prevents reading/writing another school's data by iterating institution_id."""
    if str(admin.get("institution_id")) != str(institution_id):
        raise HTTPException(status_code=403, detail="You cannot manage another institution")


async def verify_institution_admin(
    institution_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> Dict[str, Any]:
    """
    Combined identity + tenant guard for use in a route's `dependencies=[...]`
    list — WITHOUT touching the endpoint's own signature.

    FastAPI injects the path's `{institution_id}` here automatically, so we can
    (1) authenticate the institution-admin JWT and (2) enforce that the admin owns
    THAT institution, on every route, by only editing the decorator. Closes the
    multi-tenant authz gap across the whole dashboard.
    """
    admin = await get_current_institution_admin(credentials)
    _require_tenant(admin, institution_id)
    return admin


@router.post("/logout", dependencies=[Depends(check_feature_enabled)])  # logout has no {institution_id}; identity is verified inside the handler by decoding + blocklisting the token
async def institution_logout(credentials: HTTPAuthorizationCredentials = Depends(_bearer)):
    """Invalidate institution JWT by adding its JTI to the Redis blocklist."""
    from jose import jwt as jose_jwt, JWTError
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jose_jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and exp:
            remaining_ttl = max(1, int(exp - datetime.utcnow().timestamp()))
            await blocklist_token(jti, remaining_ttl)
    except JWTError as e:
        print(f"[INSTITUTION_LOGOUT] Warning: could not decode token: {e}")
    return {"message": "Logged out successfully"}


# ============================================================================
# ANALYTICS APIs
# ============================================================================

@router.get("/{institution_id}/analytics/language-distribution",
            dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def get_language_distribution(institution_id: str) -> Dict[str, Any]:
    """
    Get language distribution of learners in the institution
    """
    try:
        # Get all active learners for this institution
        learners = await database.institutional_learners.find({
            "institution_id": institution_id,
            "is_active": True
        }).to_list(length=None)
        
        # Get user IDs
        user_ids = [l["user_id"] for l in learners if l.get("user_id")]
        
        if not user_ids:
            return {
                "total_learners": 0,
                "distribution": []
            }
        
        # Aggregate language distribution from learning plans with case normalization
        pipeline = [
            {"$match": {"user_id": {"$in": user_ids}}},
            {"$group": {
                "_id": {"$toLower": "$language"},  # Normalize to lowercase
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        results = await database.learning_plans.aggregate(pipeline).to_list(length=None)
        
        # Format results
        distribution = []
        total = 0
        for result in results:
            language = result["_id"]
            if language:  # Skip None values
                count = result["count"]
                total += count
                distribution.append({
                    "language": language.capitalize(),  # Capitalize first letter
                    "count": count
                })
        
        # Add percentages
        for item in distribution:
            item["percentage"] = round((item["count"] / total * 100), 1) if total > 0 else 0
        
        return {
            "total_learners": total,
            "distribution": distribution
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get language distribution: {str(e)}")


@router.get("/{institution_id}/analytics/level-distribution",
            dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def get_level_distribution(institution_id: str) -> Dict[str, Any]:
    """
    Get proficiency level distribution of learners
    """
    try:
        # Get all active learners for this institution
        learners = await database.institutional_learners.find({
            "institution_id": institution_id,
            "is_active": True
        }).to_list(length=None)
        
        # Get user IDs
        user_ids = [l["user_id"] for l in learners if l.get("user_id")]
        
        if not user_ids:
            return {
                "total_learners": 0,
                "distribution": []
            }
        
        # Aggregate level distribution from learning plans
        pipeline = [
            {"$match": {"user_id": {"$in": user_ids}}},
            {"$group": {
                "_id": "$proficiency_level",
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        results = await database.learning_plans.aggregate(pipeline).to_list(length=None)
        
        # Format results with proper ordering
        level_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
        distribution = []
        total = 0
        
        for level in level_order:
            matching = [r for r in results if r["_id"] == level]
            if matching:
                count = matching[0]["count"]
                total += count
                distribution.append({
                    "level": level,
                    "count": count
                })
        
        # Add percentages
        for item in distribution:
            item["percentage"] = round((item["count"] / total * 100), 1) if total > 0 else 0
        
        return {
            "total_learners": total,
            "distribution": distribution
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get level distribution: {str(e)}")


# ============================================================================
# TUTOR MANAGEMENT APIs
# ============================================================================

@router.get("/{institution_id}/tutors",
            dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def get_tutors(institution_id: str) -> Dict[str, Any]:
    """
    Get all tutors for an institution with their assigned learners (including inactive)
    OPTIMIZED: Uses aggregation pipeline to avoid N+1 queries
    """
    try:
        # Single aggregation pipeline - MUCH faster!
        # NOTE: Returns ALL tutors (active and inactive)
        pipeline = [
            {
                "$match": {
                    "institution_id": institution_id
                }
            },
            {
                "$sort": {"created_at": -1}
            },
            {
                "$lookup": {
                    "from": "institutional_learners",
                    "let": {"tutor_id_str": {"$toString": "$_id"}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$tutor_id", "$$tutor_id_str"]},
                                        {"$eq": ["$is_active", True]},
                                        {"$eq": ["$institution_id", institution_id]}
                                    ]
                                }
                            }
                        },
                        {
                            "$lookup": {
                                "from": "users",
                                "let": {"user_id_str": "$user_id"},
                                "pipeline": [
                                    {
                                        "$match": {
                                            "$expr": {
                                                "$eq": [{"$toString": "$_id"}, "$$user_id_str"]
                                            }
                                        }
                                    }
                                ],
                                "as": "user_data"
                            }
                        },
                        {
                            "$unwind": {
                                "path": "$user_data",
                                "preserveNullAndEmptyArrays": False
                            }
                        }
                    ],
                    "as": "assigned_learners"
                }
            }
        ]
        
        tutors = await database.tutors.aggregate(pipeline).to_list(length=None)
        
        # Format results
        tutor_list = []
        for tutor in tutors:
            tutor_id = str(tutor["_id"])
            
            # Format learner details
            learner_details = []
            for learner in tutor.get("assigned_learners", []):
                user = learner.get("user_data", {})
                learner_details.append({
                    "user_id": str(user.get("_id", "")),
                    "name": user.get("name"),
                    "email": user.get("email"),
                    "language": user.get("preferred_language"),
                    "level": user.get("preferred_level"),
                    "enrolled_at": learner.get("enrolled_at")
                })
            
            tutor_list.append({
                "id": tutor_id,
                "name": tutor.get("name"),
                "email": tutor.get("email"),
                "bio": tutor.get("bio"),
                "specializations": tutor.get("specializations", []),
                "learner_count": len(learner_details),
                "learners": learner_details,
                "is_active": tutor.get("is_active", True),  # Include is_active field
                # Pending activation = created but hasn't set their own password yet.
                "pending_activation": bool(tutor.get("first_login", False) or tutor.get("must_reset_password", False)),
                "created_at": tutor.get("created_at")
            })
        
        return {
            "total_tutors": len(tutor_list),
            "tutors": tutor_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tutors: {str(e)}")


@router.post("/{institution_id}/tutors",
             dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def add_tutor(institution_id: str, tutor_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a single tutor to the institution.

    The system generates a strong temporary password (the admin does NOT choose
    one). It is returned ONCE in the response so the admin can pass it to the
    tutor; the tutor is forced to change it on first login (first_login +
    must_reset_password both True — kept in sync so login and the reset gate
    agree regardless of which flag downstream code reads).
    """
    try:
        from app.tutor.tutor_auth import get_password_hash

        # Validate required fields
        if not tutor_data.get("name") or not str(tutor_data.get("name")).strip():
            raise HTTPException(status_code=400, detail="Name is required")
        if not tutor_data.get("email") or not str(tutor_data.get("email")).strip():
            raise HTTPException(status_code=400, detail="Email is required")

        name = str(tutor_data["name"]).strip()
        email = str(tutor_data["email"]).strip().lower()

        # Check if tutor email already exists (global uniqueness on tutors.email)
        existing = await database.tutors.find_one({"email": email})
        if existing:
            raise HTTPException(status_code=400, detail="A tutor with this email already exists")

        # System-generated temporary password (shown once to the admin).
        temp_password = _generate_temp_password()
        hashed_password = get_password_hash(temp_password)

        now = datetime.utcnow()
        tutor = {
            "name": name,
            "email": email,
            "hashed_password": hashed_password,
            "first_login": True,          # must change on first login
            "must_reset_password": True,  # kept in sync with first_login
            "institution_id": institution_id,
            "bio": tutor_data.get("bio", "") or "",
            "qualifications": tutor_data.get("qualifications") or None,
            "specializations": tutor_data.get("specializations", []) or [],
            "languages": tutor_data.get("languages", []) or [],  # languages the tutor teaches (optional)
            "permissions": tutor_data.get("permissions", ["view_learners", "assign_tasks"]),
            "assigned_learners": [],
            "is_active": True,
            "enrollment_method": "manual_add",
            "created_at": now,
            "updated_at": now,
        }

        result = await database.tutors.insert_one(tutor)

        return {
            "message": "Tutor added successfully.",
            "tutor_id": str(result.inserted_id),
            # Returned ONCE — the admin shares it with the tutor.
            "temporary_password": temp_password,
            "tutor": {
                "id": str(result.inserted_id),
                "name": tutor["name"],
                "email": tutor["email"],
                "bio": tutor["bio"],
                "specializations": tutor["specializations"],
                "permissions": tutor["permissions"],
                "first_login": True,
                "created_at": now.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add tutor: {str(e)}")


@router.post("/{institution_id}/tutors/bulk-import",
             dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def bulk_import_tutors(
    institution_id: str,
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    """
    Bulk import tutors from CSV or Excel (.xlsx) file.
    Required columns : name (or first_name + last_name), email
    Optional columns : bio, qualifications, specializations (comma-separated)
    Column headers are matched case-insensitively with common aliases.
    Tutors receive a system-generated temporary password and must change it on
    first login (first_login + must_reset_password both True). The generated
    credentials (email + temp password) are returned so the admin can distribute
    them — they cannot be recovered later.
    """
    from app.tutor.tutor_auth import get_password_hash

    try:
        rows = await _parse_import_file(file, _TUTOR_ALIASES)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    success_count = 0
    skipped_count = 0
    failed_count  = 0
    errors: List[str] = []
    credentials: List[Dict[str, str]] = []  # email + temp password per created tutor

    for row_num, row in enumerate(rows, start=2):
        try:
            name  = row.get("name", "").strip()
            email = row.get("email", "").strip().lower()

            if not name or not email:
                errors.append(f"Row {row_num}: 'name' and 'email' are required")
                failed_count += 1
                continue

            # Skip duplicates — tutors.email is globally unique, so check globally
            # (matches the single-add path) to avoid an insert that would fail.
            if await database.tutors.find_one({"email": email}):
                skipped_count += 1
                continue

            raw_langs = row.get("languages", "")
            languages = [s.strip() for s in raw_langs.split(",") if s.strip()]

            temp_password = _generate_temp_password()

            await database.tutors.insert_one({
                "name": name,
                "email": email,
                "languages": languages,       # languages the tutor teaches (optional)
                "specializations": [],
                "institution_id": institution_id,
                "hashed_password": get_password_hash(temp_password),
                "first_login": True,
                "must_reset_password": True,
                "permissions": ["view_learners", "assign_tasks"],
                "assigned_learners": [],
                "is_active": True,
                "enrollment_method": "bulk_import",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })
            success_count += 1
            credentials.append({"name": name, "email": email, "temporary_password": temp_password})

        except Exception as exc:
            errors.append(f"Row {row_num}: unexpected error — {exc}")
            failed_count += 1

    return {
        "message": "Import completed",
        "success_count": success_count,
        "skipped_count": skipped_count,
        "failed_count": failed_count,
        "errors": errors[:20],
        "credentials": credentials,
    }


@router.get("/{institution_id}/tutors/export",
            dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def export_tutors(institution_id: str):
    """
    Export all active tutors for an institution as a downloadable CSV file.
    Columns: name, email, bio, qualifications, specializations, learner_count,
             is_active, created_at
    """
    from fastapi.responses import StreamingResponse

    try:
        tutors = await database.tutors.find(
            {"institution_id": institution_id}
        ).to_list(length=None)

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "name", "email", "bio", "qualifications", "specializations",
            "learner_count", "is_active", "created_at"
        ])

        for tutor in tutors:
            learner_count = await database.institutional_learners.count_documents({
                "tutor_id": str(tutor["_id"]),
                "institution_id": institution_id,
                "is_active": True
            })
            writer.writerow([
                tutor.get("name", ""),
                tutor.get("email", ""),
                tutor.get("bio") or "",
                tutor.get("qualifications") or "",
                ",".join(tutor.get("specializations") or []),
                learner_count,
                tutor.get("is_active", True),
                str(tutor.get("created_at", ""))
            ])

        output.seek(0)
        filename = f"tutors_{datetime.utcnow().strftime('%Y-%m-%d')}.csv"
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export tutors: {str(e)}")


@router.delete("/{institution_id}/tutors/{tutor_id}",
               dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def remove_tutor(institution_id: str, tutor_id: str) -> Dict[str, Any]:
    """
    Remove/deactivate a tutor (DEPRECATED - use deactivate_tutor instead)
    """
    try:
        # Deactivate tutor instead of deleting
        result = await database.tutors.update_one(
            {"_id": ObjectId(tutor_id), "institution_id": institution_id},
            {"$set": {"is_active": False, "deactivated_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Tutor not found")
        
        return {"message": "Tutor deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove tutor: {str(e)}")


@router.post("/{institution_id}/tutors/deactivate/{tutor_id}",
             dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def deactivate_tutor(institution_id: str, tutor_id: str) -> Dict[str, Any]:
    """
    Deactivate a tutor and unassign all their learners
    This is a reversible operation that:
    1. Marks the tutor as inactive (preserves account data)
    2. Unassigns all learners from this tutor (they become "Unassigned")
    3. Allows future reactivation
    """
    try:
        # 1. Deactivate the tutor
        tutor_result = await database.tutors.update_one(
            {"_id": ObjectId(tutor_id), "institution_id": institution_id},
            {"$set": {"is_active": False, "deactivated_at": datetime.utcnow()}}
        )
        
        if tutor_result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Tutor not found")
        
        # 2. Unassign all learners from this tutor
        learners_result = await database.institutional_learners.update_many(
            {
                "institution_id": institution_id,
                "tutor_id": tutor_id,
                "is_active": True
            },
            {
                "$set": {
                    "tutor_id": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        unassigned_count = learners_result.modified_count
        
        return {
            "message": "Tutor deactivated successfully",
            "unassigned_learners": unassigned_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deactivate tutor: {str(e)}")


@router.post("/{institution_id}/tutors/reactivate/{tutor_id}",
             dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def reactivate_tutor(institution_id: str, tutor_id: str) -> Dict[str, Any]:
    """
    Reactivate a previously deactivated tutor
    """
    try:
        result = await database.tutors.update_one(
            {"_id": ObjectId(tutor_id), "institution_id": institution_id},
            {
                "$set": {"is_active": True, "reactivated_at": datetime.utcnow()},
                "$unset": {"deactivated_at": ""}
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Tutor not found")
        
        return {"message": "Tutor reactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reactivate tutor: {str(e)}")


@router.post("/{institution_id}/tutors/{tutor_id}/reset-password",
             dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def reset_tutor_password(institution_id: str, tutor_id: str) -> Dict[str, Any]:
    """
    Admin-initiated tutor password reset.

    Generates a fresh temporary password (invalidating any previous one),
    re-arms the first-login gate (first_login + must_reset_password) and returns
    the new temp password ONCE so the admin can pass it to the tutor. Used when
    the tutor never received / forgot their initial credentials — we never store
    or re-show a plaintext password, we always mint a new one.
    """
    try:
        from app.tutor.tutor_auth import get_password_hash

        tutor = await database.tutors.find_one(
            {"_id": ObjectId(tutor_id), "institution_id": institution_id}
        )
        if not tutor:
            raise HTTPException(status_code=404, detail="Tutor not found")

        temp_password = _generate_temp_password()
        await database.tutors.update_one(
            {"_id": ObjectId(tutor_id), "institution_id": institution_id},
            {"$set": {
                "hashed_password": get_password_hash(temp_password),
                "first_login": True,
                "must_reset_password": True,
                "password_reset_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }},
        )

        return {
            "message": "Password reset successfully.",
            "temporary_password": temp_password,
            "tutor": {
                "id": str(tutor["_id"]),
                "name": tutor.get("name", ""),
                "email": tutor.get("email", ""),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset tutor password: {str(e)}")


@router.put("/{institution_id}/tutors/{tutor_id}/permissions",
            dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def update_tutor_permissions(
    institution_id: str,
    tutor_id: str,
    permissions: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update tutor permissions
    """
    try:
        result = await database.tutors.update_one(
            {"_id": ObjectId(tutor_id), "institution_id": institution_id},
            {"$set": {"permissions": permissions.get("permissions", [])}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Tutor not found")
        
        return {"message": "Permissions updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update permissions: {str(e)}")


# ============================================================================
# LEARNER MANAGEMENT APIs
# ============================================================================

@router.get("/{institution_id}/sponsored-learners",
            dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def get_sponsored_learners(institution_id: str) -> Dict[str, Any]:
    """
    Read-only list of students who redeemed THIS school's Stripe promo code.

    The school sets its promo code (e.g. "AMSTERDAMTAAL") in Settings; students
    redeem it in the mobile app at checkout, which Stripe attributes to the
    subscription. The webhook stamps `institution_promo.code` onto the user, and
    here we surface everyone whose active subscription carries that code. No
    enrollment records are created — the source of truth is Stripe.
    """
    from bson import ObjectId as OID
    try:
        inst = await database.institutions.find_one({"_id": OID(institution_id)})
        if not inst:
            raise HTTPException(status_code=404, detail="Institution not found")

        promo_code = (inst.get("promo_code") or "").strip().upper()
        max_learners = int(inst.get("max_learners", 0) or 0)

        learners: List[Dict[str, Any]] = []
        if promo_code:
            # Pre-load this school's enrollment rows + tutor names ONCE, so we can
            # annotate each sponsored learner with their enrollment/assignment
            # state without an N+1 query. Keyed by user_id.
            enroll_by_user: Dict[str, Dict[str, Any]] = {}
            async for e in database.institutional_learners.find({"institution_id": institution_id}):
                enroll_by_user[str(e.get("user_id"))] = e
            tutor_names: Dict[str, Dict[str, Any]] = {}
            async for t in database.tutors.find({"institution_id": institution_id}, {"name": 1, "email": 1}):
                tutor_names[str(t["_id"])] = {"id": str(t["_id"]), "name": t.get("name"), "email": t.get("email")}

            # Case-insensitive match on the stored redemption code.
            cursor = database.users.find(
                {"institution_promo.code": {"$regex": f"^{promo_code}$", "$options": "i"}},
                {
                    "name": 1, "email": 1, "subscription_plan": 1,
                    "subscription_status": 1, "subscription_period": 1,
                    "subscription_expires_at": 1, "institution_promo": 1,
                    "preferred_language": 1, "preferred_level": 1,
                },
            )
            async for u in cursor:
                uid = str(u["_id"])
                promo = u.get("institution_promo") or {}
                enrollment = enroll_by_user.get(uid)
                tutor = None
                if enrollment and enrollment.get("tutor_id"):
                    tutor = tutor_names.get(str(enrollment.get("tutor_id")))
                learners.append({
                    "id": uid,  # the user's id (kept for backward-compat)
                    "user_id": uid,
                    # institutional_learners._id — REQUIRED by the assign-tutor
                    # endpoint (which keys on the enrollment row _id, not user id).
                    "learner_id": str(enrollment["_id"]) if enrollment else None,
                    "enrolled": bool(enrollment),
                    "name": u.get("name", ""),
                    "email": u.get("email", ""),
                    "language": u.get("preferred_language"),
                    "level": u.get("preferred_level"),
                    "plan": u.get("subscription_plan"),
                    "status": u.get("subscription_status"),
                    "period": u.get("subscription_period"),
                    "expires_at": u.get("subscription_expires_at").isoformat()
                        if u.get("subscription_expires_at") else None,
                    "redeemed_at": promo.get("applied_at").isoformat()
                        if promo.get("applied_at") else None,
                    "tutor": tutor,  # {id,name,email} or None if unassigned
                })

        return {
            "promo_code": promo_code,
            "seats_used": len(learners),
            "max_learners": max_learners,
            "learners": learners,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{institution_id}/learners",
            dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def get_learners(institution_id: str) -> Dict[str, Any]:
    """
    Get all learners for an institution with progress data (including deactivated)
    OPTIMIZED: Uses aggregation pipeline to avoid N+1 queries
    """
    try:
        # Single aggregation pipeline - MUCH faster than N+1 queries!
        # NOTE: Returns ALL learners (active and inactive)
        pipeline = [
            {
                "$match": {
                    "institution_id": institution_id
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "let": {"user_id_str": "$user_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": [{"$toString": "$_id"}, "$$user_id_str"]
                                }
                            }
                        }
                    ],
                    "as": "user_data"
                }
            },
            {
                "$lookup": {
                    "from": "learning_plans",
                    "localField": "user_id",
                    "foreignField": "user_id",
                    "as": "learning_plan"
                }
            },
            {
                "$lookup": {
                    "from": "tutors",
                    "let": {"tutor_id_str": "$tutor_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": [{"$toString": "$_id"}, "$$tutor_id_str"]
                                }
                            }
                        }
                    ],
                    "as": "tutor_data"
                }
            },
            {
                "$unwind": {
                    "path": "$user_data",
                    "preserveNullAndEmptyArrays": False
                }
            }
        ]
        
        learners = await database.institutional_learners.aggregate(pipeline).to_list(length=None)
        
        learner_list = []
        for learner in learners:
            user = learner.get("user_data", {})
            
            # Get tutor info
            tutor = None
            tutor_data = learner.get("tutor_data", [])
            if tutor_data:
                tutor_doc = tutor_data[0]
                tutor = {
                    "id": str(tutor_doc["_id"]),
                    "name": tutor_doc.get("name"),
                    "email": tutor_doc.get("email")
                }
            
            # Get learning plan progress — use best (highest progress) plan
            progress = None
            learning_plans = learner.get("learning_plan", [])
            if learning_plans:
                learning_plan = max(learning_plans, key=lambda p: p.get("progress_percentage", 0))
                percentage = learning_plan.get("progress_percentage", 0)
                completed = learning_plan.get("completed_sessions", 0)
                total = learning_plan.get("total_sessions", 16)
                
                # Categorize progress
                if percentage < 15:
                    category = "Just Started"
                    color = "green"
                    emoji = "🟢"
                elif percentage < 35:
                    category = "Early Progress"
                    color = "blue"
                    emoji = "🔵"
                elif percentage < 60:
                    category = "Intermediate"
                    color = "yellow"
                    emoji = "🟡"
                elif percentage < 85:
                    category = "Advanced"
                    color = "orange"
                    emoji = "🟠"
                else:
                    category = "Nearly Complete"
                    color = "red"
                    emoji = "🔴"
                
                progress = {
                    "percentage": round(percentage, 1),
                    "completed_sessions": completed,
                    "total_sessions": total,
                    "category": category,
                    "color": color,
                    "emoji": emoji
                }
            
            learner_list.append({
                "id": str(learner["_id"]),
                "user_id": user.get("_id") if isinstance(user.get("_id"), str) else str(user.get("_id", "")),
                "name": user.get("name"),
                "email": user.get("email"),
                "language": user.get("preferred_language"),
                "level": user.get("preferred_level"),
                "tutor": tutor,
                "enrollment_method": learner.get("enrollment_method"),
                "consent_given": learner.get("consent_given", False),
                "enrolled_at": learner.get("enrolled_at"),
                "is_active": learner.get("is_active", True),
                "progress": progress
            })
        
        return {
            "total_learners": len(learner_list),
            "learners": learner_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learners: {str(e)}")


# ============================================================================
# LEARNER → TUTOR ASSIGNMENT (institution-admin managed)
# ============================================================================
# Business rules preserved (verified against the codebase):
#  - A sponsored learner = a user whose institution_promo.code matches this
#    school's promo_code. Only sponsored users of THIS school may be enrolled.
#  - institutional_learners is unique on (user_id, institution_id) → enroll is
#    an idempotent upsert.
#  - Promo redemption is an explicit action → consent_given=True, method
#    "promo_code" (mirrors self_signup's implicit consent).
#  - A tutor may only receive assignments if they belong to THIS institution and
#    is_active=True (matches learner/service.py enrollment checks).
#  - Assign is an upsert: enrolling + assigning in one call keeps the admin UX to
#    a single click, while still creating the row on the admin's explicit action.
#  - Tutor dashboard shows learners where tutor_id==<tutor> AND is_active=True,
#    so re-activation on assign guarantees visibility.
#  - Endpoints here enforce admin identity + tenant isolation (unlike the rest of
#    the dashboard, which is feature-flag-only).

async def _load_sponsored_user_or_404(institution_id: str, user_id: str) -> Dict[str, Any]:
    """Return the users doc IFF it is a sponsored learner of THIS school
    (institution_promo.code == this school's promo_code). Else 404."""
    inst = await database.institutions.find_one({"_id": ObjectId(institution_id)})
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    promo_code = (inst.get("promo_code") or "").strip().upper()
    if not promo_code:
        raise HTTPException(status_code=400, detail="This school has no promo code set")
    try:
        user = await database.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user id")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    code = ((user.get("institution_promo") or {}).get("code") or "").strip().upper()
    if code != promo_code:
        raise HTTPException(status_code=403, detail="This user is not a sponsored learner of your school")
    return user


async def _validate_tutor(institution_id: str, tutor_id: str) -> Dict[str, Any]:
    """Tutor must exist, belong to this institution, and be active."""
    try:
        tutor = await database.tutors.find_one({"_id": ObjectId(tutor_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid tutor id")
    if not tutor or str(tutor.get("institution_id")) != str(institution_id):
        raise HTTPException(status_code=404, detail="Tutor not found in this institution")
    if not tutor.get("is_active", True):
        raise HTTPException(status_code=400, detail="Cannot assign learners to an inactive tutor")
    return tutor


async def _enroll_sponsored_upsert(institution_id: str, user_id: str, tutor_id: Optional[str]) -> ObjectId:
    """Idempotently create/refresh the institutional_learners row for a sponsored
    learner and (optionally) set its tutor. Returns the row _id.
    Re-activates a previously deactivated row so it re-appears for the tutor."""
    now = datetime.utcnow()
    set_fields = {
        "institution_id": institution_id,
        "user_id": str(user_id),
        "enrollment_method": "promo_code",
        # Redeeming the school's code is an explicit action → implicit consent
        # (same rule as self_signup). Does NOT touch a prior revoke flag.
        "consent_given": True,
        "is_active": True,
        "updated_at": now,
    }
    if tutor_id is not None:
        set_fields["tutor_id"] = tutor_id
    result = await database.institutional_learners.update_one(
        {"user_id": str(user_id), "institution_id": institution_id},
        {
            "$set": set_fields,
            "$setOnInsert": {"enrolled_at": now, "consent_date": now},
        },
        upsert=True,
    )
    if result.upserted_id:
        return result.upserted_id
    row = await database.institutional_learners.find_one(
        {"user_id": str(user_id), "institution_id": institution_id}, {"_id": 1}
    )
    return row["_id"]


@router.post("/{institution_id}/learners/enroll",
             dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def enroll_sponsored_learner(
    institution_id: str,
    body: Dict[str, Any] = Body(...),
    admin: Dict[str, Any] = Depends(get_current_institution_admin),
) -> Dict[str, Any]:
    """
    Admin action: enroll a sponsored learner into the institution's roster
    (creates the institutional_learners row) WITHOUT assigning a tutor yet.
    Idempotent. Seat-limited by the school's max_learners.
    """
    _require_tenant(admin, institution_id)
    user_id = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    await _load_sponsored_user_or_404(institution_id, user_id)

    # Seat limit: count DISTINCT active enrolled learners; block a NEW enroll
    # beyond max_learners (matches learner/service.py). Re-enrolling an existing
    # row is always allowed (no new seat consumed).
    inst = await database.institutions.find_one({"_id": ObjectId(institution_id)})
    max_learners = int(inst.get("max_learners", 0) or 0)
    existing = await database.institutional_learners.find_one(
        {"user_id": str(user_id), "institution_id": institution_id}
    )
    if not existing and max_learners > 0:
        active_count = await database.institutional_learners.count_documents(
            {"institution_id": institution_id, "is_active": True}
        )
        if active_count >= max_learners:
            raise HTTPException(status_code=409, detail=f"Seat limit reached ({max_learners}). Cannot enroll more learners.")

    learner_id = await _enroll_sponsored_upsert(institution_id, user_id, tutor_id=None)
    return {"message": "Learner enrolled", "learner_id": str(learner_id), "user_id": str(user_id)}


@router.post("/{institution_id}/learners/assign-tutor",
             dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def assign_learner_to_tutor(
    institution_id: str,
    assignment: Dict[str, Any] = Body(...),
    admin: Dict[str, Any] = Depends(get_current_institution_admin),
) -> Dict[str, Any]:
    """
    Assign a sponsored learner to a tutor.

    Accepts EITHER `user_id` (preferred — enroll+assign in one click) OR a
    pre-existing `learner_id` (institutional_learners._id). Validates the tutor
    (same institution, active). Upserts the enrollment row so an as-yet-unenrolled
    sponsored learner is enrolled and assigned atomically.
    """
    _require_tenant(admin, institution_id)
    tutor_id = assignment.get("tutor_id")
    user_id = assignment.get("user_id")
    learner_id = assignment.get("learner_id")

    if not tutor_id:
        raise HTTPException(status_code=400, detail="tutor_id is required")
    if not user_id and not learner_id:
        raise HTTPException(status_code=400, detail="user_id or learner_id is required")

    await _validate_tutor(institution_id, tutor_id)

    # Resolve user_id from learner_id if only the row id was given.
    if not user_id and learner_id:
        try:
            row = await database.institutional_learners.find_one(
                {"_id": ObjectId(learner_id), "institution_id": institution_id}
            )
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid learner_id")
        if not row:
            raise HTTPException(status_code=404, detail="Learner not found in this institution")
        user_id = str(row.get("user_id"))

    # Sponsored-membership check (also guards cross-school user ids).
    await _load_sponsored_user_or_404(institution_id, user_id)

    row_id = await _enroll_sponsored_upsert(institution_id, user_id, tutor_id=tutor_id)
    return {
        "message": "Learner assigned to tutor",
        "learner_id": str(row_id),
        "user_id": str(user_id),
        "tutor_id": tutor_id,
    }


@router.post("/{institution_id}/learners/bulk-assign",
             dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def bulk_assign_learners_to_tutor(
    institution_id: str,
    body: Dict[str, Any] = Body(...),
    admin: Dict[str, Any] = Depends(get_current_institution_admin),
) -> Dict[str, Any]:
    """
    Assign MANY sponsored learners to ONE tutor in a single action.
    Body: {tutor_id, user_ids: [..]}. Each id is validated as a sponsored learner
    of this school; the tutor is validated once. Per-item failures are reported,
    never aborting the whole batch.
    """
    _require_tenant(admin, institution_id)
    tutor_id = body.get("tutor_id")
    user_ids = body.get("user_ids") or []
    if not tutor_id:
        raise HTTPException(status_code=400, detail="tutor_id is required")
    if not isinstance(user_ids, list) or not user_ids:
        raise HTTPException(status_code=400, detail="user_ids (non-empty list) is required")

    await _validate_tutor(institution_id, tutor_id)

    assigned, errors = [], []
    for uid in user_ids:
        try:
            await _load_sponsored_user_or_404(institution_id, uid)
            row_id = await _enroll_sponsored_upsert(institution_id, uid, tutor_id=tutor_id)
            assigned.append({"user_id": str(uid), "learner_id": str(row_id)})
        except HTTPException as he:
            errors.append({"user_id": str(uid), "error": he.detail})
        except Exception as e:
            errors.append({"user_id": str(uid), "error": str(e)})

    return {
        "message": f"Assigned {len(assigned)} learner(s) to tutor",
        "assigned_count": len(assigned),
        "failed_count": len(errors),
        "assigned": assigned,
        "errors": errors,
        "tutor_id": tutor_id,
    }


@router.post("/{institution_id}/learners/unassign",
             dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def unassign_learner(
    institution_id: str,
    body: Dict[str, Any] = Body(...),
    admin: Dict[str, Any] = Depends(get_current_institution_admin),
) -> Dict[str, Any]:
    """
    Remove a learner's tutor (keeps the enrollment row + consent, just clears
    tutor_id). The learner stays sponsored/enrolled but no longer shows on any
    tutor's dashboard.
    """
    _require_tenant(admin, institution_id)
    user_id = body.get("user_id")
    learner_id = body.get("learner_id")
    if not user_id and not learner_id:
        raise HTTPException(status_code=400, detail="user_id or learner_id is required")

    query = {"institution_id": institution_id}
    if user_id:
        query["user_id"] = str(user_id)
    else:
        try:
            query["_id"] = ObjectId(learner_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid learner_id")

    result = await database.institutional_learners.update_one(
        query, {"$set": {"tutor_id": None, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return {"message": "Learner unassigned from tutor"}


@router.post("/{institution_id}/learners/deactivate/{learner_id}",
             dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def deactivate_learner(institution_id: str, learner_id: str) -> Dict[str, Any]:
    """
    Deactivate/archive a learner (reversible operation)
    """
    try:
        result = await database.institutional_learners.update_one(
            {"_id": ObjectId(learner_id), "institution_id": institution_id},
            {"$set": {"is_active": False, "deactivated_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Learner not found")
        
        return {"message": "Learner deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deactivate learner: {str(e)}")


@router.post("/{institution_id}/learners/reactivate/{learner_id}",
             dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def reactivate_learner(institution_id: str, learner_id: str) -> Dict[str, Any]:
    """
    Reactivate a previously deactivated learner
    """
    try:
        result = await database.institutional_learners.update_one(
            {"_id": ObjectId(learner_id), "institution_id": institution_id},
            {
                "$set": {"is_active": True, "reactivated_at": datetime.utcnow()},
                "$unset": {"deactivated_at": ""}
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Learner not found")
        
        return {"message": "Learner reactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reactivate learner: {str(e)}")


@router.post("/{institution_id}/learners/bulk-import",
             dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def bulk_import_learners(
    institution_id: str,
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    """
    Bulk import learners from CSV or Excel (.xlsx) file.
    Required columns : name (or first_name + last_name), email
    Optional columns : language, level, tutor_email
    Column headers are matched case-insensitively with common aliases.
    """
    try:
        rows = await _parse_import_file(file, _LEARNER_ALIASES)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    success_count = 0
    failed_count  = 0
    skipped_count = 0   # already enrolled
    errors: List[str] = []

    for row_num, row in enumerate(rows, start=2):
        try:
            name  = row.get("name", "").strip()
            email = row.get("email", "").strip().lower()

            if not name or not email:
                errors.append(f"Row {row_num}: 'name' and 'email' are required")
                failed_count += 1
                continue

            # Find or create the user account
            user = await database.users.find_one({"email": email})
            if not user:
                user_result = await database.users.insert_one({
                    "name": name,
                    "email": email,
                    "preferred_language": row.get("language") or None,
                    "preferred_level": row.get("level") or None,
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                })
                user_id = str(user_result.inserted_id)
            else:
                user_id = str(user["_id"])

            # Resolve optional tutor assignment
            tutor_id: Optional[str] = None
            tutor_email = row.get("tutor_email", "").lower()
            if tutor_email:
                tutor = await database.tutors.find_one(
                    {"email": tutor_email, "institution_id": institution_id}
                )
                if tutor:
                    tutor_id = str(tutor["_id"])
                else:
                    errors.append(
                        f"Row {row_num}: tutor '{tutor_email}' not found in this institution — learner enrolled without tutor"
                    )

            # Skip if already enrolled
            already = await database.institutional_learners.find_one(
                {"user_id": user_id, "institution_id": institution_id}
            )
            if already:
                skipped_count += 1
                continue

            await database.institutional_learners.insert_one({
                "user_id": user_id,
                "institution_id": institution_id,
                "tutor_id": tutor_id,
                "enrollment_method": "bulk_import",
                "consent_given": False,
                "enrolled_at": datetime.utcnow(),
                "is_active": True,
            })
            success_count += 1

        except Exception as exc:
            errors.append(f"Row {row_num}: unexpected error — {exc}")
            failed_count += 1

    return {
        "message": "Import completed",
        "success_count": success_count,
        "skipped_count": skipped_count,
        "failed_count": failed_count,
        "errors": errors[:20],
    }


@router.get("/{institution_id}/learners/{user_id}/comprehensive-details",
            dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def get_comprehensive_learner_details(institution_id: str, user_id: str) -> Dict[str, Any]:
    """
    Get comprehensive learner analytics with AI-generated insights
    Includes ALL learning plans, sessions, assessments, and recommendations
    """
    try:
        # Check if learner belongs to institution
        learner = await database.institutional_learners.find_one({
            'institution_id': institution_id,
            'user_id': user_id
        })

        if not learner:
            raise HTTPException(status_code=404, detail="Learner not found")

        # Get user info
        user = await database.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get ALL learning plans
        all_learning_plans = await database.learning_plans.find({'user_id': user_id}).to_list(length=None)

        # Get ALL conversation sessions (correct collection name)
        all_conversations = await database.conversation_sessions.find({
            'user_id': user_id
        }).sort('created_at', -1).to_list(length=None)

        # Get challenge sessions
        all_challenges = await database.challenge_sessions.find({
            'user_id': user_id
        }).sort('created_at', -1).to_list(length=100)

        # Get daily stats for streak/XP data
        daily_stats = await database.daily_stats.find({
            'user_id': user_id
        }).sort('date', -1).to_list(length=30)

        # Get subscription info
        subscription = await database.subscriptions.find_one({'user_id': user_id})
        # Fallback: subscription fields may live directly on the user document
        if not subscription:
            sub_status = user.get('subscription_status')
            sub_plan = user.get('subscription_plan')
        else:
            sub_status = subscription.get('status')
            sub_plan = subscription.get('plan_type') or subscription.get('subscription_plan')
        
        # Get tutor info
        tutor_info = None
        if learner.get('tutor_id'):
            tutor = await database.tutors.find_one({'_id': ObjectId(learner['tutor_id'])})
            if tutor:
                tutor_info = {
                    'id': str(tutor['_id']),
                    'name': tutor.get('name'),
                    'email': tutor.get('email')
                }
        
        # Calculate overall metrics
        total_sessions = sum([plan.get('completed_sessions', 0) for plan in all_learning_plans])
        total_minutes = sum([plan.get('practice_minutes_used', 0) for plan in all_learning_plans])
        # Also count realtime session minutes from conversation_sessions
        realtime_minutes = sum([
            round(s.get('duration_seconds', 0) / 60, 1) for s in all_conversations
        ])
        if total_minutes == 0 and realtime_minutes > 0:
            total_minutes = realtime_minutes
        
        def _iso(v):
            """Safely convert datetime or string to ISO string."""
            if v is None:
                return None
            if isinstance(v, str):
                return v
            if hasattr(v, 'isoformat'):
                return v.isoformat()
            return str(v)

        def _to_dt(v):
            """Safely convert to naive datetime for arithmetic."""
            if isinstance(v, datetime):
                return v.replace(tzinfo=None)
            if isinstance(v, str):
                try:
                    return datetime.fromisoformat(v.replace('Z', '+00:00')).replace(tzinfo=None)
                except Exception:
                    return None
            return None

        # Format learning plans
        formatted_plans = []
        for plan in all_learning_plans:
            formatted_plans.append({
                'id': str(plan.get('_id', plan.get('id', ''))),
                'language': plan.get('language'),
                'proficiency_level': plan.get('proficiency_level'),
                'progress_percentage': round(plan.get('progress_percentage', 0), 1),
                'completed_sessions': plan.get('completed_sessions', 0),
                'total_sessions': plan.get('total_sessions', 16),
                'practice_minutes_used': round(plan.get('practice_minutes_used', 0), 1),
                'total_practice_minutes': plan.get('total_practice_minutes', 80),
                'created_at': _iso(plan.get('created_at')),
                'assessment_data': plan.get('assessment_data', {}),
                'plan_content': {
                    'title': plan.get('plan_content', {}).get('title'),
                    'assessment_summary': plan.get('plan_content', {}).get('assessment_summary', {}),
                    'learning_objectives': plan.get('plan_content', {}).get('learning_objectives', []),
                    'weekly_schedule': plan.get('plan_content', {}).get('weekly_schedule', [])
                },
                'session_summaries': plan.get('session_summaries', [])
            })

        # Format conversations (realtime sessions)
        formatted_conversations = [
            {
                'id': str(conv['_id']),
                'created_at': _iso(conv.get('created_at')),
                'duration_minutes': round(conv.get('duration_seconds', 0) / 60, 1),
                'message_count': conv.get('message_count', len(conv.get('messages', []))),
                'language': conv.get('language'),
                'level': conv.get('level'),
                'session_type': conv.get('session_type', 'practice')
            } for conv in all_conversations
        ]

        # Format challenge sessions — real schema fields
        formatted_challenges = [
            {
                'id': str(ch['_id']),
                'created_at': _iso(ch.get('created_at')),
                'challenge_type': ch.get('challenge_type'),
                'language': ch.get('language'),
                'level': ch.get('level'),
                'correct_answers': ch.get('correct_answers', 0),
                'wrong_answers': ch.get('wrong_answers', 0),
                'total_challenges': ch.get('total_challenges', 0),
                'accuracy': ch.get('accuracy', 0),
                'total_xp': ch.get('total_xp', 0),
                'max_combo': ch.get('max_combo', 0),
                'completed': ch.get('end_time') is not None
            } for ch in all_challenges
        ]

        # Daily stats summary
        stats_summary = {
            'current_streak': daily_stats[0].get('streak_days', 0) if daily_stats else 0,
            'total_xp': sum(s.get('xp_earned', 0) for s in daily_stats),
            'days_active': len([s for s in daily_stats if s.get('sessions_count', 0) > 0]),
            'recent_daily': [
                {
                    'date': _iso(s.get('date')),
                    'minutes': round(s.get('practice_minutes', s.get('speaking_minutes', 0)), 1),
                    'sessions': s.get('sessions_count', 0),
                    'xp': s.get('xp_earned', 0)
                } for s in daily_stats[:14]
            ]
        }

        # Generate AI Insights
        ai_insights = generate_ai_insights(user, formatted_plans, formatted_conversations)

        return {
            'profile': {
                'id': str(user['_id']),
                'name': user.get('name'),
                'email': user.get('email'),
                'created_at': _iso(user.get('created_at')),
                'total_sessions': total_sessions,
                'total_minutes': round(total_minutes, 1),
                'realtime_sessions': len(formatted_conversations),
                'challenge_sessions': len(formatted_challenges),
                'languages_studied': list(set(p['language'] for p in formatted_plans if p.get('language'))),
                'preferred_language': user.get('preferred_language'),
                'preferred_level': user.get('preferred_level')
            },
            'all_learning_plans': formatted_plans,
            'practice_sessions': formatted_conversations,
            'challenge_sessions': formatted_challenges,
            'daily_stats': stats_summary,
            'subscription': {
                'status': sub_status or 'none',
                'minutes_remaining': user.get('practice_minutes_remaining', 0),
                'plan_type': sub_plan,
                'subscription_plan': user.get('subscription_plan'),
                'subscription_status': user.get('subscription_status')
            },
            'tutor': tutor_info,
            'ai_insights': ai_insights,
            'consent_given': learner.get('consent_given', True),
            'enrolled_at': _iso(learner.get('enrolled_at'))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get comprehensive learner details: {str(e)}")


def generate_ai_insights(user, learning_plans, conversations):
    """Generate AI-powered insights from learner data"""
    
    total_sessions = sum([plan['completed_sessions'] for plan in learning_plans])
    total_minutes = sum([plan['practice_minutes_used'] for plan in learning_plans])
    
    # Calculate average progress
    avg_progress = sum([plan['progress_percentage'] for plan in learning_plans]) / len(learning_plans) if learning_plans else 0
    
    # Analyze session patterns
    if conversations:
        session_hours = []
        for conv in conversations:
            try:
                raw = conv.get('created_at')
                if raw:
                    from datetime import datetime
                    if isinstance(raw, str):
                        dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
                    elif hasattr(raw, 'hour'):
                        dt = raw
                    else:
                        continue
                    session_hours.append(dt.hour)
            except Exception:
                pass
        
        peak_hour = max(set(session_hours), key=session_hours.count) if session_hours else 12
        learning_time = "morning" if peak_hour < 12 else "afternoon" if peak_hour < 17 else "evening"
    else:
        learning_time = "unknown"
    
    # Calculate progress rate
    user_created_raw = user.get('created_at')
    if user_created_raw:
        try:
            from datetime import datetime
            if isinstance(user_created_raw, str):
                user_created = datetime.fromisoformat(user_created_raw.replace('Z', '+00:00')).replace(tzinfo=None)
            elif hasattr(user_created_raw, 'replace'):
                user_created = user_created_raw.replace(tzinfo=None)
            else:
                user_created = None
            if user_created:
                days_active = (datetime.utcnow() - user_created).days
                sessions_per_week = (total_sessions / days_active) * 7 if days_active > 0 else total_sessions
            else:
                sessions_per_week = 1
        except Exception:
            sessions_per_week = 1
    else:
        sessions_per_week = 1
    
    if sessions_per_week > 3:
        progress_rate = "fast"
        progress_description = "above average"
    elif sessions_per_week > 1.5:
        progress_rate = "moderate"
        progress_description = "steady"
    else:
        progress_rate = "slow"
        progress_description = "needs attention"
    
    # Engagement analysis
    if sessions_per_week > 2:
        consistency = "high"
    elif sessions_per_week > 1:
        consistency = "moderate"
    else:
        consistency = "low"
    
    # Multi-language insights
    is_multi_language = len(learning_plans) > 1
    
    # Generate recommendations
    recommendations = []
    
    for plan in learning_plans:
        lang = plan['language'].title()
        
        # Low progress check
        if plan['progress_percentage'] < 30:
            recommendations.append(f"📈 Increase {lang} practice frequency to accelerate progress")
        
        # Check weak skills from assessment
        if 'assessment_data' in plan and 'skill_scores' in plan['assessment_data']:
            weak_skills = [
                skill for skill, score in plan['assessment_data']['skill_scores'].items() 
                if score < 60
            ]
            for skill in weak_skills[:2]:  # Top 2 weak skills
                recommendations.append(f"🎯 Focus on improving {lang} {skill}")
        
        # Check areas for improvement
        if 'assessment_data' in plan and 'areas_for_improvement' in plan['assessment_data']:
            for area in plan['assessment_data']['areas_for_improvement'][:1]:
                recommendations.append(f"💡 {lang}: {area}")
    
    # Consistency recommendation
    if consistency == "low":
        recommendations.append("⏰ Try to practice more regularly - aim for at least 2 sessions per week")
    
    # Multi-language recommendation
    if is_multi_language:
        recommendations.append("🌍 Balance practice time across both languages for optimal retention")
    
    # Overall summary
    language_list = ", ".join([plan['language'].title() for plan in learning_plans])
    summary = f"This learner is studying {language_list} with {progress_description} progress. "
    summary += f"They have completed {total_sessions} practice sessions totaling {total_minutes} minutes. "
    summary += f"Most active during {learning_time} hours with {consistency} consistency. "
    
    if is_multi_language:
        summary += f"As a multi-language learner, they are developing skills across {len(learning_plans)} languages simultaneously."
    
    # Plan-specific insights
    plan_insights = {}
    for plan in learning_plans:
        plan_id = plan['id']
        lang = plan['language'].title()
        progress = plan['progress_percentage']
        
        if progress < 20:
            insight = f"Just getting started with {lang}. Early progress shows engagement."
        elif progress < 50:
            insight = f"Building foundation in {lang}. Keep the momentum going!"
        elif progress < 80:
            insight = f"Strong progress in {lang}. Approaching mastery of current level."
        else:
            insight = f"Excellent work in {lang}! Nearly completed the learning plan."
        
        # Add assessment-based insight
        if 'assessment_data' in plan and 'strengths' in plan['assessment_data']:
            strengths = plan['assessment_data'].get('strengths', [])
            if strengths:
                insight += f" Key strength: {strengths[0]}"
        
        plan_insights[plan_id] = insight
    
    return {
        'overall_summary': summary,
        'learning_style': {
            'preferred_time': learning_time,
            'type': 'multi-language' if is_multi_language else 'focused'
        },
        'progress_rate': {
            'rate': progress_rate,
            'description': progress_description,
            'sessions_per_week': round(sessions_per_week, 1)
        },
        'engagement': {
            'consistency': consistency,
            'total_sessions': total_sessions,
            'total_minutes': total_minutes,
            'average_session_duration': round(total_minutes / total_sessions, 1) if total_sessions > 0 else 0
        },
        'recommendations': recommendations[:6],  # Top 6 recommendations
        'plan_specific_insights': plan_insights,
        'multi_language_learner': is_multi_language
    }


@router.get("/{institution_id}/learners/export",
            dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def export_learners(institution_id: str):
    """
    Export learner data as a downloadable CSV file.
    Columns: name, email, language, level, tutor_email, enrolled_at, consent_given
    """
    from fastapi.responses import StreamingResponse

    try:
        learners = await database.institutional_learners.find({
            "institution_id": institution_id,
            "is_active": True
        }).to_list(length=None)

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["name", "email", "language", "level", "tutor_email", "enrolled_at", "consent_given"])

        for learner in learners:
            user_id = learner.get("user_id")
            if not user_id:
                continue
            try:
                user = await database.users.find_one({"_id": ObjectId(user_id)})
                if not user:
                    continue
                tutor_email = ""
                if learner.get("tutor_id"):
                    tutor = await database.tutors.find_one({"_id": ObjectId(learner["tutor_id"])})
                    if tutor:
                        tutor_email = tutor.get("email", "")
                writer.writerow([
                    user.get("name", ""),
                    user.get("email", ""),
                    user.get("preferred_language") or "",
                    user.get("preferred_level") or "",
                    tutor_email,
                    str(learner.get("enrolled_at", "")),
                    learner.get("consent_given", False)
                ])
            except Exception:
                pass

        output.seek(0)
        filename = f"learners_{datetime.utcnow().strftime('%Y-%m-%d')}.csv"
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export learners: {str(e)}")


# =============================================================================
# SETTINGS ENDPOINTS
# =============================================================================

# ── Institution Profile ───────────────────────────────────────────────────────

@router.get("/{institution_id}/settings/profile",
            dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def get_profile_settings(institution_id: str) -> Dict[str, Any]:
    """Return editable institution profile fields."""
    from bson import ObjectId as OID
    try:
        inst = await database.institutions.find_one({"_id": OID(institution_id)})
        if not inst:
            raise HTTPException(status_code=404, detail="Institution not found")
        return {
            "name":             inst.get("name", ""),
            "institution_type": inst.get("institution_type", "school"),
            "website":          inst.get("website") or "",
            "phone":            inst.get("phone") or "",
            "address":          inst.get("address") or "",
            "logo_url":         inst.get("logo_url") or "",
            "admin_language":   inst.get("admin_language") or "en",
            "timezone":         inst.get("timezone") or "UTC",
            "semester_start":   inst.get("semester_start") or "",
            "semester_end":     inst.get("semester_end") or "",
            # Stripe promotion code (e.g. "AMSTERDAMTAAL") the school hands to its
            # students; the Learners tab lists everyone who redeemed it.
            "promo_code":       inst.get("promo_code") or "",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{institution_id}/settings/profile",
            dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def update_profile_settings(
    institution_id: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """Update editable institution profile fields."""
    from bson import ObjectId as OID

    ALLOWED = {
        "name", "institution_type", "website", "phone",
        "address", "logo_url", "admin_language", "timezone",
        "semester_start", "semester_end", "promo_code",
    }
    INSTITUTION_TYPES = {"school", "university", "language_center", "corporate"}

    update: Dict[str, Any] = {}
    for field in ALLOWED:
        if field in body:
            # Normalise the promo code: Stripe promotion codes are matched
            # case-insensitively at checkout, but we store a canonical upper form.
            if field == "promo_code" and isinstance(body[field], str):
                update[field] = body[field].strip().upper()
            else:
                update[field] = body[field]

    if not update:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    if "institution_type" in update and update["institution_type"] not in INSTITUTION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"institution_type must be one of {sorted(INSTITUTION_TYPES)}"
        )

    update["updated_at"] = datetime.utcnow()

    try:
        result = await database.institutions.update_one(
            {"_id": OID(institution_id)},
            {"$set": update}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Institution not found")
        return {"message": "Profile updated successfully", "updated_fields": list(update.keys())}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Admin Account ─────────────────────────────────────────────────────────────

@router.get("/{institution_id}/settings/admin",
            dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def get_admin_settings(institution_id: str) -> Dict[str, Any]:
    """Return admin account settings (never returns password)."""
    from bson import ObjectId as OID
    try:
        inst = await database.institutions.find_one({"_id": OID(institution_id)})
        if not inst:
            raise HTTPException(status_code=404, detail="Institution not found")
        return {
            "admin_name":    inst.get("admin_name", ""),
            "admin_email":   inst.get("admin_email", ""),
            "admin_photo_url": inst.get("admin_photo_url") or "",
            "notify_daily_digest":  inst.get("notify_daily_digest", False),
            "notify_weekly_report": inst.get("notify_weekly_report", True),
            "notify_learner_alerts": inst.get("notify_learner_alerts", True),
            "two_factor_enabled":   inst.get("two_factor_enabled", False),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{institution_id}/settings/admin",
            dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def update_admin_settings(
    institution_id: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """Update admin name, photo URL, and notification preferences."""
    from bson import ObjectId as OID

    ALLOWED = {
        "admin_name", "admin_photo_url",
        "notify_daily_digest", "notify_weekly_report",
        "notify_learner_alerts", "two_factor_enabled",
    }
    update: Dict[str, Any] = {k: body[k] for k in ALLOWED if k in body}
    if not update:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    update["updated_at"] = datetime.utcnow()

    try:
        result = await database.institutions.update_one(
            {"_id": OID(institution_id)},
            {"$set": update}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Institution not found")
        return {"message": "Admin settings updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{institution_id}/settings/admin/change-password",
             dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def change_admin_password(
    institution_id: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """Change the admin password after verifying the current one."""
    from bson import ObjectId as OID
    import bcrypt

    current  = body.get("current_password", "")
    new_pass = body.get("new_password", "")

    if not current or not new_pass:
        raise HTTPException(status_code=400, detail="current_password and new_password are required")
    if len(new_pass) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    try:
        inst = await database.institutions.find_one({"_id": OID(institution_id)})
        if not inst:
            raise HTTPException(status_code=404, detail="Institution not found")

        stored_hash = inst.get("admin_password", "")
        if not bcrypt.checkpw(current.encode(), stored_hash.encode()):
            raise HTTPException(status_code=401, detail="Current password is incorrect")

        new_hash = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()
        await database.institutions.update_one(
            {"_id": OID(institution_id)},
            {"$set": {"admin_password": new_hash, "updated_at": datetime.utcnow()}}
        )
        # Record in activity log
        await database.institution_activity_log.insert_one({
            "institution_id": institution_id,
            "action": "password_changed",
            "detail": "Admin password changed",
            "timestamp": datetime.utcnow(),
            "ip": None,
        })
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{institution_id}/settings/admin/activity-log",
            dependencies=[Depends(check_feature_enabled), Depends(verify_institution_admin)])
async def get_activity_log(institution_id: str) -> Dict[str, Any]:
    """Return the last 20 admin activity log entries for this institution."""
    try:
        entries = await database.institution_activity_log.find(
            {"institution_id": institution_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(20).to_list(length=20)

        return {"entries": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

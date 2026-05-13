"""
Enhanced Institution Dashboard APIs
Provides analytics, tutor management, and learner management
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId
from io import StringIO, BytesIO
import csv

from app.config.feature_flags import feature_flags
from database import database
from auth import create_access_token

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
    # optional
    "bio": "bio", "biography": "bio", "description": "bio", "about": "bio",
    "qualifications": "qualifications", "qualification": "qualifications",
    "credentials": "qualifications", "degree": "qualifications",
    "specializations": "specializations", "specialization": "specializations",
    "subjects": "specializations", "languages": "specializations",
    "expertise": "specializations",
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

def check_feature_enabled():
    """Check if institutional features are enabled"""
    if not feature_flags.INSTITUTIONAL_FEATURES_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="Institutional features are not enabled"
        )

# ============================================================================
# ANALYTICS APIs
# ============================================================================

@router.get("/{institution_id}/analytics/language-distribution",
            dependencies=[Depends(check_feature_enabled)])
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
            dependencies=[Depends(check_feature_enabled)])
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
            dependencies=[Depends(check_feature_enabled)])
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
                "created_at": tutor.get("created_at")
            })
        
        return {
            "total_tutors": len(tutor_list),
            "tutors": tutor_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tutors: {str(e)}")


@router.post("/{institution_id}/tutors",
             dependencies=[Depends(check_feature_enabled)])
async def add_tutor(institution_id: str, tutor_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a new tutor to the institution
    NEW: Now includes password field for tutor login
    """
    try:
        # Import password hashing function
        from app.tutor.tutor_auth import get_password_hash, validate_password_strength
        
        # Validate required fields
        if not tutor_data.get("name") or not tutor_data.get("email"):
            raise HTTPException(status_code=400, detail="Name and email are required")
        
        # NEW: Validate password if provided
        password = tutor_data.get("password", "")
        if not password:
            raise HTTPException(status_code=400, detail="Password is required for tutor account")
        
        # Validate password strength
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)
        
        # Check if tutor email already exists
        existing = await database.tutors.find_one({"email": tutor_data["email"]})
        if existing:
            raise HTTPException(status_code=400, detail="Tutor with this email already exists")
        
        # Hash the password
        hashed_password = get_password_hash(password)
        
        # Create tutor document
        tutor = {
            "name": tutor_data["name"],
            "email": tutor_data["email"],
            "hashed_password": hashed_password,  # NEW: Store hashed password
            "first_login": True,  # NEW: Flag for password change requirement
            "institution_id": institution_id,
            "bio": tutor_data.get("bio", ""),
            "specializations": tutor_data.get("specializations", []),
            "permissions": tutor_data.get("permissions", ["view_learners", "assign_tasks"]),
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        
        result = await database.tutors.insert_one(tutor)
        
        # Convert ObjectId to string for JSON serialization
        tutor_response = {
            "message": "Tutor added successfully. Initial password has been set.",
            "tutor_id": str(result.inserted_id),
            "tutor": {
                "id": str(result.inserted_id),
                "name": tutor["name"],
                "email": tutor["email"],
                "bio": tutor["bio"],
                "specializations": tutor["specializations"],
                "permissions": tutor["permissions"],
                "first_login": True,
                "created_at": tutor["created_at"].isoformat() if tutor.get("created_at") else None
            }
        }
        
        return tutor_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add tutor: {str(e)}")


@router.post("/{institution_id}/tutors/bulk-import",
             dependencies=[Depends(check_feature_enabled)])
async def bulk_import_tutors(
    institution_id: str,
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    """
    Bulk import tutors from CSV or Excel (.xlsx) file.
    Required columns : name (or first_name + last_name), email
    Optional columns : bio, qualifications, specializations (comma-separated)
    Column headers are matched case-insensitively with common aliases.
    Tutors receive a random temporary password; must_reset_password is set True.
    """
    import secrets, string
    from app.tutor.tutor_auth import get_password_hash

    def _temp_password() -> str:
        chars = string.ascii_letters + string.digits
        return ''.join(secrets.choice(chars) for _ in range(16))

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

    for row_num, row in enumerate(rows, start=2):
        try:
            name  = row.get("name", "").strip()
            email = row.get("email", "").strip().lower()

            if not name or not email:
                errors.append(f"Row {row_num}: 'name' and 'email' are required")
                failed_count += 1
                continue

            # Skip duplicates within the same institution
            if await database.tutors.find_one({"email": email, "institution_id": institution_id}):
                skipped_count += 1
                continue

            raw_specs = row.get("specializations", "")
            specializations = [s.strip() for s in raw_specs.split(",") if s.strip()]

            await database.tutors.insert_one({
                "name": name,
                "email": email,
                "bio": row.get("bio") or None,
                "qualifications": row.get("qualifications") or None,
                "specializations": specializations,
                "institution_id": institution_id,
                "hashed_password": get_password_hash(_temp_password()),
                "must_reset_password": True,
                "assigned_learners": [],
                "is_active": True,
                "enrollment_method": "bulk_import",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
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


@router.get("/{institution_id}/tutors/export",
            dependencies=[Depends(check_feature_enabled)])
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
               dependencies=[Depends(check_feature_enabled)])
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
             dependencies=[Depends(check_feature_enabled)])
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
             dependencies=[Depends(check_feature_enabled)])
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


@router.put("/{institution_id}/tutors/{tutor_id}/permissions",
            dependencies=[Depends(check_feature_enabled)])
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

@router.get("/{institution_id}/learners",
            dependencies=[Depends(check_feature_enabled)])
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


@router.post("/{institution_id}/learners/assign-tutor",
             dependencies=[Depends(check_feature_enabled)])
async def assign_learner_to_tutor(
    institution_id: str,
    assignment: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Assign a learner to a specific tutor
    """
    try:
        learner_id = assignment.get("learner_id")
        tutor_id = assignment.get("tutor_id")
        
        if not learner_id or not tutor_id:
            raise HTTPException(status_code=400, detail="learner_id and tutor_id are required")
        
        result = await database.institutional_learners.update_one(
            {"_id": ObjectId(learner_id), "institution_id": institution_id},
            {"$set": {"tutor_id": tutor_id, "updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Learner not found or already assigned")
        
        return {"message": "Learner assigned to tutor successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign learner: {str(e)}")


@router.post("/{institution_id}/learners/deactivate/{learner_id}",
             dependencies=[Depends(check_feature_enabled)])
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
             dependencies=[Depends(check_feature_enabled)])
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
             dependencies=[Depends(check_feature_enabled)])
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
            dependencies=[Depends(check_feature_enabled)])
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
            dependencies=[Depends(check_feature_enabled)])
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
            dependencies=[Depends(check_feature_enabled)])
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
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{institution_id}/settings/profile",
            dependencies=[Depends(check_feature_enabled)])
async def update_profile_settings(
    institution_id: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """Update editable institution profile fields."""
    from bson import ObjectId as OID

    ALLOWED = {
        "name", "institution_type", "website", "phone",
        "address", "logo_url", "admin_language", "timezone",
        "semester_start", "semester_end",
    }
    INSTITUTION_TYPES = {"school", "university", "language_center", "corporate"}

    update: Dict[str, Any] = {}
    for field in ALLOWED:
        if field in body:
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
            dependencies=[Depends(check_feature_enabled)])
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
            dependencies=[Depends(check_feature_enabled)])
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
             dependencies=[Depends(check_feature_enabled)])
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
            dependencies=[Depends(check_feature_enabled)])
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

"""
Activation Codes Management Routes for Institutional Signups
Handles generation, conversion, and management of institutional activation codes
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import random
import string
import re

from auth import get_current_user
from models import UserResponse
from database import database
from admin_routes import get_current_admin, AdminUser
from activation_code_email_service import send_activation_code_email

router = APIRouter(prefix="/api/admin/activation_codes", tags=["activation_codes"])

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class GenerateActivationCodeRequest(BaseModel):
    institution_name: str = Field(..., min_length=2, max_length=200)
    institution_email: str = Field(..., min_length=5, max_length=200)  # NEW FIELD
    institution_type: Literal["School", "University", "Language Center", "Corporate"]
    is_trial: bool = True
    trial_duration_days: Optional[int] = Field(None, ge=7, le=90)
    target_plan: Literal["starter", "professional", "enterprise"] = "professional"
    max_tutors: int = Field(..., gt=0)
    max_learners: int = Field(..., gt=0)
    contract_id: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('trial_duration_days')
    def validate_trial_duration(cls, v, values):
        if values.get('is_trial') and v is None:
            raise ValueError('trial_duration_days is required when is_trial is True')
        if not values.get('is_trial') and v is not None:
            raise ValueError('trial_duration_days should not be provided when is_trial is False')
        return v
    
    @validator('contract_id')
    def validate_contract_id(cls, v, values):
        if not values.get('is_trial') and not v:
            raise ValueError('contract_id is required when is_trial is False')
        if values.get('is_trial') and v:
            raise ValueError('contract_id should not be provided when is_trial is True')
        return v


class ConvertToPaidRequest(BaseModel):
    contract_id: str = Field(..., min_length=1)
    subscription_plan: Literal["starter", "professional", "enterprise"]


class ExtendTrialRequest(BaseModel):
    additional_days: int = Field(..., ge=1, le=60)


class ActivationCodeResponse(BaseModel):
    activation_code: str
    institution_name: str
    institution_type: str
    is_trial: bool
    trial_duration_days: Optional[int]
    target_plan: str
    max_tutors: int
    max_learners: int
    status: str
    current_plan: str
    code_expires_at: str
    generated_at: str
    activated_at: Optional[str]
    trial_ends_at: Optional[str]
    converted_to_paid_at: Optional[str]
    contract_id: Optional[str]
    institution_id: Optional[str]
    used_by_email: Optional[str]
    notes: Optional[str]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_acronym(institution_name: str) -> str:
    """
    Generate acronym from institution name (3-7 uppercase letters)
    Examples:
    - "Lincoln Academy" -> "LINCOLN"
    - "Massachusetts Institute of Technology" -> "MIT"
    - "ABC Language Center" -> "ABC"
    """
    # Remove common words
    common_words = {'the', 'of', 'and', 'for', 'in', 'at', 'to', 'a', 'an'}
    words = [w for w in institution_name.split() if w.lower() not in common_words]
    
    if not words:
        words = institution_name.split()
    
    # If single word, take first 3-7 chars
    if len(words) == 1:
        acronym = words[0][:7].upper()
        return acronym if len(acronym) >= 3 else acronym.ljust(3, 'X')
    
    # If multiple words, try to create acronym from first letters
    acronym = ''.join(w[0].upper() for w in words if w)
    
    # If acronym too short, use first word
    if len(acronym) < 3:
        acronym = words[0][:7].upper()
    
    # If acronym too long, truncate
    if len(acronym) > 7:
        acronym = acronym[:7]
    
    return acronym


def generate_random_suffix() -> str:
    """
    Generate 4-character random suffix (A-Z except O,I + 2-9)
    Excludes O, I to avoid confusion with 0, 1
    """
    letters = 'ABCDEFGHJKLMNPQRSTUVWXYZ'  # Exclude O, I
    digits = '23456789'  # Exclude 0, 1
    chars = letters + digits
    return ''.join(random.choice(chars) for _ in range(4))


async def generate_unique_activation_code(institution_name: str) -> str:
    """
    Generate unique activation code in format: {ACRONYM}-ACT-{4RANDOM}
    Ensures uniqueness by checking database
    """
    collection = database.activation_codes
    max_attempts = 10
    
    acronym = generate_acronym(institution_name)
    
    for _ in range(max_attempts):
        suffix = generate_random_suffix()
        code = f"{acronym}-ACT-{suffix}"
        
        # Check if code already exists
        existing = await collection.find_one({"activation_code": code})
        if not existing:
            return code
    
    # If all attempts failed, add timestamp
    timestamp = datetime.now(timezone.utc).strftime("%H%M")
    return f"{acronym}-ACT-{timestamp}"


def serialize_activation_code(doc: dict) -> dict:
    """Convert MongoDB document to API response format"""
    if not doc:
        return None
    
    # Convert ObjectId to string
    if '_id' in doc:
        doc['id'] = str(doc['_id'])
        del doc['_id']
    
    # Convert datetime objects to ISO strings
    for field in ['generated_at', 'code_expires_at', 'activated_at', 'trial_ends_at', 
                  'converted_to_paid_at', 'created_at', 'updated_at']:
        if field in doc and doc[field]:
            if isinstance(doc[field], datetime):
                doc[field] = doc[field].isoformat()
    
    # Convert ObjectId fields to strings
    for field in ['generated_by_admin_id', 'institution_id']:
        if field in doc and doc[field]:
            doc[field] = str(doc[field])
    
    return doc


async def check_admin_rate_limit(admin_id: str) -> bool:
    """
    Check if admin has exceeded rate limit (10 codes per hour)
    Returns True if within limit, False if exceeded
    """
    collection = database.activation_codes
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    
    count = await collection.count_documents({
        "generated_by_admin_id": admin_id,
        "generated_at": {"$gte": one_hour_ago}
    })
    
    return count < 10


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("", response_model=dict)
async def generate_activation_code(
    request: GenerateActivationCodeRequest,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Generate new activation code for institution
    
    - **institution_name**: Name of the institution
    - **institution_type**: Type of institution
    - **is_trial**: Whether to start as trial
    - **trial_duration_days**: Trial duration (7-90 days) if is_trial=True
    - **target_plan**: Target subscription plan
    - **max_tutors**: Maximum number of tutors
    - **max_learners**: Maximum number of learners
    - **contract_id**: Contract ID (required if is_trial=False)
    - **notes**: Optional notes
    """
    try:
        # Check admin permissions (you may want to add role check here)
        admin_id = str(current_admin.id)
        
        # Check rate limit
        if not await check_admin_rate_limit(admin_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Maximum 10 codes per hour."
            )
        
        # Generate unique activation code
        activation_code = await generate_unique_activation_code(request.institution_name)
        
        # Calculate expiration date (30 days from now)
        now = datetime.now(timezone.utc)
        code_expires_at = now + timedelta(days=30)
        
        # Prepare document
        doc = {
            "activation_code": activation_code,
            "institution_name": request.institution_name,
            "institution_email": request.institution_email,  # NEW FIELD
            "institution_type": request.institution_type,
            "is_trial": request.is_trial,
            "trial_duration_days": request.trial_duration_days,
            "target_plan": request.target_plan,
            "max_tutors": request.max_tutors,
            "max_learners": request.max_learners,
            "status": "pending",
            "current_plan": "trial" if request.is_trial else request.target_plan,
            "generated_at": now,
            "code_expires_at": code_expires_at,
            "activated_at": None,
            "trial_ends_at": None,
            "converted_to_paid_at": None,
            "contract_id": request.contract_id,
            "institution_id": None,
            "used_by_email": None,
            "generated_by_admin_id": admin_id,
            "notes": request.notes,
            "created_at": now,
            "updated_at": now
        }
        
        # Insert into database
        collection = database.activation_codes
        result = await collection.insert_one(doc)
        
        # Fetch the created document
        created_doc = await collection.find_one({"_id": result.inserted_id})
        
        print(f"✅ Generated activation code: {activation_code} for {request.institution_name}")
        
        # Send email to institution
        email_sent = False
        try:
            email_sent = await send_activation_code_email(
                institution_email=request.institution_email,
                activation_code=activation_code,
                institution_name=request.institution_name,
                trial_duration_days=request.trial_duration_days,
                max_tutors=request.max_tutors,
                max_learners=request.max_learners,
                target_plan=request.target_plan
            )
            if email_sent:
                print(f"✅ Sent activation email to {request.institution_email}")
            else:
                print(f"⚠️ Failed to send activation email to {request.institution_email}")
        except Exception as e:
            print(f"⚠️ Error sending activation email: {str(e)}")
            # Don't fail the whole operation if email fails
        
        return {
            "success": True,
            "data": serialize_activation_code(created_doc),
            "email_sent": email_sent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating activation code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate activation code: {str(e)}"
        )


@router.get("", response_model=dict)
async def list_activation_codes(
    page: int = 1,
    per_page: int = 25,
    status_filter: Optional[str] = None,
    is_trial: Optional[bool] = None,
    institution_name: Optional[str] = None,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    List all activation codes with pagination and filters
    
    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 25)
    - **status_filter**: Filter by status (pending/active_trial/active_paid/expired/cancelled)
    - **is_trial**: Filter by trial status (true/false)
    - **institution_name**: Search by institution name
    """
    try:
        collection = database.activation_codes
        
        # Build query
        query = {}
        
        if status_filter:
            query["status"] = status_filter
        
        if is_trial is not None:
            query["is_trial"] = is_trial
        
        if institution_name:
            query["institution_name"] = {"$regex": institution_name, "$options": "i"}
        
        # Get total count
        total = await collection.count_documents(query)
        
        # Calculate skip
        skip = (page - 1) * per_page
        
        # Fetch documents
        cursor = collection.find(query).sort("generated_at", -1).skip(skip).limit(per_page)
        docs = await cursor.to_list(length=per_page)
        
        # Serialize documents
        serialized_docs = [serialize_activation_code(doc) for doc in docs]
        
        return {
            "success": True,
            "data": serialized_docs,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page
            }
        }
        
    except Exception as e:
        print(f"❌ Error listing activation codes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list activation codes: {str(e)}"
        )


@router.get("/{code_or_id}", response_model=dict)
async def get_activation_code(
    code_or_id: str,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Get single activation code details by activation code or MongoDB ID
    """
    try:
        collection = database.activation_codes
        
        # Try to find by activation_code first
        doc = await collection.find_one({"activation_code": code_or_id})
        
        # If not found, try by MongoDB _id
        if not doc:
            try:
                from bson import ObjectId
                if ObjectId.is_valid(code_or_id):
                    doc = await collection.find_one({"_id": ObjectId(code_or_id)})
            except:
                pass
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activation code '{code_or_id}' not found"
            )
        
        return {
            "success": True,
            "data": serialize_activation_code(doc)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching activation code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch activation code: {str(e)}"
        )


@router.put("/{code}/convert-to-paid", response_model=dict)
async def convert_to_paid(
    code: str,
    request: ConvertToPaidRequest,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Convert trial activation code to paid
    Updates the SAME code, does not create a new one
    """
    try:
        collection = database.activation_codes
        
        # Find the code
        doc = await collection.find_one({"activation_code": code})
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activation code '{code}' not found"
            )
        
        # Validate status
        if doc["status"] != "active_trial":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Can only convert codes with status 'active_trial'. Current status: {doc['status']}"
            )
        
        # Check if contract_id is unique
        existing_contract = await collection.find_one({
            "contract_id": request.contract_id,
            "activation_code": {"$ne": code}
        })
        
        if existing_contract:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contract ID '{request.contract_id}' is already in use"
            )
        
        # Update the code
        now = datetime.now(timezone.utc)
        update_result = await collection.update_one(
            {"activation_code": code},
            {
                "$set": {
                    "status": "active_paid",
                    "current_plan": request.subscription_plan,
                    "contract_id": request.contract_id,
                    "converted_to_paid_at": now,
                    "updated_at": now
                }
            }
        )
        
        if update_result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update activation code"
            )
        
        # Fetch updated document
        updated_doc = await collection.find_one({"activation_code": code})
        
        print(f"✅ Converted code {code} to paid with contract {request.contract_id}")
        
        return {
            "success": True,
            "data": serialize_activation_code(updated_doc),
            "message": f"Successfully converted to {request.subscription_plan} plan"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error converting to paid: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert to paid: {str(e)}"
        )


@router.put("/{code}/extend-trial", response_model=dict)
async def extend_trial(
    code: str,
    request: ExtendTrialRequest,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Extend trial period for activation code
    """
    try:
        collection = database.activation_codes
        
        # Find the code
        doc = await collection.find_one({"activation_code": code})
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activation code '{code}' not found"
            )
        
        # Validate status
        if doc["status"] != "active_trial":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Can only extend codes with status 'active_trial'. Current status: {doc['status']}"
            )
        
        # Calculate new trial end date
        current_trial_ends = doc.get("trial_ends_at")
        if not current_trial_ends:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Trial end date not set"
            )
        
        # Ensure current_trial_ends is a datetime object
        if isinstance(current_trial_ends, str):
            current_trial_ends = datetime.fromisoformat(current_trial_ends.replace('Z', '+00:00'))
        
        new_trial_ends = current_trial_ends + timedelta(days=request.additional_days)
        
        # Update the code
        now = datetime.now(timezone.utc)
        update_result = await collection.update_one(
            {"activation_code": code},
            {
                "$set": {
                    "trial_ends_at": new_trial_ends,
                    "trial_duration_days": doc.get("trial_duration_days", 0) + request.additional_days,
                    "updated_at": now
                }
            }
        )
        
        if update_result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to extend trial"
            )
        
        # Fetch updated document
        updated_doc = await collection.find_one({"activation_code": code})
        
        print(f"✅ Extended trial for code {code} by {request.additional_days} days")
        
        return {
            "success": True,
            "data": serialize_activation_code(updated_doc),
            "message": f"Trial extended by {request.additional_days} days"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error extending trial: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extend trial: {str(e)}"
        )


@router.post("/{code}/regenerate", response_model=dict)
async def regenerate_code(
    code: str,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Generate NEW code (only if original expired and unused)
    """
    try:
        collection = database.activation_codes
        
        # Find the original code
        doc = await collection.find_one({"activation_code": code})
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activation code '{code}' not found"
            )
        
        # Validate that code is expired and unused
        if doc["status"] != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Can only regenerate unused expired codes. Current status: {doc['status']}"
            )
        
        # Check if code is actually expired
        code_expires_at = doc.get("code_expires_at")
        if isinstance(code_expires_at, str):
            code_expires_at = datetime.fromisoformat(code_expires_at.replace('Z', '+00:00'))
        
        if code_expires_at > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Code has not expired yet"
            )
        
        # Generate new code
        new_activation_code = await generate_unique_activation_code(doc["institution_name"])
        
        # Calculate new expiration
        now = datetime.now(timezone.utc)
        new_expires_at = now + timedelta(days=30)
        
        # Create new document (copy from old one)
        new_doc = {
            "activation_code": new_activation_code,
            "institution_name": doc["institution_name"],
            "institution_type": doc["institution_type"],
            "is_trial": doc["is_trial"],
            "trial_duration_days": doc.get("trial_duration_days"),
            "target_plan": doc["target_plan"],
            "max_tutors": doc["max_tutors"],
            "max_learners": doc["max_learners"],
            "status": "pending",
            "current_plan": doc["current_plan"],
            "generated_at": now,
            "code_expires_at": new_expires_at,
            "activated_at": None,
            "trial_ends_at": None,
            "converted_to_paid_at": None,
            "contract_id": doc.get("contract_id"),
            "institution_id": None,
            "used_by_email": None,
            "generated_by_admin_id": str(current_admin.id),
            "notes": f"Regenerated from {code}. {doc.get('notes', '')}",
            "created_at": now,
            "updated_at": now
        }
        
        # Insert new document
        result = await collection.insert_one(new_doc)
        
        # Mark old code as cancelled
        await collection.update_one(
            {"activation_code": code},
            {
                "$set": {
                    "status": "cancelled",
                    "notes": f"{doc.get('notes', '')} [Regenerated as {new_activation_code}]",
                    "updated_at": now
                }
            }
        )
        
        # Fetch the created document
        created_doc = await collection.find_one({"_id": result.inserted_id})
        
        print(f"✅ Regenerated code {code} as {new_activation_code}")
        
        return {
            "success": True,
            "data": serialize_activation_code(created_doc),
            "message": f"New code generated: {new_activation_code}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error regenerating code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate code: {str(e)}"
        )


@router.delete("/{code}", response_model=dict)
async def cancel_code(
    code: str,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Cancel activation code (soft delete, status → cancelled)
    """
    try:
        collection = database.activation_codes
        
        # Find the code
        doc = await collection.find_one({"activation_code": code})
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activation code '{code}' not found"
            )
        
        # Update status to cancelled
        now = datetime.now(timezone.utc)
        update_result = await collection.update_one(
            {"activation_code": code},
            {
                "$set": {
                    "status": "cancelled",
                    "updated_at": now
                }
            }
        )
        
        if update_result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel activation code"
            )
        
        print(f"✅ Cancelled activation code: {code}")
        
        return {
            "success": True,
            "message": f"Activation code '{code}' has been cancelled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error cancelling code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel code: {str(e)}"
        )

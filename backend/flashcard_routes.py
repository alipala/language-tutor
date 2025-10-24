"""
Flashcard API routes for generating and managing AI-powered flashcards
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from models import (
    Flashcard, FlashcardSet, FlashcardGenerationRequest,
    FlashcardReviewRequest, FlashcardProgress, UserResponse
)
from flashcard_service import FlashcardService
from database import database
from auth import get_current_user

# Initialize router
router = APIRouter(prefix="/api/flashcards", tags=["flashcards"])

# Initialize collections
flashcards_collection = database.flashcards
flashcard_sets_collection = database.flashcard_sets

@router.post("/generate", response_model=FlashcardSet)
async def generate_flashcards(
    request: FlashcardGenerationRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Generate AI-powered flashcards from a speaking session
    """
    try:
        print(f"[FLASHCARD_API] Generating flashcards for user {current_user.id}, session {request.session_id}")

        # Validate count parameter
        if request.count < 1 or request.count > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Flashcard count must be between 1 and 10"
            )

        # Generate flashcards using the service
        flashcard_set = await FlashcardService.generate_flashcards(request, str(current_user.id))

        # Save flashcard set to database
        flashcard_set_doc = flashcard_set.dict()
        flashcard_set_doc["_id"] = ObjectId()
        flashcard_set_doc["created_at"] = datetime.utcnow()

        # Save individual flashcards
        flashcard_docs = []
        for flashcard in flashcard_set.flashcards:
            card_doc = flashcard.dict()
            card_doc["_id"] = ObjectId()
            flashcard_docs.append(card_doc)

        # Insert flashcard set
        set_result = await flashcard_sets_collection.insert_one(flashcard_set_doc)

        # Insert individual flashcards
        if flashcard_docs:
            cards_result = await flashcards_collection.insert_many(flashcard_docs)
            print(f"[FLASHCARD_API] ✅ Saved {len(cards_result.inserted_ids)} flashcards to database")

        print(f"[FLASHCARD_API] ✅ Generated and saved flashcard set: {flashcard_set.id}")

        return flashcard_set

    except Exception as e:
        print(f"[FLASHCARD_API] ❌ Error generating flashcards: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate flashcards: {str(e)}"
        )

@router.get("/sets", response_model=List[FlashcardSet])
async def get_user_flashcard_sets(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get all flashcard sets for the current user
    """
    try:
        # Find all flashcard sets for the user
        sets_cursor = flashcard_sets_collection.find({"user_id": str(current_user.id)})
        sets_docs = await sets_cursor.to_list(length=None)

        # Convert to FlashcardSet objects with populated flashcards
        flashcard_sets = []
        for doc in sets_docs:
            flashcards = []

            # Handle both old format (flashcard IDs as strings) and new format (full objects)
            flashcards_field = doc.get("flashcards", [])
            if isinstance(flashcards_field, list) and flashcards_field:
                if isinstance(flashcards_field[0], str):
                    # Old format: flashcards field contains IDs as strings
                    # Look up full flashcard objects from flashcards collection
                    flashcard_ids = flashcards_field
                    flashcards_cursor = flashcards_collection.find({
                        "id": {"$in": flashcard_ids},
                        "user_id": str(current_user.id)
                    })
                    flashcard_docs = await flashcards_cursor.to_list(length=None)

                    # Convert to Flashcard objects
                    for card_doc in flashcard_docs:
                        card_doc.pop("_id", None)
                        flashcards.append(Flashcard(**card_doc))
                else:
                    # New format: flashcards field contains full objects
                    for card_data in flashcards_field:
                        if isinstance(card_data, dict):
                            flashcards.append(Flashcard(**card_data))

            # Remove MongoDB _id field and update flashcards
            doc.pop("_id", None)
            doc["flashcards"] = flashcards
            doc["total_cards"] = len(flashcards)

            flashcard_sets.append(FlashcardSet(**doc))

        print(f"[FLASHCARD_API] Found {len(flashcard_sets)} flashcard sets for user {current_user.id}")

        return flashcard_sets

    except Exception as e:
        print(f"[FLASHCARD_API] ❌ Error fetching flashcard sets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch flashcard sets: {str(e)}"
        )

@router.get("/set/{set_id}", response_model=FlashcardSet)
async def get_flashcard_set(
    set_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get a specific flashcard set with all its flashcards
    """
    try:
        # Find the flashcard set
        set_doc = await flashcard_sets_collection.find_one({
            "id": set_id,
            "user_id": str(current_user.id)
        })

        if not set_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flashcard set not found"
            )

        # Get all flashcards for this set
        flashcards_cursor = flashcards_collection.find({
            "session_id": set_doc["session_id"],
            "user_id": str(current_user.id)
        })
        flashcard_docs = await flashcards_cursor.to_list(length=None)

        # Convert flashcards to Flashcard objects
        flashcards = []
        for doc in flashcard_docs:
            doc.pop("_id", None)
            flashcards.append(Flashcard(**doc))

        # Update the set with flashcards
        set_doc.pop("_id", None)
        set_doc["flashcards"] = flashcards
        set_doc["total_cards"] = len(flashcards)

        flashcard_set = FlashcardSet(**set_doc)

        print(f"[FLASHCARD_API] Retrieved flashcard set {set_id} with {len(flashcards)} cards")

        return flashcard_set

    except HTTPException:
        raise
    except Exception as e:
        print(f"[FLASHCARD_API] ❌ Error fetching flashcard set: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch flashcard set: {str(e)}"
        )

@router.get("/due", response_model=List[Flashcard])
async def get_due_flashcards(
    limit: int = 10,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get flashcards that are due for review
    """
    try:
        # Find flashcards due for review
        now = datetime.utcnow()
        due_cards_cursor = flashcards_collection.find({
            "user_id": str(current_user.id),
            "is_active": True,
            "$or": [
                {"next_review_date": {"$lte": now}},
                {"next_review_date": None}
            ]
        }).sort("next_review_date", 1).limit(limit)

        due_cards_docs = await due_cards_cursor.to_list(length=limit)

        # Convert to Flashcard objects
        due_cards = []
        for doc in due_cards_docs:
            doc.pop("_id", None)
            due_cards.append(Flashcard(**doc))

        print(f"[FLASHCARD_API] Found {len(due_cards)} due flashcards for user {current_user.id}")

        return due_cards

    except Exception as e:
        print(f"[FLASHCARD_API] ❌ Error fetching due flashcards: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch due flashcards: {str(e)}"
        )

@router.post("/review")
async def review_flashcard(
    request: FlashcardReviewRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update flashcard progress after review
    """
    try:
        # Find the flashcard
        flashcard_doc = await flashcards_collection.find_one({
            "id": request.flashcard_id,
            "user_id": str(current_user.id)
        })

        if not flashcard_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flashcard not found"
            )

        # Convert to Flashcard object
        flashcard_doc.pop("_id", None)
        flashcard = Flashcard(**flashcard_doc)

        # Update progress
        updated_flashcard = FlashcardService.update_flashcard_progress(flashcard, request.correct)

        # Save back to database
        update_data = {
            "review_count": updated_flashcard.review_count,
            "correct_count": updated_flashcard.correct_count,
            "incorrect_count": updated_flashcard.incorrect_count,
            "mastery_level": updated_flashcard.mastery_level,
            "last_reviewed": updated_flashcard.last_reviewed,
            "next_review_date": updated_flashcard.next_review_date
        }

        await flashcards_collection.update_one(
            {"id": request.flashcard_id, "user_id": str(current_user.id)},
            {"$set": update_data}
        )

        print(f"[FLASHCARD_API] ✅ Updated flashcard {request.flashcard_id} progress (correct: {request.correct})")

        return {
            "success": True,
            "flashcard_id": request.flashcard_id,
            "correct": request.correct,
            "mastery_level": updated_flashcard.mastery_level,
            "next_review_date": updated_flashcard.next_review_date.isoformat() if updated_flashcard.next_review_date else None
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[FLASHCARD_API] ❌ Error reviewing flashcard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review flashcard: {str(e)}"
        )

@router.get("/progress", response_model=FlashcardProgress)
async def get_flashcard_progress(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get overall flashcard progress statistics
    """
    try:
        user_id = str(current_user.id)
        now = datetime.utcnow()

        # Get total cards
        total_cards = await flashcards_collection.count_documents({
            "user_id": user_id,
            "is_active": True
        })

        # Get cards reviewed today
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day.replace(hour=23, minute=59, second=59, microsecond=999999)

        reviewed_today = await flashcards_collection.count_documents({
            "user_id": user_id,
            "last_reviewed": {"$gte": start_of_day, "$lte": end_of_day}
        })

        # Get cards due today
        due_today = await flashcards_collection.count_documents({
            "user_id": user_id,
            "is_active": True,
            "$or": [
                {"next_review_date": {"$lte": now}},
                {"next_review_date": None}
            ]
        })

        # Get mastered cards (high mastery level)
        mastered_cards = await flashcards_collection.count_documents({
            "user_id": user_id,
            "mastery_level": {"$gte": 0.8}
        })

        # Calculate average mastery
        mastery_pipeline = [
            {"$match": {"user_id": user_id, "is_active": True}},
            {"$group": {"_id": None, "avg_mastery": {"$avg": "$mastery_level"}}}
        ]

        mastery_result = await flashcards_collection.aggregate(mastery_pipeline).to_list(length=1)
        average_mastery = mastery_result[0]["avg_mastery"] if mastery_result else 0.0

        progress = FlashcardProgress(
            total_cards=total_cards,
            reviewed_today=reviewed_today,
            due_today=due_today,
            mastered_cards=mastered_cards,
            average_mastery=round(average_mastery, 2)
        )

        print(f"[FLASHCARD_API] Retrieved progress for user {user_id}: {total_cards} total, {due_today} due")

        return progress

    except Exception as e:
        print(f"[FLASHCARD_API] ❌ Error fetching progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch progress: {str(e)}"
        )

@router.get("/session/{session_id}", response_model=List[Flashcard])
async def get_flashcards_for_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get all flashcards for a specific session
    """
    try:
        # Find all flashcards for this session (include both active and legacy cards without is_active field)
        flashcards_cursor = flashcards_collection.find({
            "session_id": session_id,
            "user_id": str(current_user.id),
            "$or": [
                {"is_active": True},
                {"is_active": {"$exists": False}},  # Include cards where is_active field doesn't exist
                {"is_active": None}
            ]
        })

        flashcard_docs = await flashcards_cursor.to_list(length=None)

        # Convert to Flashcard objects
        flashcards = []
        for doc in flashcard_docs:
            doc.pop("_id", None)
            # Ensure is_active is set to True for legacy cards
            if "is_active" not in doc or doc["is_active"] is None:
                doc["is_active"] = True
            flashcards.append(Flashcard(**doc))

        print(f"[FLASHCARD_API] Found {len(flashcards)} flashcards for session {session_id}")

        return flashcards

    except Exception as e:
        print(f"[FLASHCARD_API] ❌ Error fetching flashcards for session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch flashcards for session: {str(e)}"
        )

@router.delete("/set/{set_id}")
async def delete_flashcard_set(
    set_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete a flashcard set and all its associated flashcards
    """
    try:
        # Find the flashcard set
        set_doc = await flashcard_sets_collection.find_one({
            "id": set_id,
            "user_id": str(current_user.id)
        })

        if not set_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flashcard set not found"
            )

        # Delete all flashcards in the set
        session_id = set_doc["session_id"]
        await flashcards_collection.delete_many({
            "session_id": session_id,
            "user_id": str(current_user.id)
        })

        # Delete the flashcard set
        await flashcard_sets_collection.delete_one({
            "id": set_id,
            "user_id": str(current_user.id)
        })

        print(f"[FLASHCARD_API] ✅ Deleted flashcard set {set_id} and associated flashcards")

        return {
            "success": True,
            "message": "Flashcard set deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[FLASHCARD_API] ❌ Error deleting flashcard set: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete flashcard set: {str(e)}"
        )

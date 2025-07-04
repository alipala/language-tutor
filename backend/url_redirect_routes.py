from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from database import database

router = APIRouter(tags=["url_redirect"])

@router.get("/s/{url_hash}")
async def redirect_shortened_url(url_hash: str):
    """
    Redirect shortened URLs to their original destinations
    """
    try:
        url_collection = database.shortened_urls
        
        # Find the original URL by hash
        url_doc = await url_collection.find_one({"hash": url_hash})
        
        if not url_doc:
            raise HTTPException(
                status_code=404,
                detail="Shortened URL not found"
            )
        
        # Increment click counter
        await url_collection.update_one(
            {"hash": url_hash},
            {"$inc": {"clicks": 1}}
        )
        
        original_url = url_doc["original_url"]
        print(f"[URL_REDIRECT] Redirecting {url_hash} to {original_url}")
        
        # Redirect to the original URL
        return RedirectResponse(url=original_url, status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[URL_REDIRECT] ❌ Error redirecting URL: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to redirect URL: {str(e)}"
        )

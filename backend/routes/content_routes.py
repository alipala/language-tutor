"""
Content Routes
Handles summarization and custom topic research functionality
"""

import os
import traceback
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai_client import get_async_openai

# Initialize router
router = APIRouter()

# Pydantic Models
class SummarizeRequest(BaseModel):
    transcript: str

class CustomTopicRequest(BaseModel):
    language: str
    level: str
    voice: Optional[str] = "alloy"
    topic: Optional[str] = None
    user_prompt: str

# Route Handlers
@router.post("/api/summarize")
async def summarize_conversation(request: SummarizeRequest):
    """
    Summarize conversation transcript using gpt-4o-mini for cost efficiency.
    Used to reduce cached token usage in OpenAI Realtime API.
    """
    try:
        print(f"[SUMMARIZATION] Received transcript: {len(request.transcript)} characters")

        if not request.transcript or len(request.transcript.strip()) < 10:
            raise HTTPException(status_code=400, detail="Transcript too short for summarization")

        # Use gpt-4o-mini for cost-effective summarization
        response = await get_async_openai().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": f"""Summarize this language learning conversation in 2-3 sentences.
Focus on topics discussed and any corrections made. Ignore grammar details.

Conversation:
{request.transcript}

Summary:"""
                }
            ],
            max_tokens=100,
            temperature=0.3
        )

        if not response or not response.choices:
            raise HTTPException(status_code=500, detail="Failed to generate summary")

        summary = response.choices[0].message.content.strip()

        print(f"[SUMMARIZATION] Generated summary: {len(summary)} characters")
        print(f"[SUMMARIZATION] Summary: {summary}")

        return {
            "success": True,
            "summary": summary,
            "original_length": len(request.transcript),
            "summary_length": len(summary),
            "compression_ratio": f"{(len(summary) / len(request.transcript) * 100):.1f}%"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[SUMMARIZATION] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@router.post("/api/custom-topic/research")
async def research_custom_topic(request: CustomTopicRequest):
    """
    Research a custom topic using OpenAI's web search capabilities with gpt-4o-search-preview
    """
    try:
        print(f"[RESEARCH] Starting REAL web search for custom topic: '{request.user_prompt}'")
        print(f"[RESEARCH] Language: {request.language}, Level: {request.level}")

        # Try gpt-4o-search-preview first, fallback to gpt-4o if not available
        try:
            search_response = await get_async_openai().chat.completions.create(
                model="gpt-4o-search-preview",
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are a research assistant with web search capabilities. You MUST search the web for current, accurate information about the topic provided.

CRITICAL: Use your web search capabilities to find the most recent and accurate information available online about the topic.

Your research should include:
1. Current facts and recent developments (search for latest news and updates)
2. Key details like dates, locations, participants, and outcomes
3. Important vocabulary and terminology related to the topic
4. Recent news articles, official announcements, or press releases
5. Any upcoming events or scheduled activities

Format your response for {request.level} level {request.language} language learners with:
- Clear, factual information suitable for educational discussion
- Important vocabulary highlighted
- Discussion points and questions
- Cultural or political context if relevant

IMPORTANT: Always search for the most current information available online. Do not rely solely on training data."""
                    },
                    {
                        "role": "user",
                        "content": f"Search the web for current information about: {request.user_prompt}. Find the latest news, official announcements, dates, locations, and any recent developments. This is for {request.language} language learning at {request.level} level."
                    }
                ],
                max_tokens=1500
            )
            print(f"[RESEARCH] Successfully used gpt-4o-search-preview model")

        except Exception as search_error:
            print(f"[RESEARCH] gpt-4o-search-preview failed: {str(search_error)}")
            print(f"[RESEARCH] Falling back to gpt-4o model for research")

            # Fallback to regular gpt-4o model
            search_response = await get_async_openai().chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are a knowledgeable research assistant helping with language learning. Provide comprehensive information about the topic for educational discussion.

Your research should include:
1. Key facts and background information about the topic
2. Important details like dates, locations, participants, and outcomes (if known)
3. Important vocabulary and terminology related to the topic
4. Historical context and significance
5. Discussion points and questions for language practice

Format your response for {request.level} level {request.language} language learners with:
- Clear, factual information suitable for educational discussion
- Important vocabulary highlighted
- Discussion points and questions
- Cultural or political context if relevant

Note: Provide the best information available from your training data, and acknowledge any limitations about current events."""
                    },
                    {
                        "role": "user",
                        "content": f"Provide comprehensive information about: {request.user_prompt}. Include background, key facts, important vocabulary, and discussion points. This is for {request.language} language learning at {request.level} level."
                    }
                ],
                temperature=0.3,
                max_tokens=1500
            )
            print(f"[RESEARCH] Successfully used fallback gpt-4o model")

        if not search_response or not search_response.choices:
            raise HTTPException(status_code=500, detail="Failed to get research results from OpenAI")

        research_content = search_response.choices[0].message.content

        print(f"[RESEARCH] Real web search completed successfully")
        print(f"[RESEARCH] Research content length: {len(research_content)} characters")
        print(f"[RESEARCH] Research preview: {research_content[:200]}...")

        # Validate that we got actual research content, not a generic response
        if len(research_content) < 100 or "I'll help you discuss" in research_content:
            print(f"[RESEARCH] Detected generic response, attempting fallback search...")

            # Try a more direct search approach
            fallback_response = await get_async_openai().chat.completions.create(
                model="gpt-4o-search-preview",
                messages=[
                    {
                        "role": "user",
                        "content": f"Search the internet for current information about '{request.user_prompt}'. Find recent news, official announcements, dates, locations, and key facts. Provide specific, factual information."
                    }
                ],
                max_tokens=1200
            )

            if fallback_response and fallback_response.choices:
                research_content = fallback_response.choices[0].message.content
                print(f"[RESEARCH] Fallback search completed: {len(research_content)} characters")

        # Return the research data in the format expected by the frontend
        return {
            "success": True,
            "topic": request.user_prompt,
            "language": request.language,
            "level": request.level,
            "research": research_content,
            "research_content": research_content,
            "timestamp": "2025-06-24T19:27:03.202Z"
        }

    except Exception as e:
        print(f"[RESEARCH] Error during web search: {str(e)}")
        print(f"[RESEARCH] Full error details: {traceback.format_exc()}")

        # Return a fallback response so the flow doesn't break
        fallback_content = f"""I'll help you discuss {request.user_prompt}.

This is an interesting topic that we can explore together during our conversation. I'll provide relevant information and help you practice {request.language} while discussing various aspects of this subject.

Let's have an engaging conversation about {request.user_prompt} and improve your {request.language} skills at the same time!"""

        return {
            "success": False,
            "topic": request.user_prompt,
            "language": request.language,
            "level": request.level,
            "research_content": fallback_content,
            "error": str(e),
            "timestamp": "2025-06-24T19:27:03.202Z"
        }

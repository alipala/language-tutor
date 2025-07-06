# Topic Selection Investigation Report

## Issue Summary
The user-selected topic from topic-selection page is not being properly passed to the tutor in the conversation. When users ask "what is the topic?", the tutor doesn't know about the selected topic.

## Investigation Findings

### 1. Topic Selection Flow Analysis

#### Frontend Flow:
1. **Topic Selection Page** (`frontend/app/topic-selection/page.tsx`)
   - ✅ User selects a topic (including custom topics)
   - ✅ Topic is stored in `sessionStorage.setItem('selectedTopic', topicId)`
   - ✅ Custom topic text is stored in `sessionStorage.setItem('customTopicText', customTopicText)`
   - ✅ Custom topic research is performed and stored in `sessionStorage.setItem('customTopicResearch', JSON.stringify(researchData))`

2. **Level Selection Page** (`frontend/app/level-selection/page.tsx`)
   - ✅ Retrieves topic from sessionStorage but doesn't use it in the conversation flow
   - ✅ Passes user to speech page

3. **Speech Page** (`frontend/app/speech/page.tsx`)
   - ✅ Retrieves topic from sessionStorage: `const topic = sessionStorage.getItem('selectedTopic')`
   - ✅ Retrieves custom prompt: `const customPrompt = sessionStorage.getItem('customTopicText')`
   - ✅ Passes topic and userPrompt to SpeechClient component

4. **Speech Client** (`frontend/app/speech/speech-client.tsx`)
   - ✅ Receives topic and userPrompt as props
   - ✅ Passes them to useRealtime hook via initialize function

5. **useRealtime Hook** (`frontend/lib/useRealtime.ts`)
   - ✅ Receives topic and userPrompt parameters
   - ✅ Stores custom topic prompt in sessionStorage
   - ✅ Passes parameters to realtimeService.initialize()

6. **Realtime Service** (`frontend/lib/realtimeService.ts`)
   - ✅ Receives topic, userPrompt, and assessmentData parameters
   - ✅ Retrieves research data from sessionStorage for custom topics
   - ✅ Passes all parameters to backend `/api/realtime/token` endpoint

### 2. Backend Analysis

#### Backend Token Generation (`backend/main.py`)
- ✅ Receives topic, user_prompt, and research_data in TutorSessionRequest
- ✅ Processes custom topics with research data
- ✅ **CRITICAL FINDING**: Creates enhanced instructions for custom topics that include:
  - The user's chosen topic
  - Research data about the topic
  - Instructions to start conversation about the specific topic
  - Instructions to keep conversation focused on the chosen topic

#### Backend Instructions Generation
For custom topics, the backend creates:
```python
custom_topic_instructions = f"The user has specifically chosen to discuss: '{request.user_prompt}'"
if web_search_results:
    custom_topic_instructions += f"CURRENT INFORMATION ABOUT THE TOPIC:\n{web_search_results}\n\n"
custom_topic_instructions += f"YOU MUST START YOUR VERY FIRST MESSAGE by discussing this exact topic..."
```

For regular topics, the backend should be adding topic-specific instructions but **THIS IS WHERE THE ISSUE IS**.

### 3. Root Cause Identified

**CRITICAL ISSUE**: The backend properly handles custom topics but does NOT handle regular topic selection (travel, food, hobbies, etc.).

In `backend/main.py`, the topic handling logic only processes custom topics:
```python
if request.topic == "custom" and request.user_prompt:
    # Custom topic processing with research and instructions
else:
    # NO PROCESSING FOR REGULAR TOPICS!
```

**The regular topics (travel, food, hobbies, culture, etc.) are completely ignored in the backend instructions.**

### 4. Missing Implementation

The backend needs to add topic-specific instructions for regular topics. Currently:

- ✅ Custom topics: Fully implemented with research and specific instructions
- ❌ Regular topics: Topic parameter is received but completely ignored in instruction generation

### 5. Solution Required

The backend needs to add topic-specific instructions for regular topics like:

```python
# After custom topic handling, add regular topic handling
elif request.topic and request.topic != "custom":
    topic_instructions = f"""
IMPORTANT TOPIC FOCUS: The user has chosen to practice {language} by discussing the topic: "{request.topic}".

YOU MUST:
1. Start your first message by introducing this topic
2. Ask engaging questions related to {request.topic}
3. Keep the conversation focused on {request.topic}
4. Provide vocabulary and phrases related to {request.topic}
5. If the user asks "what is the topic" or similar, remind them that you're discussing {request.topic}

Example first message: "Let's talk about {request.topic}! [topic-specific opening question]"
"""
    instructions = topic_instructions + "\n\n" + instructions
```

### 6. Files That Need Changes

1. **`backend/main.py`** - Add regular topic handling in the `/api/realtime/token` endpoint
2. Potentially **`backend/tutor_instructions.json`** - Add topic-specific conversation starters

### 7. Testing Steps After Fix

1. Select a regular topic (e.g., "Travel") in topic selection
2. Complete level selection and start conversation
3. Ask the tutor "What topic are we discussing?"
4. Verify the tutor knows and mentions the selected topic
5. Verify the conversation stays focused on the selected topic

## Conclusion

The issue was in the backend where regular topics were not being processed into the AI instructions, even though the topic parameter flows correctly through the entire frontend. 

## ✅ ISSUE RESOLVED

**Fix Implemented**: Added comprehensive regular topic handling to the backend `/api/realtime/token` endpoint in `backend/main.py`.

### What Was Added:

1. **Topic-Specific Instructions**: Each predefined topic (travel, food, hobbies, culture, movies, music, technology, environment) now has:
   - Detailed focus areas
   - Multiple starter questions
   - Conversation rules to keep discussions on topic
   - Clear instructions for the AI to introduce and maintain topic focus

2. **Topic Recognition**: When users ask "what is the topic?", the tutor will now clearly respond with the chosen topic name.

3. **Conversation Flow**: The AI now:
   - Starts conversations by introducing the selected topic
   - Asks engaging topic-specific questions
   - Keeps conversations focused on the chosen subject
   - Provides relevant vocabulary and phrases for each topic

### Example Implementation:
For "Travel & Tourism" topic, the AI now receives instructions to:
- Focus on destinations, transportation, accommodation, cultural experiences, travel planning, local customs
- Ask questions like "What's your favorite travel destination and why?"
- Clearly state "We're discussing Travel & Tourism" when asked about the topic

**Status**: ✅ **FIXED** - Regular topics are now properly passed to and recognized by the tutor in conversations.

**Commit**: `1e95b076045bbc4e0ed8fa6f4073f2b288424f1b`

### Additional Fix Applied:

**Commit**: `f52a424052aa8183f5b5eb203db8840b7de5e780`

**Issue**: The initial fix used complex emoji-heavy instructions that the OpenAI Realtime API might not follow properly.

**Solution**: Simplified the topic instructions to use clear, direct language without complex formatting:
- Removed emojis and complex formatting that might confuse the AI model
- Used simple, straightforward instructions that are easier for the model to follow
- Maintained topic focus while improving instruction clarity

**Example of simplified instructions**:
```
IMPORTANT: The user has chosen to discuss Travel & Tourism.

You must start your first message by introducing Travel & Tourism and asking a question about it.

If the user asks what topic you are discussing, respond: 'We are discussing Travel & Tourism'.

Keep the conversation focused on Travel & Tourism and related topics like: destinations, transportation, accommodation, cultural experiences, travel planning, local customs.

Example first message: 'Let's talk about Travel & Tourism! What's your favorite travel destination and why?'
```

This approach ensures better compliance with the OpenAI Realtime API's instruction processing.

# Background Sentence Analysis Implementation Plan

## Executive Summary

**Problem**: Users wait 30 seconds at session end (20 seconds for sentence analysis), creating poor UX.

**Solution**: Move individual sentence analysis to background processing, reduce user wait time from 30s to ~5-8s.

**Impact**: 75% reduction in session-end wait time, improved user satisfaction, better perceived performance.

---

## Current Architecture Analysis

### Current Synchronous Flow (30 seconds)
```
User completes session
    ↓
Mobile sends conversation + sentences → Backend
    ↓
Backend WAITS for BOTH (in parallel):
  - Session summary generation (5-10s)
  - Sentence analysis (15-20s) ← MAIN BLOCKER
    ↓
User sees "Analyzing..." spinner (20-25s total)
    ↓
Response returns with all analyses
    ↓
User can navigate to SentenceAnalysisScreen
```

### Target Asynchronous Flow (5-8 seconds)
```
User completes session
    ↓
Mobile sends conversation + sentences → Backend
    ↓
Backend ONLY waits for:
  - Session summary generation (5-10s)
  - Sentence analysis → BackgroundTask (non-blocking)
    ↓
Response returns immediately with stats (5-8s)
    ↓
User sees Session Summary Modal instantly
    ↓
Background: Sentence analysis runs (15-20s)
    ↓
Taal Coach notification pops up: "Analysis ready!"
    ↓
User clicks → Opens SentenceAnalysisScreen
```

---

## Implementation Strategy

### Phase 1: Backend Infrastructure
1. **MongoDB Schema for Analysis Jobs**
2. **Background Task Function**
3. **Polling Endpoint**
4. **Session Summary Endpoint Refactor**

### Phase 2: Mobile App Integration
1. **Remove Analyzing Wait Stage**
2. **Implement Polling Mechanism**
3. **Taal Coach Notification Component**
4. **Analysis Ready Flow**

---

## Detailed Backend Implementation

### 1. MongoDB Schema: Analysis Jobs Collection

**Collection Name**: `sentence_analysis_jobs`

**Schema**:
```python
{
  "_id": ObjectId,
  "job_id": str,  # UUID for this analysis job
  "user_id": str,
  "plan_id": str,
  "session_id": str,  # Link to session summary
  "status": str,  # "pending", "processing", "completed", "failed"
  "created_at": datetime,
  "started_at": datetime,  # When analysis began
  "completed_at": datetime,  # When analysis finished
  "sentences": [
    {
      "text": str,
      "timestamp": str,
    }
  ],
  "language": str,
  "level": str,
  "analyses": [  # Populated when completed
    {
      "analysis_id": str,
      "recognized_text": str,
      "grammatical_score": int,
      "vocabulary_score": int,
      "complexity_score": int,
      "appropriateness_score": int,
      "overall_score": float,
      "grammar_issues": [...],
      "improvement_suggestions": [...],
      "corrected_text": str,
      "level_appropriate_alternatives": [...],
      "timestamp": str
    }
  ],
  "error_message": str,  # If status="failed"
}
```

**Indexes**:
- `job_id` (unique)
- `user_id` + `created_at` (for user's recent jobs)
- `status` + `created_at` (for job processing queue)

---

### 2. Background Task Function

**File**: `/Users/alipala/CascadeProjects/language-tutor/backend/routes/session_summary_routes.py`

**New Function** (add around line 125):
```python
async def _run_sentence_analysis_background(
    job_id: str,
    user_id: str,
    plan_id: str,
    session_id: str,
    sentences_for_analysis: list,
    language: str,
    level: str
):
    """
    Background task: Run sentence analysis and store results.

    This runs AFTER the session summary response is sent to user.
    Updates the analysis job document with results when complete.
    """
    jobs_collection = get_mongo_db()["sentence_analysis_jobs"]

    try:
        # Update status to processing
        await jobs_collection.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": "processing",
                    "started_at": datetime.utcnow()
                }
            }
        )

        # Extract sentence texts
        sentence_texts = [s.get('text') for s in sentences_for_analysis if s.get('text')]

        if not sentence_texts:
            # No sentences to analyze
            await jobs_collection.update_one(
                {"job_id": job_id},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.utcnow(),
                        "analyses": []
                    }
                }
            )
            return

        # Run batch analysis (this is the 15-20 second operation)
        from background_sentence_analysis import batch_analyze_sentences

        analyses = await batch_analyze_sentences(
            sentences=sentence_texts,
            language=language,
            level=level
        )

        # Convert to dict format
        analyses_dict = [a.dict() for a in analyses]

        # Update job with completed analyses
        await jobs_collection.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": datetime.utcnow(),
                    "analyses": analyses_dict
                }
            }
        )

        logger.info(f"✅ Sentence analysis job {job_id} completed: {len(analyses)} sentences analyzed")

    except Exception as e:
        logger.error(f"❌ Sentence analysis job {job_id} failed: {str(e)}")

        # Update job with error
        await jobs_collection.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": "failed",
                    "completed_at": datetime.utcnow(),
                    "error_message": str(e)
                }
            }
        )
```

---

### 3. Refactor Session Summary Endpoint

**File**: `/Users/alipala/CascadeProjects/language-tutor/backend/routes/session_summary_routes.py`

**Changes to `store_session_summary()` function**:

**Before (Lines 398-427)** - REMOVE THIS:
```python
# ⚡ PARALLEL: Run summary generation + sentence analysis at the same time
async def _run_sentence_analysis():
    if not (conversation_data and "sentences_for_analysis" in conversation_data):
        return []
    sentences_for_analysis = conversation_data["sentences_for_analysis"]

    from background_sentence_analysis import batch_analyze_sentences
    sentence_texts = [s.get('text') for s in sentences_for_analysis if s.get('text')]

    # This runs in parallel with summary generation
    analyses = await batch_analyze_sentences(
        sentences=sentence_texts,
        language=plan.get("language", "english"),
        level=plan.get("proficiency_level", "B1")
    )
    return [a.dict() for a in analyses]

# Lines 424-428: BOTH summaries AND analyses wait here (blocking)
summary_data, background_analyses = await asyncio.gather(
    generate_comprehensive_session_summary(...),
    _run_sentence_analysis()
)
```

**After** - REPLACE WITH:
```python
# Generate ONLY session summary (no longer waiting for sentence analysis)
summary_data = await generate_comprehensive_session_summary(...)

# Create sentence analysis job for background processing
analysis_job_id = None
if conversation_data and "sentences_for_analysis" in conversation_data:
    sentences_for_analysis = conversation_data["sentences_for_analysis"]

    if sentences_for_analysis and len(sentences_for_analysis) > 0:
        # Generate unique job ID
        analysis_job_id = str(uuid.uuid4())

        # Create job document in MongoDB
        jobs_collection = get_mongo_db()["sentence_analysis_jobs"]
        await jobs_collection.insert_one({
            "job_id": analysis_job_id,
            "user_id": current_user.user_id,
            "plan_id": plan_id,
            "session_id": summary_id,  # Link to session summary
            "status": "pending",
            "created_at": datetime.utcnow(),
            "sentences": sentences_for_analysis,
            "language": plan.get("language", "english"),
            "level": plan.get("proficiency_level", "B1"),
            "analyses": []
        })

        # Schedule background task (runs AFTER response is sent)
        background_tasks.add_task(
            _run_sentence_analysis_background,
            job_id=analysis_job_id,
            user_id=current_user.user_id,
            plan_id=plan_id,
            session_id=summary_id,
            sentences_for_analysis=sentences_for_analysis,
            language=plan.get("language", "english"),
            level=plan.get("proficiency_level", "B1")
        )

background_analyses = []  # Empty - will be populated by background job
```

**Update Response (Lines 659-676)**:
```python
return {
    "success": True,
    "message": "Session summary stored successfully",
    "completed_sessions": completed_sessions,
    "progress_percentage": progress_percentage,
    "current_week": current_week,
    "session_summary": summary_data.get("summary", "No summary available."),
    "background_analyses": [],  # NOW EMPTY - being processed in background
    "analysis_job_id": analysis_job_id,  # NEW: Job ID for polling
    "analysis_status": "processing" if analysis_job_id else "none",  # NEW
    "flashcards_generated": flashcard_generation_success_count,
    "flashcard_generation_success": True,
    # ... rest of response
}
```

---

### 4. New Polling Endpoint

**File**: `/Users/alipala/CascadeProjects/language-tutor/backend/routes/session_summary_routes.py`

**New Endpoint** (add after `store_session_summary`):
```python
@router.get("/api/learning/sentence-analysis-status/{job_id}")
async def get_sentence_analysis_status(
    job_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Poll for sentence analysis job status and results.

    Returns:
    - status: "pending", "processing", "completed", "failed"
    - analyses: Array of sentence analyses (when completed)
    - progress: Estimated progress percentage
    """
    jobs_collection = get_mongo_db()["sentence_analysis_jobs"]

    # Find job
    job = await jobs_collection.find_one({
        "job_id": job_id,
        "user_id": current_user.user_id  # Security: ensure user owns this job
    })

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Analysis job not found"
        )

    # Calculate progress estimate
    progress = 0
    if job["status"] == "pending":
        progress = 0
    elif job["status"] == "processing":
        # Estimate based on time elapsed
        if job.get("started_at"):
            elapsed = (datetime.utcnow() - job["started_at"]).total_seconds()
            # Assume 20 seconds total processing time
            progress = min(int((elapsed / 20) * 100), 95)
        else:
            progress = 10
    elif job["status"] == "completed":
        progress = 100
    elif job["status"] == "failed":
        progress = 0

    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": progress,
        "created_at": job["created_at"].isoformat(),
        "started_at": job.get("started_at").isoformat() if job.get("started_at") else None,
        "completed_at": job.get("completed_at").isoformat() if job.get("completed_at") else None,
        "analyses": job.get("analyses", []),
        "error_message": job.get("error_message"),
        "sentence_count": len(job.get("sentences", []))
    }
```

---

## Detailed Mobile App Implementation

### 1. Update ConversationScreen: Remove Analyzing Wait

**File**: `/Users/alipala/github/MyTacoAIMobile/src/screens/Practice/ConversationScreen.tsx`

**Changes**:

**Add State for Analysis Job** (around line 100):
```typescript
const [analysisJobId, setAnalysisJobId] = useState<string | null>(null);
const [analysisStatus, setAnalysisStatus] = useState<'none' | 'processing' | 'completed' | 'failed'>('none');
const [showAnalysisNotification, setShowAnalysisNotification] = useState(false);
```

**Refactor `handleAutomaticSessionEnd()` (Lines 1596-1632)**:

**REMOVE**:
```typescript
// Old code that waits for analysis
setSavingStage('analyzing');  // ← REMOVE THIS STAGE
```

**REPLACE WITH**:
```typescript
// New code: Save analysis job ID from response
if (result.analysis_job_id) {
  setAnalysisJobId(result.analysis_job_id);
  setAnalysisStatus('processing');

  // Start polling for analysis completion (non-blocking)
  startPollingAnalysisStatus(result.analysis_job_id);
}

// Set stage to finalizing immediately (no wait)
setSavingStage('finalizing');
```

**Handle Response (Lines 1633-1680)**:

**CHANGE**:
```typescript
// Old: Expect background_analyses in response
if (result.background_analyses) {
  setBackgroundAnalyses(result.background_analyses);
}
```

**TO**:
```typescript
// New: background_analyses will be empty initially
// Analysis will be fetched via polling when ready
setBackgroundAnalyses([]);  // Empty until polling completes

// Store job ID for polling
if (result.analysis_job_id) {
  setAnalysisJobId(result.analysis_job_id);
  setAnalysisStatus(result.analysis_status || 'processing');
}
```

---

### 2. Implement Polling Mechanism

**File**: `/Users/alipala/github/MyTacoAIMobile/src/screens/Practice/ConversationScreen.tsx`

**Add Polling Function** (around line 1000):
```typescript
const startPollingAnalysisStatus = useCallback((jobId: string) => {
  const pollInterval = 2000; // Poll every 2 seconds
  const maxPolls = 30; // Maximum 60 seconds of polling
  let pollCount = 0;

  const pollTimer = setInterval(async () => {
    pollCount++;

    try {
      const token = await AsyncStorage.getItem('authToken');
      if (!token) {
        clearInterval(pollTimer);
        return;
      }

      const response = await fetch(
        `${API_BASE_URL}/api/learning/sentence-analysis-status/${jobId}`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch analysis status');
      }

      const data = await response.json();

      console.log(`📊 Analysis poll ${pollCount}: status=${data.status}, progress=${data.progress}%`);

      if (data.status === 'completed') {
        // Analysis is ready!
        clearInterval(pollTimer);
        setAnalysisStatus('completed');
        setBackgroundAnalyses(data.analyses);

        // Show Taal Coach notification
        setShowAnalysisNotification(true);

        console.log('✅ Sentence analysis completed:', data.analyses.length, 'sentences');

      } else if (data.status === 'failed') {
        clearInterval(pollTimer);
        setAnalysisStatus('failed');
        console.error('❌ Sentence analysis failed:', data.error_message);

      } else if (pollCount >= maxPolls) {
        // Timeout after 60 seconds
        clearInterval(pollTimer);
        console.warn('⚠️ Analysis polling timeout - still processing');
      }

    } catch (error) {
      console.error('Error polling analysis status:', error);
      pollCount++;

      if (pollCount >= maxPolls) {
        clearInterval(pollTimer);
      }
    }
  }, pollInterval);

  // Cleanup on unmount
  return () => clearInterval(pollTimer);
}, []);
```

**Add useEffect for Cleanup**:
```typescript
useEffect(() => {
  // Cleanup polling when component unmounts
  return () => {
    if (analysisJobId && analysisStatus === 'processing') {
      console.log('Cleaning up analysis polling on unmount');
    }
  };
}, [analysisJobId, analysisStatus]);
```

---

### 3. Create Taal Coach Notification Component

**File**: `/Users/alipala/github/MyTacoAIMobile/src/components/TaalCoachNotification.tsx` (NEW FILE)

```typescript
import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Dimensions,
  Platform,
} from 'react-native';
import LottieView from 'lottie-react-native';
import { LinearGradient } from 'expo-linear-gradient';

const { width } = Dimensions.get('window');

interface TaalCoachNotificationProps {
  visible: boolean;
  title: string;
  message: string;
  buttonText: string;
  onButtonPress: () => void;
  onDismiss: () => void;
  duration?: number; // Auto-dismiss after duration (ms)
}

const TaalCoachNotification: React.FC<TaalCoachNotificationProps> = ({
  visible,
  title,
  message,
  buttonText,
  onButtonPress,
  onDismiss,
  duration = 8000,
}) => {
  const slideAnim = useRef(new Animated.Value(-200)).current;
  const scaleAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      // Animate in
      Animated.parallel([
        Animated.spring(slideAnim, {
          toValue: Platform.OS === 'ios' ? 50 : 20,
          useNativeDriver: true,
          tension: 50,
          friction: 7,
        }),
        Animated.spring(scaleAnim, {
          toValue: 1,
          useNativeDriver: true,
          tension: 50,
          friction: 7,
        }),
      ]).start();

      // Auto-dismiss after duration
      const timer = setTimeout(() => {
        handleDismiss();
      }, duration);

      return () => clearTimeout(timer);
    } else {
      // Animate out
      Animated.parallel([
        Animated.timing(slideAnim, {
          toValue: -200,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.timing(scaleAnim, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [visible]);

  const handleDismiss = () => {
    Animated.parallel([
      Animated.timing(slideAnim, {
        toValue: -200,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnim, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start(() => {
      onDismiss();
    });
  };

  if (!visible) return null;

  return (
    <Animated.View
      style={[
        styles.container,
        {
          transform: [
            { translateY: slideAnim },
            { scale: scaleAnim },
          ],
        },
      ]}
    >
      <LinearGradient
        colors={['#6366F1', '#8B5CF6']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.gradient}
      >
        <TouchableOpacity
          style={styles.content}
          onPress={onButtonPress}
          activeOpacity={0.95}
        >
          {/* Taal Coach Lottie Animation */}
          <View style={styles.lottieContainer}>
            <LottieView
              source={require('../assets/animations/taal-coach.json')}
              autoPlay
              loop
              style={styles.lottie}
            />
          </View>

          {/* Content */}
          <View style={styles.textContainer}>
            <Text style={styles.title}>{title}</Text>
            <Text style={styles.message}>{message}</Text>

            <View style={styles.buttonContainer}>
              <Text style={styles.buttonText}>{buttonText}</Text>
              <Text style={styles.arrow}>→</Text>
            </View>
          </View>

          {/* Dismiss button */}
          <TouchableOpacity
            style={styles.dismissButton}
            onPress={handleDismiss}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Text style={styles.dismissText}>✕</Text>
          </TouchableOpacity>
        </TouchableOpacity>
      </LinearGradient>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 20,
    right: 20,
    zIndex: 9999,
    elevation: 999,
  },
  gradient: {
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  lottieContainer: {
    width: 60,
    height: 60,
    marginRight: 12,
  },
  lottie: {
    width: '100%',
    height: '100%',
  },
  textContainer: {
    flex: 1,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  message: {
    fontSize: 14,
    fontWeight: '400',
    color: '#E0E7FF',
    marginBottom: 8,
  },
  buttonContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  buttonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
    marginRight: 4,
  },
  arrow: {
    fontSize: 16,
    color: '#FFFFFF',
  },
  dismissButton: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 8,
  },
  dismissText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});

export default TaalCoachNotification;
```

---

### 4. Integrate Notification in ConversationScreen

**File**: `/Users/alipala/github/MyTacoAIMobile/src/screens/Practice/ConversationScreen.tsx`

**Import Component** (top of file):
```typescript
import TaalCoachNotification from '../components/TaalCoachNotification';
```

**Add to Render** (before closing `</SafeAreaView>`):
```typescript
{/* Taal Coach Notification for Analysis Completion */}
<TaalCoachNotification
  visible={showAnalysisNotification}
  title="Analysis Ready!"
  message="Your speech analysis is complete. See how you did!"
  buttonText="View Analysis"
  onButtonPress={() => {
    setShowAnalysisNotification(false);
    handleViewAnalysis();
  }}
  onDismiss={() => setShowAnalysisNotification(false)}
  duration={10000}
/>
```

**Update `handleViewAnalysis()` Function** (Lines 1891-1929):
```typescript
const handleViewAnalysis = () => {
  // Check if analyses are ready
  if (backgroundAnalyses && backgroundAnalyses.length > 0) {
    navigation.navigate('SentenceAnalysis', {
      analyses: backgroundAnalyses,
      sessionSummary: sessionSummary,
      duration: formatDuration(sessionDuration),
      messageCount: messages.filter(m => m.role === 'user').length,
    });
  } else if (analysisStatus === 'processing') {
    // Still processing - show toast
    Alert.alert(
      'Analysis In Progress',
      'Your speech analysis is still processing. We\'ll notify you when it\'s ready!',
      [{ text: 'OK' }]
    );
  } else if (analysisStatus === 'failed') {
    Alert.alert(
      'Analysis Failed',
      'Sorry, we couldn\'t complete your speech analysis. Please try again later.',
      [{ text: 'OK' }]
    );
  } else {
    Alert.alert(
      'No Analysis Available',
      'No sentence analysis is available for this session.',
      [{ text: 'OK' }]
    );
  }
};
```

---

## Testing Plan

### Backend Testing

1. **Test Background Job Creation**:
   - Complete a session with sentences
   - Verify job document created in `sentence_analysis_jobs` collection
   - Verify `status="pending"` initially

2. **Test Background Task Execution**:
   - Monitor logs for task execution
   - Verify status changes: `pending` → `processing` → `completed`
   - Verify `analyses` array populated with results

3. **Test Polling Endpoint**:
   - Call `/api/learning/sentence-analysis-status/{job_id}`
   - Verify returns correct status
   - Verify progress estimation
   - Verify security (user can only access their own jobs)

4. **Test Error Handling**:
   - Simulate OpenAI API failure
   - Verify job status changes to `failed`
   - Verify `error_message` populated

### Mobile App Testing

1. **Test Instant Response**:
   - Complete a session
   - Verify session summary modal appears in 5-8 seconds (no 20-second wait)
   - Verify "Analyzing" stage removed

2. **Test Polling**:
   - Monitor console logs for polling requests
   - Verify polling happens every 2 seconds
   - Verify polling stops when analysis completes

3. **Test Notification**:
   - Wait for analysis completion
   - Verify Taal Coach notification appears
   - Verify notification auto-dismisses after 10 seconds
   - Verify manual dismiss works

4. **Test Analysis Navigation**:
   - Click notification button
   - Verify navigates to `SentenceAnalysisScreen`
   - Verify analyses display correctly

5. **Test Edge Cases**:
   - Session with no sentences (verify no polling)
   - Polling timeout (verify graceful handling)
   - Network error during polling (verify retry)
   - User navigates away before analysis completes (verify cleanup)

---

## Performance Impact

### Before (Synchronous)
| Stage | Duration |
|-------|----------|
| Session summary generation | 5-10s |
| Sentence analysis | 15-20s |
| **Total user wait** | **20-30s** |

### After (Asynchronous)
| Stage | Duration |
|-------|----------|
| Session summary generation | 5-10s |
| **Total user wait** | **5-10s** |
| Sentence analysis (background) | 15-20s (non-blocking) |

### Improvement
- **75% reduction** in perceived wait time
- User can view session stats immediately
- Analysis delivered via notification when ready
- Better UX: User not blocked by processing

---

## Database Impact

### New Collection
- `sentence_analysis_jobs`: ~1KB per job
- Indexed on `job_id`, `user_id`, `status`
- Recommended cleanup: Delete jobs older than 30 days

### Storage Estimate
- 1000 sessions/day × 1KB = 1MB/day
- 30 days = 30MB storage
- Minimal impact on MongoDB

---

## Rollout Strategy

### Phase 1: Backend (1-2 hours)
1. Deploy MongoDB schema
2. Deploy background task function
3. Deploy polling endpoint
4. Deploy session summary refactor

### Phase 2: Mobile App (2-3 hours)
1. Deploy polling mechanism
2. Deploy notification component
3. Deploy UI updates
4. Test complete flow

### Phase 3: Monitoring (ongoing)
1. Monitor job completion rates
2. Monitor polling performance
3. Monitor notification engagement
4. Track user satisfaction improvement

---

## Rollback Plan

If issues arise:
1. Revert session summary endpoint to synchronous analysis
2. Disable polling in mobile app
3. Remove notification component
4. Keep MongoDB schema (no data loss)

---

## Success Metrics

- **User wait time**: 30s → 5-8s (75% reduction)
- **Analysis completion rate**: >99%
- **Notification click-through rate**: >60%
- **User satisfaction**: Measured via app store reviews

---

## Conclusion

This implementation moves sentence analysis to background processing, dramatically improving UX by reducing session-end wait time from 30 seconds to 5-8 seconds. The Taal Coach notification provides a delightful way to notify users when analysis is ready, maintaining engagement while improving perceived performance.

**Key Benefits**:
- 75% faster session completion
- Better user experience
- Scalable architecture (leverages existing BackgroundTasks pattern)
- Minimal database impact
- Easy rollback if needed

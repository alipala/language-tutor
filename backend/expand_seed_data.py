"""
Expand seed data to include B1, B2, C1, C2 levels
Quick expansion to ensure all CEFR levels are covered
"""

import asyncio
from datetime import datetime
from database import init_db, database


def generate_additional_challenges():
    """Generate challenges for B1-C2 levels"""

    challenges = []

    # B1 Level - 6 challenges (one per type)
    challenges.extend([
        {
            "id": "es_b1_1",
            "type": "error_spotting",
            "title": "Spot the Mistake",
            "emoji": "🧩",
            "description": "Can you spot the error?",
            "cefrLevel": "B1",
            "estimatedSeconds": 14,
            "sentence": "If I would have time, I would help you.",
            "options": [
                {"id": "opt1", "text": "If I would have", "isCorrect": True},
                {"id": "opt2", "text": "time", "isCorrect": False},
                {"id": "opt3", "text": "would help you", "isCorrect": False}
            ],
            "explanation": "Use 'had' in the if-clause, not 'would have'",
            "correctedSentence": "If I had time, I would help you.",
            "tags": ["conditionals", "second_conditional"],
            "completed": False
        },
        {
            "id": "sf_b1_1",
            "type": "swipe_fix",
            "title": "You Struggled With This",
            "emoji": "🔄",
            "description": "Swipe to learn the difference",
            "cefrLevel": "B1",
            "estimatedSeconds": 15,
            "concept": "Make vs Do",
            "examples": [
                {"text": "I need to make my homework", "isCorrect": False, "explanation": "Use 'do' with homework, not 'make'"},
                {"text": "I need to do my homework", "isCorrect": True, "explanation": "Perfect! We 'do' homework, exercises, and tasks"}
            ],
            "tags": ["collocations", "make_do"],
            "completed": False
        },
        {
            "id": "mq_b1_1",
            "type": "micro_quiz",
            "title": "Quick Quiz",
            "emoji": "⚡",
            "description": "Choose wisely",
            "cefrLevel": "B1",
            "estimatedSeconds": 10,
            "question": "Which preposition fits? \"I'm interested ___ learning Spanish.\"",
            "options": [
                {"id": "opt1", "text": "in", "isCorrect": True},
                {"id": "opt2", "text": "on", "isCorrect": False},
                {"id": "opt3", "text": "at", "isCorrect": False}
            ],
            "explanation": "We use 'interested in' for hobbies and activities",
            "tags": ["prepositions", "interested_in"],
            "completed": False
        },
        {
            "id": "fc_b1_1",
            "type": "smart_flashcard",
            "title": "Smart Flashcard",
            "emoji": "📚",
            "description": "Word you misused",
            "cefrLevel": "B1",
            "estimatedSeconds": 12,
            "word": "get used to",
            "context": "Expressing habits",
            "explanation": "To become familiar with something over time (+ noun/gerund)",
            "exampleSentence": "I'm getting used to waking up early for work.",
            "tags": ["phrasal_verbs", "habits"],
            "completed": False
        },
        {
            "id": "nc_b1_1",
            "type": "native_check",
            "title": "Would a Native Say This?",
            "emoji": "🧠",
            "description": "Natural phrasing?",
            "cefrLevel": "B1",
            "estimatedSeconds": 12,
            "sentence": "I did a travel to Spain last summer.",
            "isNatural": False,
            "correctedVersion": "I traveled to Spain last summer.",
            "explanation": "'Travel' is usually a verb in this context, not 'do a travel'",
            "tags": ["collocations", "travel"],
            "completed": False
        },
        {
            "id": "bt_b1_1",
            "type": "brain_tickler",
            "title": "10-Second Challenge",
            "emoji": "⏱️",
            "description": "Fast decision!",
            "cefrLevel": "B1",
            "estimatedSeconds": 10,
            "timeLimit": 10,
            "question": "Complete: \"I wish I ___ rich.\"",
            "options": [
                {"id": "opt1", "text": "am", "isCorrect": False},
                {"id": "opt2", "text": "were", "isCorrect": True},
                {"id": "opt3", "text": "will be", "isCorrect": False}
            ],
            "explanation": "Use 'were' (not 'was') for hypothetical wishes",
            "tags": ["wish_sentences", "subjunctive"],
            "completed": False
        },
    ])

    # B2 Level - 6 challenges
    challenges.extend([
        {
            "id": "es_b2_1",
            "type": "error_spotting",
            "title": "Spot the Mistake",
            "emoji": "🧩",
            "description": "Find the subtle error",
            "cefrLevel": "B2",
            "estimatedSeconds": 15,
            "sentence": "Despite of the rain, we went hiking.",
            "options": [
                {"id": "opt1", "text": "Despite of", "isCorrect": True},
                {"id": "opt2", "text": "the rain", "isCorrect": False},
                {"id": "opt3", "text": "went hiking", "isCorrect": False}
            ],
            "explanation": "Use 'Despite' without 'of' or use 'In spite of'",
            "correctedSentence": "Despite the rain, we went hiking.",
            "tags": ["connectors", "prepositions"],
            "completed": False
        },
        {
            "id": "sf_b2_1",
            "type": "swipe_fix",
            "title": "You Struggled With This",
            "emoji": "🔄",
            "description": "Compare the nuance",
            "cefrLevel": "B2",
            "estimatedSeconds": 15,
            "concept": "Affect vs Effect",
            "examples": [
                {"text": "The weather will affect the game", "isCorrect": True, "explanation": "'Affect' is usually a verb meaning to influence"},
                {"text": "The weather will have an effect on the game", "isCorrect": True, "explanation": "'Effect' is usually a noun meaning the result"}
            ],
            "tags": ["vocabulary", "affect_effect"],
            "completed": False
        },
        {
            "id": "mq_b2_1",
            "type": "micro_quiz",
            "title": "Quick Quiz",
            "emoji": "⚡",
            "description": "Make the right choice",
            "cefrLevel": "B2",
            "estimatedSeconds": 12,
            "question": "Choose the most natural phrase:",
            "options": [
                {"id": "opt1", "text": "I am agree with you", "isCorrect": False},
                {"id": "opt2", "text": "I agree with you", "isCorrect": True},
                {"id": "opt3", "text": "I am agreeing with you", "isCorrect": False}
            ],
            "explanation": "'Agree' is a state, not an action. Don't use continuous form",
            "tags": ["stative_verbs"],
            "completed": False
        },
        {
            "id": "fc_b2_1",
            "type": "smart_flashcard",
            "title": "Smart Flashcard",
            "emoji": "📚",
            "description": "Tricky phrase",
            "cefrLevel": "B2",
            "estimatedSeconds": 15,
            "word": "take for granted",
            "context": "Idiomatic expressions",
            "explanation": "To fail to appreciate something because you're too familiar with it",
            "exampleSentence": "We often take our health for granted until we get sick.",
            "tags": ["idioms", "phrasal_verbs"],
            "completed": False
        },
        {
            "id": "nc_b2_1",
            "type": "native_check",
            "title": "Would a Native Say This?",
            "emoji": "🧠",
            "description": "Does this sound natural?",
            "cefrLevel": "B2",
            "estimatedSeconds": 12,
            "sentence": "I'm looking forward to meet you.",
            "isNatural": False,
            "correctedVersion": "I'm looking forward to meeting you.",
            "explanation": "Use gerund (-ing) after 'looking forward to', not infinitive",
            "tags": ["gerunds", "phrasal_verbs"],
            "completed": False
        },
        {
            "id": "bt_b2_1",
            "type": "brain_tickler",
            "title": "10-Second Challenge",
            "emoji": "⏱️",
            "description": "Race against time!",
            "cefrLevel": "B2",
            "estimatedSeconds": 10,
            "timeLimit": 10,
            "question": "Which sentence is passive?",
            "options": [
                {"id": "opt1", "text": "She wrote the report", "isCorrect": False},
                {"id": "opt2", "text": "The report was written", "isCorrect": True},
                {"id": "opt3", "text": "She is writing now", "isCorrect": False}
            ],
            "explanation": "Passive voice uses 'be' + past participle",
            "tags": ["passive_voice", "grammar"],
            "completed": False
        },
    ])

    # C1 Level - 6 challenges
    challenges.extend([
        {
            "id": "es_c1_1",
            "type": "error_spotting",
            "title": "Spot the Mistake",
            "emoji": "🧩",
            "description": "Catch the subtle mistake",
            "cefrLevel": "C1",
            "estimatedSeconds": 15,
            "sentence": "The data suggests that climate change is accelerating.",
            "options": [
                {"id": "opt1", "text": "The data suggests", "isCorrect": True},
                {"id": "opt2", "text": "climate change", "isCorrect": False},
                {"id": "opt3", "text": "is accelerating", "isCorrect": False}
            ],
            "explanation": "'Data' is often plural in formal writing - use 'suggest'",
            "correctedSentence": "The data suggest that climate change is accelerating.",
            "tags": ["formal_writing", "subject_verb_agreement"],
            "completed": False
        },
        {
            "id": "sf_c1_1",
            "type": "swipe_fix",
            "title": "You Struggled With This",
            "emoji": "🔄",
            "description": "Subtle distinction",
            "cefrLevel": "C1",
            "estimatedSeconds": 18,
            "concept": "Imply vs Infer",
            "examples": [
                {"text": "The speaker implied that changes were coming", "isCorrect": True, "explanation": "'Imply' means to suggest indirectly (speaker's action)"},
                {"text": "The audience inferred that changes were coming", "isCorrect": True, "explanation": "'Infer' means to conclude from evidence (listener's action)"}
            ],
            "tags": ["vocabulary_precision", "imply_infer"],
            "completed": False
        },
        {
            "id": "mq_c1_1",
            "type": "micro_quiz",
            "title": "Quick Quiz",
            "emoji": "⚡",
            "description": "Advanced choice",
            "cefrLevel": "C1",
            "estimatedSeconds": 12,
            "question": "Which sounds most natural?",
            "options": [
                {"id": "opt1", "text": "The meeting was very productive", "isCorrect": False},
                {"id": "opt2", "text": "The meeting proved highly productive", "isCorrect": True},
                {"id": "opt3", "text": "The meeting was much productive", "isCorrect": False}
            ],
            "explanation": "'Proved highly' is more formal and sophisticated than 'very'",
            "tags": ["formal_language", "adverbs"],
            "completed": False
        },
        {
            "id": "fc_c1_1",
            "type": "smart_flashcard",
            "title": "Smart Flashcard",
            "emoji": "📚",
            "description": "Advanced usage",
            "cefrLevel": "C1",
            "estimatedSeconds": 15,
            "word": "nuanced",
            "context": "Sophisticated description",
            "explanation": "Characterized by subtle shades of meaning or expression",
            "exampleSentence": "Her nuanced understanding of the issue impressed the committee.",
            "tags": ["advanced_vocabulary", "formal"],
            "completed": False
        },
        {
            "id": "nc_c1_1",
            "type": "native_check",
            "title": "Would a Native Say This?",
            "emoji": "🧠",
            "description": "Native-like?",
            "cefrLevel": "C1",
            "estimatedSeconds": 15,
            "sentence": "The findings underscore the need for immediate action.",
            "isNatural": True,
            "correctedVersion": None,
            "explanation": "Excellent! This is sophisticated and natural academic English",
            "tags": ["academic_writing", "formal"],
            "completed": False
        },
        {
            "id": "bt_c1_1",
            "type": "brain_tickler",
            "title": "10-Second Challenge",
            "emoji": "⏱️",
            "description": "Think fast!",
            "cefrLevel": "C1",
            "estimatedSeconds": 10,
            "timeLimit": 10,
            "question": "Which is a causative structure?",
            "options": [
                {"id": "opt1", "text": "I cut my hair", "isCorrect": False},
                {"id": "opt2", "text": "I had my hair cut", "isCorrect": True},
                {"id": "opt3", "text": "I was cutting hair", "isCorrect": False}
            ],
            "explanation": "'Have something done' shows someone else performed the action",
            "tags": ["causative", "grammar"],
            "completed": False
        },
    ])

    # C2 Level - 6 challenges
    challenges.extend([
        {
            "id": "es_c2_1",
            "type": "error_spotting",
            "title": "Spot the Mistake",
            "emoji": "🧩",
            "description": "Advanced error detection",
            "cefrLevel": "C2",
            "estimatedSeconds": 18,
            "sentence": "She was reticent to share her opinion on the matter.",
            "options": [
                {"id": "opt1", "text": "reticent to", "isCorrect": True},
                {"id": "opt2", "text": "share her opinion", "isCorrect": False},
                {"id": "opt3", "text": "on the matter", "isCorrect": False}
            ],
            "explanation": "'Reticent' means unwilling to speak. Use 'reluctant to' for unwillingness to act",
            "correctedSentence": "She was reluctant to share her opinion on the matter.",
            "tags": ["vocabulary_precision", "near_synonyms"],
            "completed": False
        },
        {
            "id": "sf_c2_1",
            "type": "swipe_fix",
            "title": "You Struggled With This",
            "emoji": "🔄",
            "description": "Advanced nuance",
            "cefrLevel": "C2",
            "estimatedSeconds": 20,
            "concept": "Disinterested vs Uninterested",
            "examples": [
                {"text": "He was uninterested in the proposal", "isCorrect": True, "explanation": "'Uninterested' means not interested or bored"},
                {"text": "A judge must be disinterested", "isCorrect": True, "explanation": "'Disinterested' means impartial, without bias"}
            ],
            "tags": ["vocabulary_precision", "near_synonyms"],
            "completed": False
        },
        {
            "id": "mq_c2_1",
            "type": "micro_quiz",
            "title": "Quick Quiz",
            "emoji": "⚡",
            "description": "Expert decision",
            "cefrLevel": "C2",
            "estimatedSeconds": 15,
            "question": "Select the most precise usage:",
            "options": [
                {"id": "opt1", "text": "The proposal was turned down", "isCorrect": False},
                {"id": "opt2", "text": "The proposal was rejected", "isCorrect": False},
                {"id": "opt3", "text": "The proposal was summarily dismissed", "isCorrect": True}
            ],
            "explanation": "'Summarily dismissed' conveys abruptness and finality with precision",
            "tags": ["advanced_vocabulary", "formal"],
            "completed": False
        },
        {
            "id": "fc_c2_1",
            "type": "smart_flashcard",
            "title": "Smart Flashcard",
            "emoji": "📚",
            "description": "Expert-level term",
            "cefrLevel": "C2",
            "estimatedSeconds": 18,
            "word": "ubiquitous",
            "context": "Formal vocabulary",
            "explanation": "Present, appearing, or found everywhere",
            "exampleSentence": "Smartphones have become ubiquitous in modern society.",
            "tags": ["advanced_vocabulary", "formal"],
            "completed": False
        },
        {
            "id": "nc_c2_1",
            "type": "native_check",
            "title": "Would a Native Say This?",
            "emoji": "🧠",
            "description": "Expert check",
            "cefrLevel": "C2",
            "estimatedSeconds": 15,
            "sentence": "The data was analyzed meticulously.",
            "isNatural": False,
            "correctedVersion": "The data were analyzed meticulously.",
            "explanation": "In formal writing, 'data' is often treated as plural",
            "tags": ["formal_writing", "subject_verb_agreement"],
            "completed": False
        },
        {
            "id": "bt_c2_1",
            "type": "brain_tickler",
            "title": "10-Second Challenge",
            "emoji": "⏱️",
            "description": "Expert speed test!",
            "cefrLevel": "C2",
            "estimatedSeconds": 10,
            "timeLimit": 10,
            "question": "Identify the subjunctive mood:",
            "options": [
                {"id": "opt1", "text": "If I was rich...", "isCorrect": False},
                {"id": "opt2", "text": "I suggest that he leave", "isCorrect": True},
                {"id": "opt3", "text": "He might come", "isCorrect": False}
            ],
            "explanation": "Subjunctive uses base form after suggest/demand/insist",
            "tags": ["subjunctive", "grammar"],
            "completed": False
        },
    ])

    return challenges


async def expand_seed_data():
    """Add B1-C2 challenges to database"""
    try:
        print("[EXPAND] 🌱 Expanding seed data with B1-C2 levels...")

        await init_db()

        challenges_collection = database.challenges

        # Generate additional challenges
        new_challenges = generate_additional_challenges()

        # Add timestamps
        for challenge in new_challenges:
            challenge["created_at"] = datetime.utcnow()
            challenge["updated_at"] = datetime.utcnow()

        # Insert
        if new_challenges:
            result = await challenges_collection.insert_many(new_challenges)
            print(f"[EXPAND] ✅ Inserted {len(result.inserted_ids)} new challenges")

        # Verify totals
        total = await challenges_collection.count_documents({})
        print(f"\n[EXPAND] 📊 Total challenges now: {total}")

        # Count by level
        for level in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            count = await challenges_collection.count_documents({'cefrLevel': level})
            print(f"[EXPAND]   - {level}: {count}")

        print("\n[EXPAND] 🎉 Expansion complete!")

    except Exception as e:
        print(f"[EXPAND] ❌ Error: {str(e)}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(expand_seed_data())

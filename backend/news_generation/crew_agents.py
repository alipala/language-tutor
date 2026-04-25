"""
CrewAI Agents for News Generation
Defines specialized agents for search, safety assessment, summarization, and vocabulary

NOTE: CrewAI is optional for MVP. System works with template-based generation.
For full LLM-based generation, install: pip install crewai langchain-openai
"""

import os
from typing import List, Dict, Any
import logging
from dotenv import load_dotenv

# Load environment
load_dotenv()

logger = logging.getLogger(__name__)

# CrewAI imports (optional - for full LLM generation)
try:
    from crewai import Agent, Task, Crew, Process
    CREWAI_AVAILABLE = True
    logger.info("[NEWS_AGENTS] CrewAI available for LLM-based generation")
except ImportError:
    logger.info("[NEWS_AGENTS] CrewAI not available - using MVP template-based generation")
    CREWAI_AVAILABLE = False
    Agent = None
    Task = None
    Crew = None
    Process = None

# Configuration - Use same model as existing crew (gpt-4o)
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o")
GPT_MODEL_MINI = "gpt-4o-mini"  # For cheaper vocabulary generation

# MVP Configuration
MVP_ARTICLE_COUNT = 5  # Target 5 articles per day
MVP_LANGUAGES = ["en", "es", "nl", "pt", "de", "fr"]  # English, Spanish, Dutch, Portuguese, German, French
MVP_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]  # All 6 CEFR proficiency levels

# CEFR Level Requirements
LEVEL_REQUIREMENTS = {
    "A1": {
        "word_count_range": (50, 80),
        "vocabulary_count": (6, 8),
        "sentence_length_max": 8,
        "description": "ABSOLUTE BEGINNER level - Use ONLY the most basic, common words. ONLY present tense. NO subordinate clauses. NO complex grammar. Subject-Verb-Object structure only. AI tutor MUST NOT introduce vocabulary beyond basic everyday words."
    },
    "A2": {
        "word_count_range": (80, 120),
        "vocabulary_count": (8, 10),
        "sentence_length_max": 12,
        "description": "ELEMENTARY level - Use basic, familiar vocabulary only. Simple present and simple past tense. NO subjunctive, NO passive voice, NO complex conditionals. Simple compound sentences OK. AI tutor MUST stay within elementary vocabulary during conversation."
    },
    "B1": {
        "word_count_range": (120, 180),
        "vocabulary_count": (10, 12),
        "sentence_length_max": 18,
        "description": "Intermediate vocabulary, mix of simple and compound sentences"
    },
    "B2": {
        "word_count_range": (180, 250),
        "vocabulary_count": (12, 15),
        "sentence_length_max": 25,
        "description": "Advanced vocabulary, complex sentences with clauses, idioms"
    },
    "C1": {
        "word_count_range": (250, 350),
        "vocabulary_count": (15, 18),
        "sentence_length_max": 30,
        "description": "Sophisticated vocabulary, complex grammatical structures, nuanced expressions"
    },
    "C2": {
        "word_count_range": (350, 500),
        "vocabulary_count": (18, 22),
        "sentence_length_max": 35,
        "description": "Native-like vocabulary, highly complex sentences, subtle expressions, idiomatic language"
    }
}


def create_search_agent():
    """
    Agent 1: News Curator
    Finds educational, engaging news articles from the past 24 hours
    """
    if not CREWAI_AVAILABLE:
        return None

    return Agent(
        role="News Curator for Language Learners",
        goal=f"Find {MVP_ARTICLE_COUNT}-8 diverse, educational news articles published in the last 24 hours",
        backstory="""You are an expert at finding engaging, educational news content
        perfect for language learners. You focus on articles about Technology, Science,
        Culture, Sports, Environment, Health, Education, and Business Innovation.
        You avoid controversial, violent, or distressing content.""",
        llm=GPT_MODEL,  # Use string model name like existing pattern
        verbose=True,
        allow_delegation=False
    )


def create_safety_agent():
    """
    Agent 2: Content Safety Evaluator
    Filters out inappropriate content using safety scoring
    """
    if not CREWAI_AVAILABLE:
        return None

    return Agent(
        role="Content Safety Evaluator",
        goal="Filter news articles to ensure they are safe and appropriate for language learners",
        backstory="""You are a content safety specialist who evaluates articles on three criteria:
        1. Violence Score (0-10): Violent content, conflict, distressing imagery
        2. Controversy Score (0-10): Political, religious, divisive topics
        3. Educational Value Score (0-10): Learning potential, vocabulary richness

        Approval criteria: Violence < 3, Controversy < 5, Educational Value > 6

        You protect learners from distressing content while maximizing educational value.""",
        llm=GPT_MODEL,
        verbose=True,
        allow_delegation=False
    )


def create_summarization_agent():
    """
    Agent 3: CEFR Content Adapter
    Adapts news articles for different proficiency levels
    """
    if not CREWAI_AVAILABLE:
        return None

    return Agent(
        role="CEFR Content Adaptation Specialist",
        goal="Adapt news articles to appropriate CEFR levels (A1, A2, B1, B2, C1, C2) for language learners with STRICT level adherence",
        backstory="""You are an expert language pedagogy specialist who adapts content
        to match CEFR proficiency levels. You understand how to simplify or enrich
        language while maintaining the core message and interest of the article.

        You follow STRICT CEFR guidelines for word count, sentence complexity, and vocabulary.

        CRITICAL for A1/A2 levels:
        - A1: ABSOLUTE BEGINNER - Use only the 500 most common words, present tense only
        - A2: ELEMENTARY - Use only basic familiar words, simple present/past tense only
        - You provide detailed AI tutor instructions that enforce level boundaries
        - AI tutor instructions MUST warn against vocabulary/grammar drift beyond the level
        - For A1/A2, AI tutor MUST simplify and rephrase if learner shows confusion

        Your AI instructions ensure the conversation stays strictly within the proficiency level.""",
        llm=GPT_MODEL,
        verbose=True,
        allow_delegation=False
    )


def create_vocabulary_agent():
    """
    Agent 4: Vocabulary List Generator
    Creates level-appropriate vocabulary lists with translations and examples
    """
    if not CREWAI_AVAILABLE:
        return None

    return Agent(
        role="Vocabulary Teaching Specialist",
        goal="Generate level-appropriate vocabulary lists with translations, examples, and pronunciation",
        backstory="""You are a vocabulary teaching expert who creates useful word lists
        for language learners. You select words that are relevant to the article content,
        appropriate for the learner's level, and provide clear examples and translations.

        You also generate 3-4 engaging discussion questions to help learners practice
        speaking about the topic.""",
        llm=GPT_MODEL_MINI,  # Use cheaper model for vocabulary
        verbose=True,
        allow_delegation=False
    )


def create_search_task(agent: Agent) -> Task:
    """
    Task for News Curator: Search for candidate articles
    """
    return Task(
        description=f"""Search for {MVP_ARTICLE_COUNT}-8 educational news articles published in the last 24 hours.

        Focus on these categories:
        - Technology and Innovation
        - Science and Discovery
        - Culture and Arts
        - Sports and Athletics
        - Environment and Nature
        - Health and Wellness
        - Education and Learning
        - Business Innovation

        For each article, provide:
        1. Title
        2. URL
        3. Source (publication name)
        4. Category
        5. Brief summary (2-3 sentences)
        6. Image URL (if available)
        7. Published date/time

        Return a JSON list of articles.

        AVOID these topics:
        - War, military conflict, violence
        - Politics, elections, government controversy
        - Crime, disasters, tragic events
        - Celebrity gossip or scandal
        - Religious or cultural conflicts
        """,
        agent=agent,
        expected_output="JSON list of 5-8 news articles with complete metadata"
    )


def create_safety_task(agent: Agent, articles: List[Dict[str, Any]]) -> Task:
    """
    Task for Safety Evaluator: Filter safe articles
    """
    return Task(
        description=f"""Evaluate these {len(articles)} articles for safety and educational value.

        For each article, provide scores (0-10):
        1. Violence Score: 0 = no violence, 10 = extremely violent
        2. Controversy Score: 0 = non-controversial, 10 = highly divisive
        3. Educational Value: 0 = no learning value, 10 = excellent for learning

        Approval criteria:
        - Violence Score < 3
        - Controversy Score < 5
        - Educational Value > 6

        Return only approved articles with their safety scores.
        Aim to approve at least {MVP_ARTICLE_COUNT} articles.

        Articles to evaluate:
        {articles}
        """,
        agent=agent,
        expected_output=f"JSON list of {MVP_ARTICLE_COUNT}+ approved articles with safety scores"
    )


def create_summarization_task(
    agent: Agent,
    article: Dict[str, Any],
    language: str,
    level: str
) -> Task:
    """
    Task for Content Adapter: Adapt article for specific language and level
    """
    level_req = LEVEL_REQUIREMENTS[level]

    # Language-specific instructions
    language_names = {
        "en": "English",
        "es": "Spanish",
        "nl": "Dutch",
        "pt": "Portuguese",
        "de": "German",
        "fr": "French"
    }

    return Task(
        description=f"""Adapt this news article for {language_names[language]} language learners at {level} level.

        Original Article:
        Title: {article.get('title', '')}
        Summary: {article.get('summary', '')}

        CEFR {level} Requirements:
        - Word count: {level_req['word_count_range'][0]}-{level_req['word_count_range'][1]} words
        - Sentence length: Maximum {level_req['sentence_length_max']} words per sentence
        - {level_req['description']}

        **CRITICAL: Write the ENTIRE summary text IN THE {language_names[language]} LANGUAGE (language code: {language})**

        Create an adapted summary that:
        1. Maintains the key facts and interest of the story
        2. Uses level-appropriate vocabulary and grammar for {level}
        3. Is engaging and encourages conversation
        4. Follows CEFR {level} guidelines strictly
        5. Is written COMPLETELY in {language_names[language]} - not English!

        Also provide:
        - AI tutor instructions: Detailed guidance (in English) for the AI conversation partner that:
          * Lists MAXIMUM vocabulary complexity allowed (based on {level})
          * Specifies EXACT grammar structures to use/avoid
          * Defines sentence complexity limits (max {level_req['sentence_length_max']} words/sentence)
          * For A1/A2: Emphasizes staying STRICTLY within beginner level - NO advanced vocabulary or grammar
          * For A1/A2: Tutor must simplify/rephrase if learner doesn't understand
          * For A1/A2: Use present tense primarily, avoid complex past/future constructions
          * Provides conversation strategies to keep discussion at {level} level
          * Warns tutor NOT to drift beyond {level} vocabulary/grammar during conversation

        Return JSON with:
        {{
            "summary": "adapted summary text IN {language_names[language]}",
            "word_count": <actual count>,
            "ai_instructions": "Strict level-appropriate guidance for AI tutor (in English). MUST include vocabulary limits, grammar constraints, sentence complexity rules, and explicit warnings to stay at {level} level."
        }}
        """,
        agent=agent,
        expected_output="JSON with adapted summary, word count, and AI instructions"
    )


def create_vocabulary_task(
    agent: Agent,
    article: Dict[str, Any],
    summary: str,
    language: str,
    level: str
) -> Task:
    """
    Task for Vocabulary Specialist: Create vocabulary list and discussion questions
    """
    level_req = LEVEL_REQUIREMENTS[level]
    vocab_count = level_req['vocabulary_count']

    language_names = {
        "en": "English",
        "es": "Spanish",
        "nl": "Dutch",
        "pt": "Portuguese",
        "de": "German",
        "fr": "French"
    }

    return Task(
        description=f"""Generate a vocabulary list and discussion questions for this adapted news article.

        Article Title: {article.get('title', '')}
        Adapted Summary: {summary}
        Target Language: {language_names[language]} (language code: {language})
        Level: {level}

        **CRITICAL: All vocabulary items and discussion questions MUST be in {language_names[language]} language!**

        Create {vocab_count[0]}-{vocab_count[1]} vocabulary items that:
        1. Are relevant to the article content
        2. Are appropriate for {level} level learners
        3. Help learners discuss the topic

        For each vocabulary item, provide:
        - word: The word in {language_names[language]}
        - translation: Translation to English (if language is not English) or definition in English
        - example: A simple example sentence using the word IN {language_names[language]}
        - ipa: IPA pronunciation (optional, if helpful)

        Also create 3-4 discussion questions IN {language_names[language]} that:
        - Encourage learners to express opinions
        - Practice past tense, present tense, or future tense as appropriate for {level}
        - Are open-ended and interesting
        - Help practice the vocabulary words
        - Are written COMPLETELY in {language_names[language]} - not English!

        Return JSON with:
        {{
            "vocabulary": [
                {{
                    "word": "example word in {language_names[language]}",
                    "translation": "English translation or definition",
                    "example": "Example sentence in {language_names[language]}",
                    "ipa": "/ɪɡˈzæmpəl/"
                }},
                ...
            ],
            "discussion_questions": [
                "Question in {language_names[language]}...",
                "Another question in {language_names[language]}...",
                ...
            ]
        }}
        """,
        agent=agent,
        expected_output="JSON with vocabulary list and discussion questions"
    )

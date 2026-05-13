"""
tutor_config.py
===============
Single source of truth for the AI tutor's session configuration.

Contains:
  - TOPIC_CATALOGUE  : 20 predefined topics with full metadata for every
                       CEFR level (A1-C2), including target-language vocabulary,
                       subtopic progression arcs, and emoji markers.
  - SESSION_PACING   : Duration-aware phase timing for 1 / 3 / 5 minute sessions.
  - Helper functions : get_topic_config(), get_session_pacing()

Design principles
-----------------
* All vocabulary is given in ENGLISH and notes say "use these in {language}" so
  the AI tutor translates them into the target language naturally.  Giving Dutch
  vocabulary here would hard-code one language; the tutor handles all languages.
* Subtopic arcs are ordered short → long so slicing [:n] always produces a
  coherent progression for any session duration.
* This module has NO external dependencies — import it anywhere safely.
"""

from typing import Dict, Any, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# TOPIC CATALOGUE
# ─────────────────────────────────────────────────────────────────────────────

TOPIC_CATALOGUE: Dict[str, Dict[str, Any]] = {

    # ── daily-routine ────────────────────────────────────────────────────────
    "daily-routine": {
        "id":          "daily-routine",
        # These aliases cover every raw ID the frontend might send
        "aliases":     ["daily", "daily_routine", "dailyroutine"],
        "display_name": "Daily Routines",
        "emoji":       "morning",
        "description": (
            "Talk about what you do every day: morning habits, meals, "
            "work or school, evening activities, and bedtime."
        ),
        # Key vocabulary per CEFR level (English labels — tutor uses target language)
        "vocabulary": {
            "A1": [
                "wake up", "get up", "wash", "eat", "drink", "sleep",
                "go to work", "go home", "morning", "evening",
                "breakfast", "lunch", "dinner",
            ],
            "A2": [
                "shower", "get dressed", "commute", "arrive", "finish work",
                "cook dinner", "watch TV", "go to bed", "daily schedule",
                "every day", "usually", "sometimes",
            ],
            "B1": [
                "routine", "habit", "productive", "relax", "manage time",
                "alarm clock", "rush hour", "work from home",
                "leisure time", "balance",
            ],
            "B2": [
                "work-life balance", "prioritise", "juggle responsibilities",
                "flexible schedule", "remote work", "efficiency",
                "downtime", "multitask",
            ],
            "C1": [
                "regimented", "ad hoc", "compartmentalise", "optimise workflow",
                "circadian rhythm", "mindfulness routine", "burnout",
            ],
            "C2": [
                "idiomatic expressions of habit", "nuanced time management discourse",
                "register shifts between formal and informal",
            ],
        },
        # Subtopic arcs — ordered from simplest to richest
        # slice to fit session length: 1 min → 1 arc, 3 min → 2 arcs, 5 min → 3+ arcs
        "subtopic_arcs": [
            {
                "name": "Morning routine",
                "questions": [
                    "What time do you wake up?",
                    "What do you do first in the morning?",
                    "Do you eat breakfast?",
                ],
                "emoji": "morning",
            },
            {
                "name": "Meals during the day",
                "questions": [
                    "What do you usually eat for breakfast / lunch / dinner?",
                    "Do you cook at home or eat out?",
                    "What is your favourite meal of the day?",
                ],
                "emoji": "bread",
            },
            {
                "name": "Work or school",
                "questions": [
                    "What time do you start work / school?",
                    "How do you get there?",
                    "What do you do in the afternoon?",
                ],
                "emoji": "office",
            },
            {
                "name": "Evening and free time",
                "questions": [
                    "What do you do in the evening?",
                    "Do you watch TV or use your phone?",
                    "What time do you go to sleep?",
                ],
                "emoji": "night",
            },
        ],
    },

    # ── travel ────────────────────────────────────────────────────────────────
    "travel": {
        "id":          "travel",
        "aliases":     ["traveling", "travelling", "tourism"],
        "display_name": "Travel & Tourism",
        "emoji":       "airplane",
        "description": (
            "Discuss travel destinations, trips you have taken or want to take, "
            "transport, accommodation, and cultural experiences."
        ),
        "vocabulary": {
            "A1": [
                "go to", "by plane", "by train", "by bus", "hotel",
                "beach", "city", "country", "visa", "passport", "ticket",
            ],
            "A2": [
                "book a hotel", "check in", "check out", "suitcase", "airport",
                "departure", "arrival", "holiday", "trip", "destination",
            ],
            "B1": [
                "itinerary", "tour guide", "local customs", "budget travel",
                "backpacking", "package holiday", "sightseeing", "jet lag",
            ],
            "B2": [
                "off the beaten track", "travel insurance", "cultural immersion",
                "sustainable tourism", "spontaneous trip", "travel hack",
            ],
            "C1": [
                "wanderlust", "nomadic lifestyle", "ecotourism", "gentrification",
                "overtourism", "digital nomad",
            ],
            "C2": [
                "socio-political implications of tourism", "nuanced cultural commentary",
                "idiomatic travel expressions",
            ],
        },
        "subtopic_arcs": [
            {
                "name": "Where you have been",
                "questions": [
                    "Have you travelled to another country?",
                    "Where did you go? When?",
                    "Did you like it?",
                ],
                "emoji": "airplane",
            },
            {
                "name": "How you travel",
                "questions": [
                    "Do you prefer planes, trains, or cars?",
                    "Do you book hotels or Airbnb?",
                    "Do you travel alone or with others?",
                ],
                "emoji": "train",
            },
            {
                "name": "Dream destination",
                "questions": [
                    "Where would you love to go?",
                    "Why does that place interest you?",
                    "What would you do there?",
                ],
                "emoji": "sunny",
            },
            {
                "name": "Travel experiences and tips",
                "questions": [
                    "What was the best trip you have taken?",
                    "What went wrong on a trip?",
                    "What advice would you give a first-time visitor to your country?",
                ],
                "emoji": "camera",
            },
        ],
    },

    # ── food ──────────────────────────────────────────────────────────────────
    "food": {
        "id":          "food",
        "aliases":     ["cooking", "cuisine", "eating"],
        "display_name": "Food & Cooking",
        "emoji":       "pizza",
        "description": (
            "Talk about favourite foods, cuisines, cooking habits, "
            "restaurants, dietary preferences, and cultural food traditions."
        ),
        "vocabulary": {
            "A1": [
                "eat", "drink", "like", "don't like", "bread", "rice",
                "meat", "fish", "vegetables", "fruit", "water", "coffee", "tea",
            ],
            "A2": [
                "cook", "recipe", "ingredient", "delicious", "taste",
                "sweet", "salty", "spicy", "restaurant", "menu", "order",
            ],
            "B1": [
                "cuisine", "dish", "portion", "vegetarian", "vegan",
                "allergy", "diet", "homemade", "takeaway", "reservation",
            ],
            "B2": [
                "gastronomy", "Michelin-starred", "fusion cuisine",
                "food pairing", "farm-to-table", "dietary restriction",
            ],
            "C1": [
                "culinary tradition", "umami", "fermentation", "foraging",
                "food sovereignty", "nose-to-tail cooking",
            ],
            "C2": [
                "sociocultural role of food", "nuanced culinary vocabulary",
                "idiomatic food expressions",
            ],
        },
        "subtopic_arcs": [
            {
                "name": "Favourite foods",
                "questions": [
                    "What is your favourite food?",
                    "Do you prefer sweet or savoury?",
                    "What food do you eat every day?",
                ],
                "emoji": "pizza",
            },
            {
                "name": "Cooking at home",
                "questions": [
                    "Do you cook? What do you make?",
                    "What is the easiest thing you can cook?",
                    "What is your favourite recipe?",
                ],
                "emoji": "bread",
            },
            {
                "name": "Restaurants and eating out",
                "questions": [
                    "Do you go to restaurants often?",
                    "What type of restaurant do you prefer?",
                    "What is the best meal you have had at a restaurant?",
                ],
                "emoji": "restaurant",
            },
            {
                "name": "Cultural food traditions",
                "questions": [
                    "What traditional food is popular in your country?",
                    "Is there a food you tried abroad that you loved?",
                    "How has food culture changed in your lifetime?",
                ],
                "emoji": "salad",
            },
        ],
    },

    # ── family ────────────────────────────────────────────────────────────────
    "family": {
        "id":          "family",
        "aliases":     ["relationships", "family-life"],
        "display_name": "Family & Relationships",
        "emoji":       "family",
        "description": (
            "Discuss family members, relationships, traditions, "
            "and how family life shapes who we are."
        ),
        "vocabulary": {
            "A1": [
                "mother", "father", "sister", "brother", "son", "daughter",
                "grandparent", "family", "married", "single", "children",
            ],
            "A2": [
                "cousin", "aunt", "uncle", "close family", "live with",
                "grow up", "tradition", "celebrate", "holiday together",
            ],
            "B1": [
                "relationship", "bond", "generation", "upbringing",
                "family values", "independent", "supportive",
            ],
            "B2": [
                "nuclear family", "extended family", "cultural expectations",
                "work-family balance", "family dynamics",
            ],
            "C1": [
                "multigenerational household", "patriarchal / matriarchal",
                "intergenerational conflict", "role model",
            ],
            "C2": [
                "sociological perspectives on family", "evolving family structures",
                "nuanced discussion of relationships",
            ],
        },
        "subtopic_arcs": [
            {
                "name": "Your family members",
                "questions": [
                    "How many people are in your family?",
                    "Do you have brothers or sisters?",
                    "Where does your family live?",
                ],
                "emoji": "family",
            },
            {
                "name": "Family activities and traditions",
                "questions": [
                    "What do you do together as a family?",
                    "Do you celebrate any special traditions?",
                    "What is a typical family meal like in your home?",
                ],
                "emoji": "bread",
            },
            {
                "name": "Relationships and support",
                "questions": [
                    "Who are you closest to in your family?",
                    "How does your family support each other?",
                    "What have you learned from your parents?",
                ],
                "emoji": "love",
            },
            {
                "name": "Family and culture",
                "questions": [
                    "How important is family in your culture?",
                    "How has family life changed compared to your grandparents' time?",
                    "What values do you want to pass on to the next generation?",
                ],
                "emoji": "friends",
            },
        ],
    },

    # ── work ──────────────────────────────────────────────────────────────────
    "work": {
        "id":          "work",
        "aliases":     ["career", "job", "profession"],
        "display_name": "Work & Career",
        "emoji":       "office",
        "description": (
            "Discuss jobs, career goals, workplace situations, "
            "professional development, and work-life balance."
        ),
        "vocabulary": {
            "A1": [
                "job", "work", "office", "boss", "colleague",
                "start", "finish", "morning", "afternoon", "tired",
            ],
            "A2": [
                "salary", "interview", "apply for a job", "experience",
                "meeting", "project", "deadline", "team", "manager",
            ],
            "B1": [
                "career", "promotion", "skills", "responsibilities",
                "flexible hours", "remote work", "freelance", "networking",
            ],
            "B2": [
                "work-life balance", "corporate culture", "job satisfaction",
                "entrepreneur", "leadership", "redundancy", "burnout",
            ],
            "C1": [
                "professional development", "glass ceiling", "organisational hierarchy",
                "disruptive innovation", "talent acquisition",
            ],
            "C2": [
                "macroeconomic employment trends", "nuanced professional discourse",
                "idiomatic business expressions",
            ],
        },
        "subtopic_arcs": [
            {
                "name": "Your current job",
                "questions": [
                    "What do you do for work?",
                    "Where do you work?",
                    "Do you like your job?",
                ],
                "emoji": "office",
            },
            {
                "name": "Daily work life",
                "questions": [
                    "What do you do on a typical work day?",
                    "Do you work with a team or alone?",
                    "What is the best and worst part of your job?",
                ],
                "emoji": "computer",
            },
            {
                "name": "Career goals",
                "questions": [
                    "What would your dream job be?",
                    "Are you happy in your current career?",
                    "What skills do you want to develop?",
                ],
                "emoji": "writing",
            },
            {
                "name": "Work-life balance",
                "questions": [
                    "How do you switch off after work?",
                    "Do you think people work too much in your country?",
                    "What changes would make working life better?",
                ],
                "emoji": "happy",
            },
        ],
    },

    # ── health ────────────────────────────────────────────────────────────────
    "health": {
        "id":          "health",
        "aliases":     ["fitness", "wellness", "sport"],
        "display_name": "Health & Fitness",
        "emoji":       "doctor",
        "description": (
            "Talk about exercise, healthy habits, medical topics, "
            "mental wellness, and lifestyle choices."
        ),
        "vocabulary": {
            "A1": [
                "sick", "tired", "happy", "doctor", "hospital",
                "medicine", "sleep", "eat well", "exercise",
            ],
            "A2": [
                "healthy food", "go running", "gym", "headache",
                "cold", "fever", "appointment", "diet",
            ],
            "B1": [
                "physical fitness", "mental health", "stress", "nutrition",
                "work out", "injury", "recovery", "wellbeing",
            ],
            "B2": [
                "preventative healthcare", "chronic condition", "holistic health",
                "mindfulness", "work-related stress", "sedentary lifestyle",
            ],
            "C1": [
                "healthcare system", "epidemiology", "psychosomatic",
                "cognitive health", "evidence-based medicine",
            ],
            "C2": [
                "bioethics", "healthcare policy discourse",
                "nuanced discussion of public health",
            ],
        },
        "subtopic_arcs": [
            {
                "name": "Exercise habits",
                "questions": [
                    "Do you exercise? What do you do?",
                    "How often do you exercise?",
                    "Do you prefer indoor or outdoor activities?",
                ],
                "emoji": "running",
            },
            {
                "name": "Eating and lifestyle",
                "questions": [
                    "Do you try to eat healthily?",
                    "What is your biggest unhealthy habit?",
                    "How much sleep do you usually get?",
                ],
                "emoji": "salad",
            },
            {
                "name": "Mental health",
                "questions": [
                    "How do you manage stress?",
                    "What do you do to relax?",
                    "Do you think mental health is talked about enough?",
                ],
                "emoji": "happy",
            },
            {
                "name": "Healthcare and medical experiences",
                "questions": [
                    "When did you last see a doctor?",
                    "What is the healthcare system like in your country?",
                    "What do you think is the most important health habit?",
                ],
                "emoji": "doctor",
            },
        ],
    },

    # ── hobbies ───────────────────────────────────────────────────────────────
    "hobbies": {
        "id":          "hobbies",
        "aliases":     ["interests", "free-time", "leisure"],
        "display_name": "Hobbies & Interests",
        "emoji":       "music",
        "description": (
            "Share favourite activities, creative pursuits, personal interests, "
            "and how you spend your free time."
        ),
        "vocabulary": {
            "A1": [
                "like", "love", "music", "sport", "read", "watch",
                "play", "game", "free time", "weekend",
            ],
            "A2": [
                "hobby", "interest", "go swimming", "paint", "cook",
                "travel", "meet friends", "cinema", "concert",
            ],
            "B1": [
                "passion", "spare time", "pursue", "creative",
                "collect", "volunteer", "club", "competition",
            ],
            "B2": [
                "dedicated hobbyist", "professional vs amateur",
                "niche interest", "side project", "work-hobby balance",
            ],
            "C1": [
                "intrinsic motivation", "flow state", "craftmanship",
                "renaissance person", "esoteric interest",
            ],
            "C2": [
                "philosophical value of leisure", "idiomatic hobby expressions",
                "nuanced discussion of creativity",
            ],
        },
        "subtopic_arcs": [
            {
                "name": "Main hobbies",
                "questions": [
                    "What do you do in your free time?",
                    "Do you have a hobby?",
                    "Did you start that hobby recently or long ago?",
                ],
                "emoji": "music",
            },
            {
                "name": "How you practise your hobby",
                "questions": [
                    "How often do you do your hobby?",
                    "Do you do it alone or with others?",
                    "Have you ever competed or performed?",
                ],
                "emoji": "soccer",
            },
            {
                "name": "Hobbies you want to try",
                "questions": [
                    "Is there a hobby you would love to start?",
                    "What stops you from trying it?",
                    "What hobby do you think is underrated?",
                ],
                "emoji": "camera",
            },
            {
                "name": "Hobbies and identity",
                "questions": [
                    "How has your hobby changed you?",
                    "Could your hobby become your career?",
                    "What would life be like without hobbies?",
                ],
                "emoji": "happy",
            },
        ],
    },

    # ── technology ────────────────────────────────────────────────────────────
    "technology": {
        "id":          "technology",
        "aliases":     ["tech", "digital", "internet", "gadgets"],
        "display_name": "Technology & Digital Life",
        "emoji":       "phone",
        "description": (
            "Discuss gadgets, apps, social media, digital trends, "
            "and how technology shapes daily life."
        ),
        "vocabulary": {
            "A1": [
                "phone", "computer", "internet", "email", "photo",
                "app", "good", "bad", "like", "use",
            ],
            "A2": [
                "smartphone", "social media", "message", "video call",
                "search", "download", "online shopping", "password",
            ],
            "B1": [
                "technology", "digital", "privacy", "screen time",
                "artificial intelligence", "automation", "update",
            ],
            "B2": [
                "cybersecurity", "data privacy", "algorithm", "cloud",
                "digital literacy", "disruptive technology",
            ],
            "C1": [
                "surveillance capitalism", "net neutrality", "blockchain",
                "machine learning", "ethical AI",
            ],
            "C2": [
                "sociotechnical systems", "techno-determinism",
                "nuanced debate on tech regulation",
            ],
        },
        "subtopic_arcs": [
            {
                "name": "Devices you use",
                "questions": [
                    "What devices do you use every day?",
                    "Is your phone important to you?",
                    "How many hours a day do you use your phone?",
                ],
                "emoji": "phone",
            },
            {
                "name": "Social media and apps",
                "questions": [
                    "Do you use social media? Which ones?",
                    "What apps can you not live without?",
                    "Do you think social media is good or bad?",
                ],
                "emoji": "computer",
            },
            {
                "name": "Technology at work or school",
                "questions": [
                    "How does technology help you at work or school?",
                    "Has AI changed how you work?",
                    "What tech skill do you wish you had?",
                ],
                "emoji": "writing",
            },
            {
                "name": "Future of technology",
                "questions": [
                    "What technology will change the world most in the next 10 years?",
                    "Are you worried about privacy online?",
                    "Could robots take your job?",
                ],
                "emoji": "tv",
            },
        ],
    },

    # ── environment ───────────────────────────────────────────────────────────
    "environment": {
        "id":          "environment",
        "aliases":     ["nature", "climate", "ecology", "sustainability"],
        "display_name": "Environment & Nature",
        "emoji":       "sunny",
        "description": (
            "Explore environmental issues, sustainability, the natural world, "
            "conservation, and eco-friendly practices."
        ),
        "vocabulary": {
            "A1": [
                "sun", "rain", "water", "tree", "animal",
                "clean", "dirty", "good", "bad", "big",
            ],
            "A2": [
                "weather", "recycle", "pollution", "nature",
                "park", "sea", "forest", "protect", "save",
            ],
            "B1": [
                "environment", "climate change", "renewable energy",
                "carbon footprint", "endangered species", "eco-friendly",
            ],
            "B2": [
                "sustainability", "fossil fuels", "deforestation",
                "greenhouse gases", "biodiversity", "green energy",
            ],
            "C1": [
                "climate policy", "Paris Agreement", "decarbonisation",
                "circular economy", "environmental justice",
            ],
            "C2": [
                "geopolitics of climate", "nuanced environmental discourse",
                "intergenerational equity",
            ],
        },
        "subtopic_arcs": [
            {
                "name": "Your connection to nature",
                "questions": [
                    "Do you like being outdoors?",
                    "What is nature like where you live?",
                    "Do you have a favourite natural place?",
                ],
                "emoji": "sunny",
            },
            {
                "name": "Everyday eco habits",
                "questions": [
                    "Do you recycle?",
                    "How do you try to help the environment?",
                    "Do you use public transport or a bike?",
                ],
                "emoji": "bicycle",
            },
            {
                "name": "Climate change concerns",
                "questions": [
                    "Do you think climate change is serious?",
                    "How has the weather changed in your country?",
                    "What should governments do about climate change?",
                ],
                "emoji": "rainy",
            },
            {
                "name": "Solutions and future",
                "questions": [
                    "What can individuals do to help the planet?",
                    "Do you feel hopeful or worried about the environment?",
                    "What technology might save the environment?",
                ],
                "emoji": "sunny",
            },
        ],
    },

    # ── education ────────────────────────────────────────────────────────────
    "education": {
        "id":          "education",
        "aliases":     ["school", "learning", "study", "university"],
        "display_name": "Education & Learning",
        "emoji":       "school",
        "description": (
            "Talk about school, university, learning experiences, "
            "educational goals, and study methods."
        ),
        "vocabulary": {
            "A1": [
                "school", "teacher", "student", "book", "read",
                "write", "learn", "class", "exam", "good",
            ],
            "A2": [
                "subject", "maths", "science", "language", "grade",
                "homework", "study", "university", "course", "diploma",
            ],
            "B1": [
                "degree", "curriculum", "skills", "self-study",
                "online learning", "scholarship", "revision", "assignment",
            ],
            "B2": [
                "higher education", "critical thinking", "lifelong learning",
                "academic pressure", "learning style", "pedagogy",
            ],
            "C1": [
                "educational reform", "Socratic method", "interdisciplinary",
                "cognitive development", "meritocracy",
            ],
            "C2": [
                "philosophy of education", "nuanced academic discourse",
                "educational inequality",
            ],
        },
        "subtopic_arcs": [
            {
                "name": "Your school experience",
                "questions": [
                    "Where did you go to school?",
                    "What was your favourite subject?",
                    "Did you enjoy school?",
                ],
                "emoji": "school",
            },
            {
                "name": "Learning styles",
                "questions": [
                    "How do you learn best?",
                    "Do you prefer reading books or watching videos?",
                    "Have you ever taken an online course?",
                ],
                "emoji": "book",
            },
            {
                "name": "Education and career",
                "questions": [
                    "Did your education prepare you for work?",
                    "Would you go back to school to learn something new?",
                    "What subject would you study if you could choose anything?",
                ],
                "emoji": "writing",
            },
            {
                "name": "Education systems and reform",
                "questions": [
                    "What is good and bad about the education system in your country?",
                    "Should university be free?",
                    "What skill is NOT taught at school but should be?",
                ],
                "emoji": "books",
            },
        ],
    },

    # ── shopping ──────────────────────────────────────────────────────────────
    "shopping": {
        "id":          "shopping",
        "aliases":     ["money", "buying", "consumer"],
        "display_name": "Shopping & Money",
        "emoji":       "store",
        "description": (
            "Discuss shopping experiences, prices, budgeting, "
            "financial topics, and consumer choices."
        ),
        "vocabulary": {
            "A1": [
                "buy", "sell", "money", "expensive", "cheap",
                "store", "price", "good", "pay", "have",
            ],
            "A2": [
                "supermarket", "market", "clothes", "food shopping",
                "receipt", "sale", "discount", "credit card", "cash",
            ],
            "B1": [
                "budget", "afford", "compare prices", "online shopping",
                "return policy", "brand", "quality", "impulsive buy",
            ],
            "B2": [
                "consumer behaviour", "sustainable fashion", "fast fashion",
                "financial literacy", "investing", "debt",
            ],
            "C1": [
                "consumerism", "planned obsolescence", "ethical consumption",
                "financial independence", "economic mobility",
            ],
            "C2": [
                "macroeconomic consumer trends", "nuanced financial discourse",
                "idiomatic money expressions",
            ],
        },
        "subtopic_arcs": [
            {
                "name": "Shopping habits",
                "questions": [
                    "Do you like shopping?",
                    "Where do you usually shop?",
                    "Do you prefer online or in-store shopping?",
                ],
                "emoji": "store",
            },
            {
                "name": "What you buy",
                "questions": [
                    "What do you spend most money on?",
                    "Did you buy something recently that you loved?",
                    "Do you ever buy things you don't need?",
                ],
                "emoji": "money",
            },
            {
                "name": "Budget and saving",
                "questions": [
                    "Do you have a budget?",
                    "Are you a saver or a spender?",
                    "What is the most expensive thing you have bought?",
                ],
                "emoji": "money",
            },
            {
                "name": "Consumer values",
                "questions": [
                    "Do you care about where products are made?",
                    "Do you think people buy too much?",
                    "How has online shopping changed society?",
                ],
                "emoji": "happy",
            },
        ],
    },

    # ── movies ────────────────────────────────────────────────────────────────
    "movies": {
        "id":          "movies",
        "aliases":     ["films", "tv", "cinema", "series", "tv-shows"],
        "display_name": "Movies & TV Shows",
        "emoji":       "tv",
        "description": (
            "Discuss films, series, actors, directors, entertainment preferences, "
            "genres, and media consumption."
        ),
        "vocabulary": {
            "A1": [
                "film", "watch", "like", "good", "bad", "actor",
                "funny", "sad", "happy", "action",
            ],
            "A2": [
                "cinema", "series", "genre", "comedy", "drama",
                "director", "character", "scene", "recommend",
            ],
            "B1": [
                "plot", "storyline", "special effects", "soundtrack",
                "award-winning", "documentary", "sequel", "adaptation",
            ],
            "B2": [
                "cinematography", "narrative structure", "social commentary",
                "streaming platform", "binge-watch", "cult classic",
            ],
            "C1": [
                "auteur", "mise-en-scène", "subtext", "allegory",
                "film theory", "representation in media",
            ],
            "C2": [
                "philosophy of film", "media studies discourse",
                "nuanced critique of cultural representation",
            ],
        },
        "subtopic_arcs": [
            {
                "name": "Favourite movies or shows",
                "questions": [
                    "What is your favourite film or series?",
                    "What genre do you prefer?",
                    "Did you watch anything recently?",
                ],
                "emoji": "tv",
            },
            {
                "name": "How you watch",
                "questions": [
                    "Do you watch at home or at the cinema?",
                    "Which streaming service do you use?",
                    "Do you watch with others or alone?",
                ],
                "emoji": "home",
            },
            {
                "name": "Opinions and recommendations",
                "questions": [
                    "What film would you recommend?",
                    "What is an overrated film?",
                    "Who is your favourite actor or director?",
                ],
                "emoji": "happy",
            },
            {
                "name": "Films and society",
                "questions": [
                    "Can a film change how you think about something?",
                    "Should films always have a happy ending?",
                    "What important topics should films explore more?",
                ],
                "emoji": "book",
            },
        ],
    },

    # ── music ─────────────────────────────────────────────────────────────────
    "music": {
        "id":          "music",
        "aliases":     ["arts", "art", "culture", "concerts"],
        "display_name": "Music & Arts",
        "emoji":       "music",
        "description": (
            "Talk about music genres, artists, concerts, creative arts, "
            "and artistic expression."
        ),
        "vocabulary": {
            "A1": [
                "music", "song", "like", "listen", "good", "bad",
                "play", "guitar", "piano", "loud", "quiet",
            ],
            "A2": [
                "singer", "band", "concert", "album", "genre",
                "pop", "rock", "classical", "dance", "favourite",
            ],
            "B1": [
                "lyrics", "melody", "rhythm", "instrument",
                "live music", "streaming", "playlist", "talented",
            ],
            "B2": [
                "musical influence", "soundtrack", "composition",
                "improvisation", "music industry", "cultural impact of music",
            ],
            "C1": [
                "musical theory", "dissonance", "avant-garde",
                "music as cultural identity", "patronage of the arts",
            ],
            "C2": [
                "philosophy of aesthetics", "semiotics of music",
                "nuanced cultural critique",
            ],
        },
        "subtopic_arcs": [
            {
                "name": "Music preferences",
                "questions": [
                    "What type of music do you like?",
                    "Who is your favourite singer or band?",
                    "What song always makes you happy?",
                ],
                "emoji": "music",
            },
            {
                "name": "Playing and creating",
                "questions": [
                    "Do you play a musical instrument?",
                    "Have you ever tried to sing or make music?",
                    "Would you like to learn an instrument?",
                ],
                "emoji": "music",
            },
            {
                "name": "Concerts and live music",
                "questions": [
                    "Have you been to a concert?",
                    "What was the best live music you have heard?",
                    "Would you prefer a small venue or a big stadium?",
                ],
                "emoji": "happy",
            },
            {
                "name": "Music and emotion",
                "questions": [
                    "What music do you listen to when you are sad?",
                    "Can music change your mood?",
                    "What music defines your generation?",
                ],
                "emoji": "love",
            },
        ],
    },

    # ── sports ────────────────────────────────────────────────────────────────
    "sports": {
        "id":          "sports",
        "aliases":     ["sport", "exercise", "games", "athletics"],
        "display_name": "Sports & Games",
        "emoji":       "soccer",
        "description": (
            "Discuss sports, games, competitions, physical activities, "
            "team sports, individual sports, and recreational activities."
        ),
        "vocabulary": {
            "A1": [
                "play", "run", "football", "basketball", "swimming",
                "win", "lose", "team", "good", "fun",
            ],
            "A2": [
                "sport", "exercise", "gym", "match", "tournament",
                "score", "goal", "athlete", "coach", "training",
            ],
            "B1": [
                "competitive", "professional", "amateur", "fitness",
                "injury", "championship", "referee", "strategy",
            ],
            "B2": [
                "sports psychology", "doping", "fair play",
                "sports industry", "sponsorship", "fandom",
            ],
            "C1": [
                "sports governance", "performance enhancement",
                "commercialisation of sport", "Olympic ideals",
            ],
            "C2": [
                "philosophy of competition", "nuanced sports discourse",
                "sociopolitical role of sport",
            ],
        },
        "subtopic_arcs": [
            {
                "name": "Sports you like",
                "questions": [
                    "Do you like sport?",
                    "What sport do you play or watch?",
                    "Did you play sport as a child?",
                ],
                "emoji": "soccer",
            },
            {
                "name": "Following sports",
                "questions": [
                    "Do you have a favourite team?",
                    "Do you watch sport on TV?",
                    "Have you ever been to a live sporting event?",
                ],
                "emoji": "basketball",
            },
            {
                "name": "Sport and fitness",
                "questions": [
                    "Do you exercise to keep fit or for fun?",
                    "How often do you exercise?",
                    "What sport would you love to try?",
                ],
                "emoji": "running",
            },
            {
                "name": "Sport and society",
                "questions": [
                    "Should professional athletes earn so much money?",
                    "What sport should be in the Olympics that is not?",
                    "How does sport bring people together?",
                ],
                "emoji": "friends",
            },
        ],
    },

    # ── weather ───────────────────────────────────────────────────────────────
    "weather": {
        "id":          "weather",
        "aliases":     ["seasons", "climate-local"],
        "display_name": "Weather & Seasons",
        "emoji":       "sunny",
        "description": (
            "Discuss weather conditions, seasons, climate, outdoor activities, "
            "and how weather affects daily life."
        ),
        "vocabulary": {
            "A1": [
                "sun", "rain", "snow", "cold", "hot", "wind",
                "cloudy", "good", "bad", "today",
            ],
            "A2": [
                "temperature", "season", "spring", "summer", "autumn", "winter",
                "forecast", "umbrella", "coat", "thunder",
            ],
            "B1": [
                "climate", "heatwave", "flood", "storm", "drought",
                "humidity", "mild", "extreme weather",
            ],
            "B2": [
                "climate change", "carbon emissions", "weather patterns",
                "natural disaster", "meteorology",
            ],
            "C1": [
                "global warming discourse", "climate modelling",
                "societal impact of weather events",
            ],
            "C2": [
                "geopolitics of climate", "nuanced environmental language",
                "idiomatic weather expressions",
            ],
        },
        "subtopic_arcs": [
            {
                "name": "Weather today and where you live",
                "questions": [
                    "What is the weather like today?",
                    "What is the weather usually like where you live?",
                    "What is your favourite type of weather?",
                ],
                "emoji": "sunny",
            },
            {
                "name": "Seasons",
                "questions": [
                    "What is your favourite season?",
                    "What do you like to do in summer? In winter?",
                    "Does the weather affect your mood?",
                ],
                "emoji": "rainy",
            },
            {
                "name": "Extreme weather",
                "questions": [
                    "Have you ever experienced extreme weather?",
                    "What natural disasters happen in your country?",
                    "Are summers getting hotter where you live?",
                ],
                "emoji": "cloudy",
            },
            {
                "name": "Weather and life",
                "questions": [
                    "Does bad weather stop you doing things?",
                    "How do you stay warm or cool in extreme weather?",
                    "What would life be like without seasons?",
                ],
                "emoji": "snow",
            },
        ],
    },

    # ── home ──────────────────────────────────────────────────────────────────
    "home": {
        "id":          "home",
        "aliases":     ["housing", "living", "apartment", "house"],
        "display_name": "Home & Living",
        "emoji":       "home",
        "description": (
            "Discuss housing, home decoration, household tasks, "
            "living spaces, and domestic life."
        ),
        "vocabulary": {
            "A1": [
                "home", "house", "room", "bed", "kitchen",
                "big", "small", "nice", "live", "sleep",
            ],
            "A2": [
                "apartment", "flat", "bedroom", "bathroom", "garden",
                "neighbour", "rent", "buy", "furniture", "clean",
            ],
            "B1": [
                "interior design", "decorate", "renovate",
                "household chores", "mortgage", "landlord", "tenant",
            ],
            "B2": [
                "property market", "minimalism", "sustainable home",
                "open-plan", "gentrification", "home office",
            ],
            "C1": [
                "housing crisis", "urban planning", "co-living",
                "architecture", "social housing",
            ],
            "C2": [
                "sociology of domestic space", "housing policy discourse",
                "nuanced discussion of home and identity",
            ],
        },
        "subtopic_arcs": [
            {
                "name": "Where you live",
                "questions": [
                    "Do you live in a house or an apartment?",
                    "Do you rent or own your home?",
                    "What is your favourite room?",
                ],
                "emoji": "home",
            },
            {
                "name": "Home life",
                "questions": [
                    "Do you live alone or with others?",
                    "What household chores do you do?",
                    "Do you like cooking at home?",
                ],
                "emoji": "chair",
            },
            {
                "name": "Your ideal home",
                "questions": [
                    "What would your dream home look like?",
                    "Would you prefer to live in a city or the countryside?",
                    "What would you change about where you live now?",
                ],
                "emoji": "door",
            },
            {
                "name": "Housing and society",
                "questions": [
                    "Is it hard to afford housing in your city?",
                    "Should young people rent or buy?",
                    "How has the neighbourhood you live in changed?",
                ],
                "emoji": "money",
            },
        ],
    },

    # ── transportation ────────────────────────────────────────────────────────
    "transportation": {
        "id":          "transportation",
        "aliases":     ["transport", "commute", "travel-local", "vehicles"],
        "display_name": "Transportation & Getting Around",
        "emoji":       "bus",
        "description": (
            "Talk about vehicles, public transport, commuting, "
            "getting around, traffic, and transportation systems."
        ),
        "vocabulary": {
            "A1": [
                "bus", "train", "car", "bike", "walk",
                "go", "come", "near", "far", "fast",
            ],
            "A2": [
                "taxi", "subway", "ticket", "station", "drive",
                "traffic", "bus stop", "platform", "arrive",
            ],
            "B1": [
                "commute", "rush hour", "public transport",
                "road trip", "navigation", "delay", "route",
            ],
            "B2": [
                "sustainable transport", "electric vehicle",
                "infrastructure", "congestion charge", "ride-sharing",
            ],
            "C1": [
                "urban mobility", "autonomous vehicles",
                "transport policy", "carbon footprint of transport",
            ],
            "C2": [
                "geopolitics of transport infrastructure",
                "nuanced urban planning discourse",
                "idiomatic transport expressions",
            ],
        },
        "subtopic_arcs": [
            {
                "name": "How you get around",
                "questions": [
                    "How do you usually get to work or school?",
                    "Do you drive?",
                    "Do you prefer public transport or a car?",
                ],
                "emoji": "bus",
            },
            {
                "name": "Daily commute",
                "questions": [
                    "How long does it take you to get to work?",
                    "Is traffic bad where you live?",
                    "What do you do on the train or bus?",
                ],
                "emoji": "train",
            },
            {
                "name": "Sustainable transport",
                "questions": [
                    "Do you cycle or walk?",
                    "What do you think about electric cars?",
                    "Should cities ban cars from the centre?",
                ],
                "emoji": "bicycle",
            },
            {
                "name": "Transport and the future",
                "questions": [
                    "What is public transport like in your city?",
                    "Would you use a self-driving car?",
                    "How should cities improve transport?",
                ],
                "emoji": "airplane",
            },
        ],
    },

    # ── culture ───────────────────────────────────────────────────────────────
    "culture": {
        "id":          "culture",
        "aliases":     ["traditions", "customs", "heritage", "society"],
        "display_name": "Culture & Traditions",
        "emoji":       "happy",
        "description": (
            "Explore cultural aspects, traditions, festivals, customs, "
            "cultural differences, and heritage."
        ),
        "vocabulary": {
            "A1": [
                "celebrate", "festival", "food", "family", "holiday",
                "tradition", "music", "dance", "dress",
            ],
            "A2": [
                "culture", "custom", "religion", "language",
                "national day", "ceremony", "gift", "greeting",
            ],
            "B1": [
                "heritage", "identity", "cultural values",
                "multicultural", "stereotype", "generation", "integration",
            ],
            "B2": [
                "cultural appropriation", "globalisation", "diversity",
                "diaspora", "cultural exchange",
            ],
            "C1": [
                "cultural relativism", "postcolonialism",
                "soft power", "cultural hegemony",
            ],
            "C2": [
                "anthropological perspectives on culture",
                "nuanced intercultural discourse",
                "semiotics of cultural symbols",
            ],
        },
        "subtopic_arcs": [
            {
                "name": "Your country's culture",
                "questions": [
                    "What is a popular tradition in your country?",
                    "What do people celebrate in your country?",
                    "What food is typical for celebrations?",
                ],
                "emoji": "happy",
            },
            {
                "name": "Cultural differences",
                "questions": [
                    "What surprised you about another culture?",
                    "What do foreigners misunderstand about your culture?",
                    "What cultural habit from another country do you admire?",
                ],
                "emoji": "friends",
            },
            {
                "name": "Culture and identity",
                "questions": [
                    "How much does your culture shape who you are?",
                    "Do you feel your cultural identity is strong?",
                    "Has your culture changed in your lifetime?",
                ],
                "emoji": "love",
            },
            {
                "name": "Globalisation and culture",
                "questions": [
                    "Is globalisation making cultures more similar?",
                    "Should minority languages be protected?",
                    "What from your culture do you want to share with the world?",
                ],
                "emoji": "airplane",
            },
        ],
    },

    # ── pets ──────────────────────────────────────────────────────────────────
    "pets": {
        "id":          "pets",
        "aliases":     ["animals", "wildlife", "pet-care"],
        "display_name": "Pets & Animals",
        "emoji":       "happy",
        "description": (
            "Talk about pets, animals, wildlife, animal care, "
            "pet ownership, and animal behaviour."
        ),
        "vocabulary": {
            "A1": [
                "dog", "cat", "bird", "fish", "animal",
                "big", "small", "cute", "like", "have",
            ],
            "A2": [
                "pet", "owner", "feed", "walk", "vet",
                "wild animal", "habitat", "zoo", "fur", "care",
            ],
            "B1": [
                "adopt", "breed", "endangered", "wildlife",
                "conservation", "companionship", "allergic",
            ],
            "B2": [
                "animal rights", "factory farming", "biodiversity",
                "exotic pets", "human-animal bond",
            ],
            "C1": [
                "sentience", "animal cognition", "veganism discourse",
                "rewilding", "species extinction",
            ],
            "C2": [
                "philosophy of animal rights", "nuanced conservation discourse",
                "zoonotic disease and society",
            ],
        },
        "subtopic_arcs": [
            {
                "name": "Pets you have or want",
                "questions": [
                    "Do you have a pet?",
                    "What animal would you love to have?",
                    "Did you have a pet as a child?",
                ],
                "emoji": "happy",
            },
            {
                "name": "Caring for animals",
                "questions": [
                    "How do you take care of a pet?",
                    "Is having a pet expensive?",
                    "Do you think people treat pets like family members?",
                ],
                "emoji": "home",
            },
            {
                "name": "Wild animals",
                "questions": [
                    "What is your favourite wild animal?",
                    "Have you ever seen a wild animal up close?",
                    "Should wild animals be kept in zoos?",
                ],
                "emoji": "sunny",
            },
            {
                "name": "Animals and society",
                "questions": [
                    "Do you think animal rights are important?",
                    "What should we do to protect endangered species?",
                    "Could you ever become vegan or vegetarian?",
                ],
                "emoji": "love",
            },
        ],
    },

    # ── news ──────────────────────────────────────────────────────────────────
    "news": {
        "id":          "news",
        "aliases":     ["current-events", "current_events", "world-news"],
        "display_name": "News & Current Events",
        "emoji":       "book",
        "description": (
            "Talk about current events, news stories, global happenings, "
            "social issues, and world affairs."
        ),
        "vocabulary": {
            "A1": [
                "good", "bad", "big", "important", "happen",
                "today", "country", "people", "know",
            ],
            "A2": [
                "news", "newspaper", "event", "problem", "government",
                "election", "health", "economy", "local", "international",
            ],
            "B1": [
                "headline", "journalist", "report", "politics",
                "opinion", "source", "bias", "social media",
            ],
            "B2": [
                "misinformation", "media literacy", "investigative journalism",
                "press freedom", "breaking news",
            ],
            "C1": [
                "propaganda", "fourth estate", "editorial bias",
                "geopolitics", "social polarisation",
            ],
            "C2": [
                "philosophy of truth in media", "nuanced political discourse",
                "democratic accountability",
            ],
        },
        "subtopic_arcs": [
            {
                "name": "How you follow the news",
                "questions": [
                    "Do you read the news?",
                    "Where do you get your news from?",
                    "How often do you check the news?",
                ],
                "emoji": "book",
            },
            {
                "name": "Recent stories",
                "questions": [
                    "What is a big story in the news at the moment?",
                    "Is there local news that affects your life?",
                    "What news story surprised you recently?",
                ],
                "emoji": "phone",
            },
            {
                "name": "News and opinions",
                "questions": [
                    "Do you share news articles with others?",
                    "Do you discuss news with friends or family?",
                    "Has a news story ever changed your opinion?",
                ],
                "emoji": "friends",
            },
            {
                "name": "Media trust and future",
                "questions": [
                    "Do you trust the news media?",
                    "How can you tell if news is reliable?",
                    "Is social media a good or bad source of news?",
                ],
                "emoji": "confused",
            },
        ],
    },
}

# Build a fast alias → canonical ID lookup at module load time
_ALIAS_TO_ID: Dict[str, str] = {}
for _cfg in TOPIC_CATALOGUE.values():
    _ALIAS_TO_ID[_cfg["id"]] = _cfg["id"]
    for _alias in _cfg.get("aliases", []):
        _ALIAS_TO_ID[_alias.lower()] = _cfg["id"]


# ─────────────────────────────────────────────────────────────────────────────
# SESSION PACING ENGINE
# ─────────────────────────────────────────────────────────────────────────────

# For each session duration (minutes), defines:
#   greeting_seconds   — time for the opening exchange
#   practice_seconds   — time for the main topic practice
#   wrapup_seconds     — time for closing
#   subtopics_to_cover — how many subtopic arcs to attempt (guides model pacing)
#   turns_target       — total tutor turns the model should aim for
#   response_sentences — max sentences per tutor turn (tighter for short sessions)

SESSION_PACING: Dict[int, Dict[str, Any]] = {
    1: {
        "greeting_seconds":   10,
        "practice_seconds":   40,
        "wrapup_seconds":     10,
        "subtopics_to_cover": 1,
        "turns_target":       4,   # ~10s per turn
        "response_sentences": 1,
        "pacing_note": (
            "This is a 1-MINUTE session. You have roughly 4 exchanges total. "
            "Skip the greeting entirely — open directly with the topic and "
            "one yes/no question. Ask ONE subtopic only. "
            "Wrap up after 3 student responses."
        ),
    },
    3: {
        "greeting_seconds":   15,
        "practice_seconds":   150,
        "wrapup_seconds":     15,
        "subtopics_to_cover": 2,
        "turns_target":       10,  # ~18s per turn
        "response_sentences": 1,
        "pacing_note": (
            "This is a 3-MINUTE session. You have roughly 10 exchanges total. "
            "Spend 1 exchange on greeting. Cover 2 subtopics. "
            "Wrap up after ~8 student responses."
        ),
    },
    5: {
        "greeting_seconds":   30,
        "practice_seconds":   240,
        "wrapup_seconds":     30,
        "subtopics_to_cover": 3,
        "turns_target":       16,  # ~18s per turn
        "response_sentences": 2,
        "pacing_note": (
            "This is a 5-MINUTE session. You have roughly 16 exchanges total. "
            "Spend 2 exchanges on greeting. Cover 3 subtopics progressively. "
            "Wrap up with a brief positive summary."
        ),
    },
}

# Fallback for any duration not in the table
_DEFAULT_PACING = SESSION_PACING[5]


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def get_topic_config(topic_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Resolve a topic ID (including aliases) to its full catalogue entry.

    Returns None if the topic is not found (e.g. custom topics).
    """
    if not topic_id:
        return None
    canonical = _ALIAS_TO_ID.get(topic_id.lower().strip())
    if canonical:
        return TOPIC_CATALOGUE.get(canonical)
    return None


def get_session_pacing(duration_minutes: Optional[int]) -> Dict[str, Any]:
    """
    Return the pacing configuration for the requested session duration.

    Snaps to the nearest defined duration (1 / 3 / 5).
    """
    if duration_minutes is None:
        return _DEFAULT_PACING

    # Snap to nearest key
    keys = sorted(SESSION_PACING.keys())
    best = min(keys, key=lambda k: abs(k - duration_minutes))
    return SESSION_PACING[best]


def get_topic_vocabulary(topic_id: Optional[str], level: str) -> List[str]:
    """
    Return the level-appropriate vocabulary list for a topic.

    Falls back to empty list if topic not found.
    """
    cfg = get_topic_config(topic_id)
    if not cfg:
        return []
    vocab_map = cfg.get("vocabulary", {})
    # Try exact level first, then adjacent levels as fallback
    level_upper = level.upper()
    if level_upper in vocab_map:
        return vocab_map[level_upper]
    # Fallback: try one level down
    _order = ["A1", "A2", "B1", "B2", "C1", "C2"]
    idx = _order.index(level_upper) if level_upper in _order else 2
    fallback_idx = max(0, idx - 1)
    return vocab_map.get(_order[fallback_idx], [])


def get_subtopic_arcs(
    topic_id: Optional[str],
    n: int,
) -> List[Dict[str, Any]]:
    """
    Return the first `n` subtopic arcs for a topic (in progression order).
    """
    cfg = get_topic_config(topic_id)
    if not cfg:
        return []
    return cfg.get("subtopic_arcs", [])[:n]


# ─────────────────────────────────────────────────────────────────────────────
# ROLEPLAY SCENARIOS
# One immersive scenario per topic, level-aware.
# Fields:
#   character     — who the model plays
#   location      — where the scene is set
#   entry_action  — what the learner has just done (sets the scene)
#   goal          — what the learner must accomplish
#   opening_line  — model's first spoken line (in-character)
#   level_notes   — how to adjust complexity per CEFR band
# ─────────────────────────────────────────────────────────────────────────────

ROLEPLAY_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "travel": {
        "character":    "Alex, a friendly hotel receptionist",
        "location":     "a hotel front desk in the city the learner wants to visit",
        "entry_action": "The learner has just walked in with their luggage to check in",
        "goal":         "Check in, ask about the room, find out about local attractions",
        "opening_line": "Good afternoon! Welcome. Do you have a reservation with us?",
        "level_notes": {
            "A1": "Use only simple present tense. Ask one yes/no question at a time. Speak very slowly.",
            "A2": "Use present and past tense. Ask about travel plans simply. Confirm what you understood.",
            "B1": "Discuss room preferences, local tips, and transport options naturally.",
            "B2": "Include details about hotel policies, area recommendations, cultural insights.",
            "C1": "Use idiomatic hospitality language. Discuss sustainability, local hidden gems.",
            "C2": "Full authentic register. Discuss travel philosophy, cultural nuances, complex requests.",
        },
    },
    "food": {
        "character":    "Marco, a warm waiter at a local restaurant",
        "location":     "a bustling restaurant in the target-language country",
        "entry_action": "The learner has just sat down and is looking at the menu",
        "goal":         "Order a meal, ask about dishes, make special requests, pay the bill",
        "opening_line": "Good evening! Here is our menu. Can I get you something to drink first?",
        "level_notes": {
            "A1": "Name dishes simply. Accept any attempt at ordering. Confirm each item clearly.",
            "A2": "Describe 1-2 dishes. Ask about allergies simply. Confirm the full order.",
            "B1": "Describe ingredients, cooking methods. Handle special requests naturally.",
            "B2": "Discuss cuisine origins, chef specials, wine pairings, dietary philosophy.",
            "C1": "Use culinary vocabulary richly. Discuss sourcing, seasonal menus, food culture.",
            "C2": "Full sommelier-level discourse. Pair wines, discuss gastronomic trends.",
        },
    },
    "work": {
        "character":    "Sarah, a friendly HR manager conducting a job interview",
        "location":     "a modern office meeting room",
        "entry_action": "The learner has just entered for a job interview at their dream company",
        "goal":         "Answer interview questions confidently, ask smart questions, negotiate",
        "opening_line": "Hi, please have a seat! Thank you for coming in today. Tell me a little about yourself.",
        "level_notes": {
            "A1": "Ask only about name, job experience, and hobbies. Accept very short answers.",
            "A2": "Ask about previous work and daily tasks. Keep questions simple and direct.",
            "B1": "Discuss strengths, goals, and team experience. Follow up naturally.",
            "B2": "Probe motivations, conflict resolution, leadership style.",
            "C1": "Discuss strategy, culture fit, compensation. Use professional register.",
            "C2": "Full executive-level dialogue. Negotiate terms, discuss vision and impact.",
        },
    },
    "hobbies": {
        "character":    "Jamie, an enthusiastic member of a local hobby club",
        "location":     "a community centre where the club meets",
        "entry_action": "The learner has just arrived to try the club for the first time",
        "goal":         "Introduce yourself, learn about the hobby, decide if you want to join",
        "opening_line": "Hey, welcome! Is this your first time here? What made you interested in joining us?",
        "opening_line_by_level": {
            "A1": "Hi! Welcome! Is this your first time?",
            "A2": "Hey, welcome! Is this your first time here? Do you like this hobby?",
            "B1": "Hey, welcome! Is this your first time here? What brought you to us today?",
            "B2": "Hey, welcome! Is this your first time here? What made you interested in joining us?",
            "C1": "Hey, welcome! Is this your first time here? What made you interested in joining us?",
            "C2": "Hey, welcome! Is this your first time here? What made you interested in joining us?",
        },
        "level_notes": {
            "A1": "Ask about name and basic likes. Use simple vocabulary about activities.",
            "A2": "Discuss frequency and how to do the hobby. Use simple descriptions.",
            "B1": "Explain the hobby's benefits, share personal stories, invite the learner to try.",
            "B2": "Discuss skill levels, competitions, the community and its culture.",
            "C1": "Explore the psychology of the hobby, its creative dimensions, niche aspects.",
            "C2": "Debate the role of hobbies in identity, wellness, and modern society.",
        },
    },
    "shopping": {
        "character":    "Sofia, a helpful shop assistant",
        "location":     "a clothing store in the city centre",
        "entry_action": "The learner has just walked in looking for something specific",
        "goal":         "Find the right item, ask about sizes and prices, make a purchase or return",
        "opening_line": "Hi there! Can I help you find something today?",
        "level_notes": {
            "A1": "Point to items. Accept colour, size, price as the only vocabulary needed.",
            "A2": "Discuss size, colour, price, and where to find items in the store.",
            "B1": "Discuss style preferences, compare options, handle exchanges naturally.",
            "B2": "Discuss brand quality, sustainable fashion choices, return policies.",
            "C1": "Discuss fashion trends, ethical consumption, designer vs fast fashion.",
            "C2": "Debate the economics of fashion, consumer psychology, global supply chains.",
        },
    },
    "daily": {
        "character":    "Lena, a friendly neighbour",
        "location":     "outside the apartment building in the morning",
        "entry_action": "The learner runs into their neighbour while leaving for the day",
        "goal":         "Have a natural chat about daily routines, plans, and neighbourhood life",
        "opening_line": "Oh hi! Early start today? I'm just heading to the café before work.",
        "level_notes": {
            "A1": "Discuss morning routines using simple present. One question at a time.",
            "A2": "Talk about daily schedule, commute, and simple plans for the day.",
            "B1": "Discuss work-life balance, weekend plans, neighbourhood events.",
            "B2": "Debate remote work, productivity habits, urban vs rural lifestyle.",
            "C1": "Explore the psychology of routines, digital detox, mindful living.",
            "C2": "Analyse societal pace of life, burnout culture, modern urban experience.",
        },
    },
    "health": {
        "character":    "Dr. Chen, a calm and thorough GP",
        "location":     "a doctor's consultation room",
        "entry_action": "The learner has just sat down for a routine health check-up",
        "goal":         "Describe symptoms, answer questions about lifestyle, receive advice",
        "opening_line": "Good morning! So, what brings you in today? How have you been feeling?",
        "level_notes": {
            "A1": "Ask about basic symptoms using body part vocabulary. Keep it very simple.",
            "A2": "Ask about pain, frequency, and daily habits. Use common health vocabulary.",
            "B1": "Discuss lifestyle, diet, and exercise. Give clear recommendations.",
            "B2": "Explore mental health, preventive care, and detailed medical history.",
            "C1": "Discuss chronic conditions, treatment options, healthcare systems.",
            "C2": "Debate public health policy, bioethics, pharmaceutical industry.",
        },
    },
    "technology": {
        "character":    "Sam, a patient tech support specialist",
        "location":     "a tech support call (phone or chat)",
        "entry_action": "The learner has just contacted support because their device isn't working",
        "goal":         "Describe the problem, follow troubleshooting steps, resolve the issue",
        "opening_line": "Hi, thank you for calling tech support! My name is Sam. What seems to be the problem today?",
        "level_notes": {
            "A1": "Use only the most basic device vocabulary. Confirm each step clearly.",
            "A2": "Guide through simple steps. Name apps, buttons, settings simply.",
            "B1": "Troubleshoot connectivity, software issues. Use clear technical language.",
            "B2": "Discuss settings, security, data backup. Handle complex scenarios.",
            "C1": "Discuss system architecture, privacy policies, digital security in depth.",
            "C2": "Debate tech ethics, AI implications, digital rights and data sovereignty.",
        },
    },
    "education": {
        "character":    "Professor Rivera, a knowledgeable and encouraging academic",
        "location":     "a university office during office hours",
        "entry_action": "The learner has knocked on the door to ask for advice about their studies",
        "goal":         "Discuss academic challenges, get study advice, explore course options",
        "opening_line": "Come in! Great to see you. How are things going with your studies so far?",
        "level_notes": {
            "A1": "Ask about subjects and schedule using simple vocabulary. Be encouraging.",
            "A2": "Discuss homework, exams, and study habits in simple terms.",
            "B1": "Explore learning strategies, academic goals, and course options.",
            "B2": "Discuss thesis topics, research methods, academic career paths.",
            "C1": "Debate educational philosophy, academic freedom, interdisciplinary study.",
            "C2": "Explore the future of education, AI in academia, knowledge production.",
        },
    },
    "family": {
        "character":    "Mia, a new colleague who is curious and friendly",
        "location":     "a company lunch break in the office kitchen",
        "entry_action": "The learner sits down next to Mia who starts a conversation",
        "goal":         "Talk about family background, traditions, and personal life naturally",
        "opening_line": "Mind if I join you? I'm Mia, I just started last week. Do you have family nearby?",
        "level_notes": {
            "A1": "Ask about family members and simple descriptions. Accept one-word answers.",
            "A2": "Discuss family activities and traditions using simple past and present.",
            "B1": "Share family stories, cultural traditions, and personal anecdotes.",
            "B2": "Discuss family dynamics, generational differences, modern family structures.",
            "C1": "Explore sociology of family, identity formation, cultural norms.",
            "C2": "Debate kinship structures, family policy, evolving social contracts.",
        },
    },
}


def get_roleplay_scenario(topic_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return the roleplay scenario for a given topic, or None if not found."""
    if not topic_id:
        return None
    cfg = get_topic_config(topic_id)
    if not cfg:
        return None
    canonical_id = cfg["id"]
    return ROLEPLAY_SCENARIOS.get(canonical_id)

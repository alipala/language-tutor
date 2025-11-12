"""
Enriched Learning Goals Configuration
Provides hierarchical, level-appropriate, language-specific learning goals
"""

from typing import Dict, List, Any

# Enriched Goals Data Structure
ENRICHED_GOALS: Dict[str, Any] = {
    "travel": {
        "id": "travel",
        "text": "Travel & Tourism",
        "category": "practical",
        "description": "Communicate effectively while traveling",
        "icon": "✈️",
        "sub_goals": {
            "transportation": {
                "id": "transportation",
                "text": "Transportation & Navigation",
                "description": "Get around cities, use public transport, ask directions",
                "icon": "🚇",
                "level_focus": {
                    "A1-A2": [
                        "Ask for directions to common places",
                        "Buy tickets for buses, trains, and taxis",
                        "Understand basic signs and announcements",
                        "Ask about departure and arrival times"
                    ],
                    "B1-B2": [
                        "Handle travel disruptions and delays",
                        "Negotiate with taxi drivers and understand fares",
                        "Understand complex announcements and schedules",
                        "Discuss alternative routes and transportation options"
                    ],
                    "C1-C2": [
                        "Discuss detailed travel plans and itineraries",
                        "Handle complex situations (cancellations, refunds, complaints)",
                        "Understand regional accents and dialects in announcements",
                        "Navigate bureaucratic processes for travel documents"
                    ]
                },
                "key_vocabulary": ["ticket", "platform", "departure", "arrival", "delay", "station", "fare", "route"],
                "key_phrases": ["How do I get to...", "Where is the...", "When does it leave?", "How much is the fare?"],
                "skill_priorities": {
                    "fluency": 1.3,
                    "vocabulary": 1.2,
                    "pronunciation": 1.1,
                    "grammar": 0.9,
                    "coherence": 0.8
                }
            },
            "accommodation": {
                "id": "accommodation",
                "text": "Accommodation",
                "description": "Book hotels, check in/out, handle issues",
                "icon": "🏨",
                "level_focus": {
                    "A1-A2": [
                        "Check in and out of hotels",
                        "Ask about room facilities and amenities",
                        "Report simple problems (no hot water, broken items)",
                        "Understand hotel services and breakfast times"
                    ],
                    "B1-B2": [
                        "Negotiate prices and request upgrades",
                        "Describe specific accommodation needs and preferences",
                        "Handle complaints and request compensation",
                        "Understand booking terms, conditions, and cancellation policies"
                    ],
                    "C1-C2": [
                        "Discuss accommodation preferences in detail",
                        "Understand and negotiate rental contracts",
                        "Handle complex issues (disputes, legal matters, refunds)",
                        "Negotiate long-term stays and special arrangements"
                    ]
                },
                "key_vocabulary": ["reservation", "check-in", "amenities", "complaint", "refund", "upgrade"],
                "key_phrases": ["I have a reservation", "Is breakfast included?", "There's a problem with...", "Can I get a refund?"],
                "skill_priorities": {
                    "vocabulary": 1.2,
                    "fluency": 1.1,
                    "coherence": 1.1,
                    "pronunciation": 1.0,
                    "grammar": 0.9
                }
            },
            "food_dining": {
                "id": "food_dining",
                "text": "Food & Dining",
                "description": "Order food, understand menus, dietary restrictions",
                "icon": "🍽️",
                "level_focus": {
                    "A1-A2": [
                        "Order food and drinks from menus",
                        "Ask about ingredients and preparation methods",
                        "Request the bill and understand prices",
                        "Express basic food preferences and allergies"
                    ],
                    "B1-B2": [
                        "Discuss dietary restrictions and special requirements",
                        "Make restaurant reservations and special requests",
                        "Understand detailed menus and wine lists",
                        "Engage in conversations about food and cuisine"
                    ],
                    "C1-C2": [
                        "Discuss cuisine, cooking methods, and culinary traditions",
                        "Understand regional specialties and food culture",
                        "Engage in sophisticated food discussions and recommendations",
                        "Navigate fine dining etiquette and wine pairing"
                    ]
                },
                "key_vocabulary": ["menu", "order", "allergic", "vegetarian", "bill", "tip", "reservation"],
                "key_phrases": ["I'd like to order...", "I'm allergic to...", "Can I have the bill?", "Do you have...?"],
                "skill_priorities": {
                    "vocabulary": 1.3,
                    "fluency": 1.2,
                    "pronunciation": 1.1,
                    "grammar": 0.9,
                    "coherence": 0.8
                }
            },
            "shopping": {
                "id": "shopping",
                "text": "Shopping & Services",
                "description": "Buy items, return products, use services",
                "icon": "🛍️",
                "level_focus": {
                    "A1-A2": [
                        "Buy basic items and ask about prices",
                        "Understand sizes, colors, and quantities",
                        "Ask where to find items in stores",
                        "Pay for purchases and understand receipts"
                    ],
                    "B1-B2": [
                        "Return or exchange items",
                        "Compare products and ask for recommendations",
                        "Negotiate prices in markets",
                        "Understand warranties and return policies"
                    ],
                    "C1-C2": [
                        "Discuss product quality, value, and specifications",
                        "Understand consumer rights and legal protections",
                        "Handle complex transactions and disputes",
                        "Navigate online shopping and customer service"
                    ]
                },
                "key_vocabulary": ["price", "size", "color", "receipt", "refund", "exchange", "warranty"],
                "key_phrases": ["How much is this?", "Do you have this in...?", "Can I return this?", "I'd like a refund"],
                "skill_priorities": {
                    "vocabulary": 1.2,
                    "fluency": 1.2,
                    "pronunciation": 1.0,
                    "grammar": 0.9,
                    "coherence": 0.9
                }
            },
            "emergency": {
                "id": "emergency",
                "text": "Emergency Situations",
                "description": "Ask for help, medical issues, report problems",
                "icon": "🚨",
                "level_focus": {
                    "A1-A2": [
                        "Ask for help in emergencies",
                        "Describe basic problems and symptoms",
                        "Understand emergency signs and instructions",
                        "Call for emergency services"
                    ],
                    "B1-B2": [
                        "Explain medical issues and symptoms in detail",
                        "Report theft, loss, or accidents to authorities",
                        "Understand emergency instructions and procedures",
                        "Navigate healthcare system and pharmacies"
                    ],
                    "C1-C2": [
                        "Handle complex emergency situations",
                        "Understand legal procedures and rights",
                        "Communicate with authorities and officials",
                        "Navigate insurance claims and documentation"
                    ]
                },
                "key_vocabulary": ["help", "emergency", "police", "doctor", "hospital", "pain", "lost", "stolen"],
                "key_phrases": ["I need help", "Call an ambulance", "I lost my...", "Someone stole my..."],
                "skill_priorities": {
                    "fluency": 1.3,
                    "pronunciation": 1.2,
                    "vocabulary": 1.2,
                    "grammar": 0.8,
                    "coherence": 0.9
                }
            },
            "social": {
                "id": "social",
                "text": "Social Interactions",
                "description": "Meet people, make friends, understand culture",
                "icon": "👥",
                "level_focus": {
                    "A1-A2": [
                        "Greet people and make introductions",
                        "Make small talk about weather, hobbies, family",
                        "Exchange basic personal information",
                        "Accept and decline invitations politely"
                    ],
                    "B1-B2": [
                        "Make friends and build relationships",
                        "Share experiences and tell stories",
                        "Understand cultural norms and etiquette",
                        "Discuss interests and plan social activities"
                    ],
                    "C1-C2": [
                        "Engage in deep conversations on various topics",
                        "Understand humor, idioms, and cultural references",
                        "Navigate complex social situations",
                        "Build meaningful cross-cultural relationships"
                    ]
                },
                "key_vocabulary": ["hello", "nice to meet you", "friend", "invitation", "culture", "tradition"],
                "key_phrases": ["Nice to meet you", "Where are you from?", "Would you like to...?", "That sounds interesting"],
                "skill_priorities": {
                    "fluency": 1.2,
                    "coherence": 1.2,
                    "vocabulary": 1.1,
                    "pronunciation": 1.0,
                    "grammar": 0.9
                }
            }
        }
    },
    "business": {
        "id": "business",
        "text": "Business & Professional",
        "category": "professional",
        "description": "Communicate effectively in professional settings",
        "icon": "💼",
        "sub_goals": {
            "email": {
                "id": "email",
                "text": "Email & Written Communication",
                "description": "Write professional emails and documents",
                "icon": "📧",
                "level_focus": {
                    "A1-A2": [
                        "Write simple business emails with basic greetings",
                        "Understand basic business correspondence",
                        "Use appropriate greetings and closings",
                        "Request information politely in writing"
                    ],
                    "B1-B2": [
                        "Write formal emails with proper structure",
                        "Draft reports, proposals, and business documents",
                        "Use appropriate business tone and register",
                        "Handle email chains and follow-up communications"
                    ],
                    "C1-C2": [
                        "Write complex business documents and proposals",
                        "Master nuanced tone, style, and persuasive writing",
                        "Handle sensitive communications diplomatically",
                        "Write executive summaries and strategic documents"
                    ]
                },
                "key_vocabulary": ["regarding", "attached", "deadline", "follow-up", "proposal", "meeting"],
                "key_phrases": ["I am writing to...", "Please find attached...", "Looking forward to...", "Best regards"],
                "skill_priorities": {
                    "grammar": 1.3,
                    "vocabulary": 1.2,
                    "coherence": 1.2,
                    "fluency": 0.8,
                    "pronunciation": 0.7
                }
            },
            "meetings": {
                "id": "meetings",
                "text": "Meetings & Presentations",
                "description": "Participate in meetings and give presentations",
                "icon": "📊",
                "level_focus": {
                    "A1-A2": [
                        "Introduce yourself in meetings",
                        "Understand basic meeting agendas",
                        "Ask simple questions during meetings",
                        "Give short self-introductions"
                    ],
                    "B1-B2": [
                        "Participate actively in meetings and discussions",
                        "Give structured presentations with visual aids",
                        "Express opinions, suggestions, and concerns",
                        "Handle basic Q&A sessions"
                    ],
                    "C1-C2": [
                        "Lead meetings and facilitate discussions",
                        "Give complex presentations on technical topics",
                        "Handle challenging questions and objections",
                        "Moderate debates and build consensus"
                    ]
                },
                "key_vocabulary": ["agenda", "minutes", "action items", "presentation", "slide", "discussion"],
                "key_phrases": ["Let's move on to...", "I'd like to add...", "Any questions?", "To summarize..."],
                "skill_priorities": {
                    "coherence": 1.3,
                    "fluency": 1.2,
                    "vocabulary": 1.1,
                    "pronunciation": 1.1,
                    "grammar": 1.0
                }
            },
            "negotiations": {
                "id": "negotiations",
                "text": "Negotiations & Sales",
                "description": "Negotiate terms, present proposals, close deals",
                "icon": "🤝",
                "level_focus": {
                    "A1-A2": [
                        "Understand basic offers and prices",
                        "Ask simple questions about products/services",
                        "Express basic agreement or disagreement",
                        "Understand simple contracts and terms"
                    ],
                    "B1-B2": [
                        "Negotiate terms and conditions",
                        "Present proposals and business cases",
                        "Handle objections and counteroffers",
                        "Discuss pricing, discounts, and payment terms"
                    ],
                    "C1-C2": [
                        "Lead complex negotiations and close deals",
                        "Understand subtle cues and read between lines",
                        "Navigate cultural differences in negotiation styles",
                        "Handle high-stakes negotiations and conflicts"
                    ]
                },
                "key_vocabulary": ["offer", "negotiate", "terms", "contract", "discount", "deal", "agreement"],
                "key_phrases": ["What if we...", "I propose that...", "Can we agree on...", "Let's find a solution"],
                "skill_priorities": {
                    "fluency": 1.3,
                    "coherence": 1.2,
                    "vocabulary": 1.2,
                    "pronunciation": 1.0,
                    "grammar": 1.0
                }
            },
            "networking": {
                "id": "networking",
                "text": "Networking & Socializing",
                "description": "Build professional relationships, engage in small talk",
                "icon": "🌐",
                "level_focus": {
                    "A1-A2": [
                        "Exchange business cards and contact information",
                        "Make basic introductions at events",
                        "Ask about someone's job and company",
                        "Engage in simple professional small talk"
                    ],
                    "B1-B2": [
                        "Build professional relationships and rapport",
                        "Engage in extended small talk and find common ground",
                        "Discuss industry trends and news",
                        "Follow up after networking events"
                    ],
                    "C1-C2": [
                        "Network strategically and build partnerships",
                        "Understand business culture and etiquette",
                        "Navigate complex social-professional situations",
                        "Build and maintain international business relationships"
                    ]
                },
                "key_vocabulary": ["networking", "connection", "industry", "colleague", "partnership", "contact"],
                "key_phrases": ["Nice to meet you", "What do you do?", "Let's stay in touch", "I'd love to connect"],
                "skill_priorities": {
                    "fluency": 1.3,
                    "vocabulary": 1.1,
                    "coherence": 1.1,
                    "pronunciation": 1.0,
                    "grammar": 0.9
                }
            },
            "calls": {
                "id": "calls",
                "text": "Phone & Video Calls",
                "description": "Conduct business calls, schedule meetings",
                "icon": "📞",
                "level_focus": {
                    "A1-A2": [
                        "Answer phone and identify yourself",
                        "Take simple messages",
                        "Ask someone to repeat or speak slowly",
                        "End calls politely"
                    ],
                    "B1-B2": [
                        "Conduct business calls and schedule meetings",
                        "Handle voicemail and leave messages",
                        "Discuss details and confirm information",
                        "Manage video calls and screen sharing"
                    ],
                    "C1-C2": [
                        "Handle complex calls and negotiations",
                        "Understand various accents and phone quality issues",
                        "Manage conference calls with multiple participants",
                        "Handle difficult conversations and complaints"
                    ]
                },
                "key_vocabulary": ["call", "message", "voicemail", "conference", "line", "connection"],
                "key_phrases": ["This is...", "May I speak to...?", "Could you repeat that?", "I'll call you back"],
                "skill_priorities": {
                    "pronunciation": 1.3,
                    "fluency": 1.2,
                    "vocabulary": 1.1,
                    "grammar": 0.9,
                    "coherence": 1.0
                }
            }
        },
        "language_specific_variations": {
            "english": {
                "cultural_notes": "Direct communication, time-consciousness, networking focus",
                "additional_focus": ["Email etiquette", "Multicultural teams", "Virtual meetings"]
            },
            "spanish": {
                "cultural_notes": "Relationship-building, formal vs informal (tú/usted)",
                "additional_focus": ["Personal relationships", "Indirect communication", "Business meals"]
            },
            "japanese": {
                "cultural_notes": "Keigo (honorific language), hierarchy, business card exchange",
                "additional_focus": ["Formal protocols", "Group harmony", "Indirect communication"]
            },
            "german": {
                "cultural_notes": "Formal titles, structured communication, punctuality",
                "additional_focus": ["Direct but formal", "Precision", "Planning"]
            },
            "french": {
                "cultural_notes": "Formal language, business meals, intellectual discourse",
                "additional_focus": ["Relationship-building", "Style and presentation", "Formality"]
            }
        }
    },
    "academic": {
        "id": "academic",
        "text": "Academic & Education",
        "category": "educational",
        "description": "Succeed in academic settings",
        "icon": "🎓",
        "sub_goals": {
            "lectures": {
                "id": "lectures",
                "text": "Lectures & Note-Taking",
                "description": "Understand lectures, take notes, ask questions",
                "icon": "📝",
                "level_focus": {
                    "A1-A2": [
                        "Understand simple lectures on familiar topics",
                        "Take basic notes with key words",
                        "Ask simple clarification questions",
                        "Follow lecture structure and main points"
                    ],
                    "B1-B2": [
                        "Follow complex lectures and take detailed notes",
                        "Understand academic vocabulary and concepts",
                        "Ask thoughtful questions during lectures",
                        "Identify main arguments and supporting evidence"
                    ],
                    "C1-C2": [
                        "Understand specialized lectures in your field",
                        "Synthesize information from multiple sources",
                        "Engage critically with lecture content",
                        "Take comprehensive notes and identify gaps"
                    ]
                },
                "key_vocabulary": ["lecture", "notes", "professor", "topic", "argument", "evidence", "theory"],
                "key_phrases": ["Could you explain...?", "What do you mean by...?", "Can you give an example?"],
                "skill_priorities": {
                    "vocabulary": 1.3,
                    "coherence": 1.2,
                    "grammar": 1.1,
                    "fluency": 0.9,
                    "pronunciation": 0.8
                }
            },
            "reading": {
                "id": "reading",
                "text": "Reading & Research",
                "description": "Read academic texts, conduct research",
                "icon": "📚",
                "level_focus": {
                    "A1-A2": [
                        "Read simple texts and understand basic concepts",
                        "Identify main ideas in short articles",
                        "Use dictionaries and reference materials",
                        "Understand basic academic vocabulary"
                    ],
                    "B1-B2": [
                        "Read academic articles and understand main arguments",
                        "Identify thesis statements and supporting evidence",
                        "Conduct basic research using multiple sources",
                        "Understand academic writing conventions"
                    ],
                    "C1-C2": [
                        "Read complex research papers and analyze critically",
                        "Synthesize information from multiple academic sources",
                        "Evaluate research methodology and conclusions",
                        "Conduct comprehensive literature reviews"
                    ]
                },
                "key_vocabulary": ["research", "article", "study", "analysis", "methodology", "conclusion"],
                "key_phrases": ["According to...", "The study shows...", "The author argues...", "In conclusion..."],
                "skill_priorities": {
                    "vocabulary": 1.3,
                    "grammar": 1.2,
                    "coherence": 1.2,
                    "fluency": 0.8,
                    "pronunciation": 0.7
                }
            },
            "writing": {
                "id": "writing",
                "text": "Writing & Essays",
                "description": "Write academic papers, essays, reports",
                "icon": "✍️",
                "level_focus": {
                    "A1-A2": [
                        "Write simple paragraphs with basic structure",
                        "Describe topics using simple sentences",
                        "Use basic academic vocabulary",
                        "Follow simple essay structure (intro, body, conclusion)"
                    ],
                    "B1-B2": [
                        "Write structured essays with clear arguments",
                        "Use academic vocabulary and formal register",
                        "Cite sources and avoid plagiarism",
                        "Develop paragraphs with topic sentences and support"
                    ],
                    "C1-C2": [
                        "Write research papers with sophisticated arguments",
                        "Master academic style and conventions",
                        "Argue complex points with nuanced evidence",
                        "Write literature reviews and critical analyses"
                    ]
                },
                "key_vocabulary": ["essay", "thesis", "argument", "paragraph", "citation", "reference", "conclusion"],
                "key_phrases": ["This essay argues...", "According to research...", "In conclusion...", "Furthermore..."],
                "skill_priorities": {
                    "grammar": 1.3,
                    "vocabulary": 1.3,
                    "coherence": 1.2,
                    "fluency": 0.8,
                    "pronunciation": 0.7
                }
            },
            "presentations": {
                "id": "presentations",
                "text": "Presentations & Seminars",
                "description": "Present research, participate in seminars",
                "icon": "🎤",
                "level_focus": {
                    "A1-A2": [
                        "Give short presentations on familiar topics",
                        "Use visual aids to support simple presentations",
                        "Answer basic questions about your presentation",
                        "Speak clearly and at appropriate pace"
                    ],
                    "B1-B2": [
                        "Present research findings with structure",
                        "Participate actively in seminars and discussions",
                        "Handle Q&A sessions confidently",
                        "Use academic language in presentations"
                    ],
                    "C1-C2": [
                        "Lead seminars and facilitate academic discussions",
                        "Defend thesis and research methodology",
                        "Engage in academic debate and critique",
                        "Present complex research to specialist audiences"
                    ]
                },
                "key_vocabulary": ["presentation", "slide", "research", "findings", "methodology", "discussion"],
                "key_phrases": ["Today I will present...", "My research shows...", "To answer your question...", "In summary..."],
                "skill_priorities": {
                    "coherence": 1.3,
                    "fluency": 1.2,
                    "pronunciation": 1.2,
                    "vocabulary": 1.1,
                    "grammar": 1.0
                }
            }
        }
    },
    "daily": {
        "id": "daily",
        "text": "Daily Life & Social",
        "category": "personal",
        "description": "Handle everyday situations and conversations",
        "icon": "🏠",
        "sub_goals": {
            "family": {
                "id": "family",
                "text": "Family & Relationships",
                "description": "Talk about family, describe relationships",
                "icon": "👨‍👩‍👧‍👦",
                "level_focus": {
                    "A1-A2": [
                        "Talk about family members and relationships",
                        "Describe basic family activities",
                        "Express simple emotions and feelings",
                        "Discuss daily routines with family"
                    ],
                    "B1-B2": [
                        "Discuss family issues and relationships in detail",
                        "Express complex emotions and opinions",
                        "Talk about family traditions and values",
                        "Navigate family conversations and conflicts"
                    ],
                    "C1-C2": [
                        "Navigate complex family dynamics",
                        "Understand cultural differences in family structures",
                        "Discuss sensitive family topics diplomatically",
                        "Express nuanced emotions and perspectives"
                    ]
                },
                "key_vocabulary": ["family", "parents", "children", "relationship", "love", "support"],
                "key_phrases": ["My family consists of...", "I'm close to...", "We usually...", "I feel..."],
                "skill_priorities": {
                    "fluency": 1.2,
                    "vocabulary": 1.2,
                    "coherence": 1.1,
                    "pronunciation": 1.0,
                    "grammar": 0.9
                }
            },
            "hobbies": {
                "id": "hobbies",
                "text": "Hobbies & Interests",
                "description": "Discuss interests, share experiences",
                "icon": "🎨",
                "level_focus": {
                    "A1-A2": [
                        "Talk about hobbies and free time activities",
                        "Describe what you like to do",
                        "Ask others about their interests",
                        "Express preferences simply"
                    ],
                    "B1-B2": [
                        "Discuss interests in detail and share experiences",
                        "Explain why you enjoy certain activities",
                        "Compare different hobbies and activities",
                        "Make plans to do activities together"
                    ],
                    "C1-C2": [
                        "Engage in specialized discussions about interests",
                        "Understand technical vocabulary in hobby areas",
                        "Share expert knowledge and insights",
                        "Discuss philosophy and deeper meaning of interests"
                    ]
                },
                "key_vocabulary": ["hobby", "interest", "activity", "enjoy", "passion", "skill"],
                "key_phrases": ["I enjoy...", "In my free time...", "I'm interested in...", "I've been doing... for..."],
                "skill_priorities": {
                    "fluency": 1.3,
                    "vocabulary": 1.2,
                    "coherence": 1.0,
                    "pronunciation": 1.0,
                    "grammar": 0.9
                }
            },
            "health": {
                "id": "health",
                "text": "Health & Wellness",
                "description": "Describe symptoms, understand medical advice",
                "icon": "🏥",
                "level_focus": {
                    "A1-A2": [
                        "Describe basic symptoms and health problems",
                        "Understand simple medical advice",
                        "Make doctor appointments",
                        "Ask about medications and dosages"
                    ],
                    "B1-B2": [
                        "Discuss health issues and medical history",
                        "Understand medical instructions and prescriptions",
                        "Talk about lifestyle and wellness",
                        "Navigate healthcare system and insurance"
                    ],
                    "C1-C2": [
                        "Discuss complex health topics and conditions",
                        "Understand medical terminology and procedures",
                        "Engage in health policy discussions",
                        "Understand medical research and studies"
                    ]
                },
                "key_vocabulary": ["doctor", "symptom", "medicine", "pain", "treatment", "health", "appointment"],
                "key_phrases": ["I have a pain in...", "I feel...", "The doctor said...", "I need to..."],
                "skill_priorities": {
                    "vocabulary": 1.3,
                    "fluency": 1.2,
                    "pronunciation": 1.1,
                    "grammar": 0.9,
                    "coherence": 1.0
                }
            },
            "housing": {
                "id": "housing",
                "text": "Housing & Living",
                "description": "Discuss housing, handle living situations",
                "icon": "🏡",
                "level_focus": {
                    "A1-A2": [
                        "Describe your home and neighborhood",
                        "Talk about daily routines at home",
                        "Discuss basic housing needs",
                        "Understand rental advertisements"
                    ],
                    "B1-B2": [
                        "Discuss housing issues and maintenance",
                        "Understand rental agreements and contracts",
                        "Negotiate with landlords and roommates",
                        "Describe ideal living situations"
                    ],
                    "C1-C2": [
                        "Handle complex housing matters and disputes",
                        "Understand legal documents and tenant rights",
                        "Discuss real estate and property investment",
                        "Navigate housing regulations and policies"
                    ]
                },
                "key_vocabulary": ["apartment", "rent", "landlord", "utilities", "neighborhood", "lease"],
                "key_phrases": ["I live in...", "The rent is...", "There's a problem with...", "I'm looking for..."],
                "skill_priorities": {
                    "vocabulary": 1.2,
                    "coherence": 1.1,
                    "fluency": 1.1,
                    "grammar": 1.0,
                    "pronunciation": 0.9
                }
            }
        }
    },
    "culture": {
        "id": "culture",
        "text": "Culture & Entertainment",
        "category": "cultural",
        "description": "Engage with culture, media, and entertainment",
        "icon": "🎭",
        "sub_goals": {
            "media": {
                "id": "media",
                "text": "Media & News",
                "description": "Understand news, follow current events",
                "icon": "📰",
                "level_focus": {
                    "A1-A2": [
                        "Understand simple news and basic headlines",
                        "Follow weather forecasts and sports results",
                        "Understand basic current events",
                        "Read simple news articles"
                    ],
                    "B1-B2": [
                        "Follow news stories and understand context",
                        "Understand current events and their implications",
                        "Discuss news and express opinions",
                        "Compare different news sources"
                    ],
                    "C1-C2": [
                        "Analyze news critically and identify bias",
                        "Understand political nuances and implications",
                        "Engage in informed discussions about current affairs",
                        "Understand complex economic and social issues"
                    ]
                },
                "key_vocabulary": ["news", "headline", "article", "report", "journalist", "current events"],
                "key_phrases": ["According to the news...", "I read that...", "What do you think about...?", "The article says..."],
                "skill_priorities": {
                    "vocabulary": 1.3,
                    "coherence": 1.2,
                    "grammar": 1.1,
                    "fluency": 1.0,
                    "pronunciation": 0.8
                }
            },
            "arts": {
                "id": "arts",
                "text": "Arts & Literature",
                "description": "Discuss art, books, movies",
                "icon": "🎨",
                "level_focus": {
                    "A1-A2": [
                        "Describe art and artistic works simply",
                        "Talk about books, movies, and TV shows you like",
                        "Express basic opinions about culture",
                        "Understand simple cultural references"
                    ],
                    "B1-B2": [
                        "Discuss artistic works and express detailed opinions",
                        "Analyze themes and messages in art and literature",
                        "Compare different artistic styles and periods",
                        "Engage in cultural discussions"
                    ],
                    "C1-C2": [
                        "Analyze literature and art critically",
                        "Understand complex cultural references and symbolism",
                        "Engage in sophisticated cultural discussions",
                        "Discuss artistic movements and their impact"
                    ]
                },
                "key_vocabulary": ["art", "literature", "novel", "painting", "film", "culture", "artist"],
                "key_phrases": ["I really enjoyed...", "The theme is...", "It reminds me of...", "The artist conveys..."],
                "skill_priorities": {
                    "vocabulary": 1.3,
                    "coherence": 1.2,
                    "fluency": 1.1,
                    "grammar": 1.0,
                    "pronunciation": 0.9
                }
            }
        }
    }
}


def get_level_category(level: str) -> str:
    """
    Map CEFR level to category for goal selection
    
    Args:
        level: CEFR level (A1, A2, B1, B2, C1, C2)
        
    Returns:
        Level category (A1-A2, B1-B2, or C1-C2)
    """
    if level in ["A1", "A2"]:
        return "A1-A2"
    elif level in ["B1", "B2"]:
        return "B1-B2"
    else:
        return "C1-C2"


def get_enriched_goal(goal_id: str) -> Dict[str, Any]:
    """
    Get enriched goal configuration by ID
    
    Args:
        goal_id: Goal identifier (e.g., "travel", "business")
        
    Returns:
        Goal configuration dictionary
    """
    return ENRICHED_GOALS.get(goal_id, {})


def get_sub_goal(goal_id: str, sub_goal_id: str) -> Dict[str, Any]:
    """
    Get specific sub-goal configuration
    
    Args:
        goal_id: Main goal identifier
        sub_goal_id: Sub-goal identifier
        
    Returns:
        Sub-goal configuration dictionary
    """
    goal = ENRICHED_GOALS.get(goal_id, {})
    sub_goals = goal.get("sub_goals", {})
    return sub_goals.get(sub_goal_id, {})


def get_sub_goal_activities(
    goal_id: str,
    sub_goal_id: str,
    level: str
) -> List[str]:
    """
    Get level-appropriate activities for a sub-goal
    
    Args:
        goal_id: Main goal identifier
        sub_goal_id: Sub-goal identifier
        level: CEFR level
        
    Returns:
        List of activities appropriate for the level
    """
    sub_goal = get_sub_goal(goal_id, sub_goal_id)
    level_category = get_level_category(level)
    level_focus = sub_goal.get("level_focus", {})
    return level_focus.get(level_category, [])


def get_all_main_goals() -> List[Dict[str, Any]]:
    """
    Get list of all main goal categories
    
    Returns:
        List of main goal configurations (without sub-goals)
    """
    return [
        {
            "id": goal_id,
            "text": goal_data["text"],
            "category": goal_data["category"],
            "description": goal_data["description"],
            "icon": goal_data.get("icon", ""),
            "sub_goal_count": len(goal_data.get("sub_goals", {}))
        }
        for goal_id, goal_data in ENRICHED_GOALS.items()
    ]


def get_sub_goals_for_main_goal(goal_id: str) -> List[Dict[str, Any]]:
    """
    Get list of sub-goals for a main goal
    
    Args:
        goal_id: Main goal identifier
        
    Returns:
        List of sub-goal configurations (without level details)
    """
    goal = ENRICHED_GOALS.get(goal_id, {})
    sub_goals = goal.get("sub_goals", {})
    
    return [
        {
            "id": sub_goal_id,
            "text": sub_goal_data["text"],
            "description": sub_goal_data["description"],
            "icon": sub_goal_data.get("icon", ""),
            "main_goal": goal_id
        }
        for sub_goal_id, sub_goal_data in sub_goals.items()
    ]

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from bson import ObjectId

from models.world_building_models import (
    StoryWorldInDB, WorldState, LearningObjectives, CollaborationSettings, Statistics,
    Character, Location, ImportantItem,
    LanguageEnum, TargetLevelEnum, GenreEnum, PrivacySettingEnum, 
    PrimaryFocusEnum, ContributionOrderEnum, WorldStatusEnum
)
from services.world_building_service import world_building_service

class WorldBuildingSeedData:
    """Generate seed data for collaborative world building feature"""
    
    @staticmethod
    def create_sample_worlds() -> List[Dict[str, Any]]:
        """Create sample story worlds for different languages and levels"""
        
        # Create a sample creator ID (this would be replaced with actual user IDs)
        sample_creator_id = ObjectId()
        
        worlds = []
        
        # 1. English Mystery World (B1 Level)
        mystery_world = {
            "_id": ObjectId(),
            "title": "The Vanishing Library",
            "description": "A mysterious library where books disappear overnight. Join other learners to solve this supernatural mystery while practicing English conversation skills.",
            "creator_id": sample_creator_id,
            "language": LanguageEnum.EN.value,
            "target_level": TargetLevelEnum.B1.value,
            "genre": GenreEnum.MYSTERY.value,
            "privacy_setting": PrivacySettingEnum.PUBLIC.value,
            "learning_objectives": {
                "primary_focus": PrimaryFocusEnum.VOCABULARY.value,
                "target_structures": [
                    "Past perfect tense for describing events",
                    "Modal verbs for speculation (might, could, must)",
                    "Question formation for investigations"
                ],
                "vocabulary_themes": [
                    "Mystery and detective vocabulary",
                    "Library and book-related terms",
                    "Emotions and reactions"
                ]
            },
            "world_state": {
                "current_plot_point": "The librarian has discovered that three rare books have vanished from the restricted section. Strange whispers can be heard after midnight.",
                "active_characters": [
                    {
                        "name": "Eleanor Blackwood",
                        "role": "Head Librarian",
                        "description": "A knowledgeable but secretive woman who has worked at the library for 30 years"
                    },
                    {
                        "name": "Detective Martinez",
                        "role": "Local Police Detective",
                        "description": "A thorough investigator who specializes in unusual cases"
                    }
                ],
                "locations": [
                    {
                        "name": "The Restricted Section",
                        "description": "A dimly lit area with ancient books behind locked glass cases"
                    },
                    {
                        "name": "The Reading Room",
                        "description": "A grand hall with tall windows and comfortable reading chairs"
                    }
                ],
                "important_items": [
                    {
                        "name": "The Missing Books",
                        "significance": "Three rare manuscripts on supernatural phenomena that disappeared without a trace"
                    },
                    {
                        "name": "Security Camera Footage",
                        "significance": "Shows the books were there at closing time but gone by morning"
                    }
                ]
            },
            "collaboration_settings": {
                "max_contributors": 6,
                "session_duration_minutes": 15,
                "requires_approval": False,
                "contribution_order": ContributionOrderEnum.SEQUENTIAL.value
            },
            "statistics": {
                "total_sessions": 0,
                "total_contributors": 1,
                "average_session_rating": 0.0,
                "completion_rate": 0.0,
                "learning_effectiveness_score": 0.0
            },
            "contributors": [sample_creator_id],
            "status": WorldStatusEnum.ACTIVE.value,
            "tags": ["mystery", "supernatural", "investigation", "beginner-friendly"],
            "featured": True,
            "created_at": datetime.utcnow() - timedelta(days=2),
            "updated_at": datetime.utcnow(),
            "last_contribution_at": datetime.utcnow() - timedelta(hours=3)  # Recent activity for trending
        }
        worlds.append(mystery_world)
        
        # 2. Spanish Adventure World (A2 Level)
        adventure_world = {
            "_id": ObjectId(),
            "title": "La Búsqueda del Tesoro Perdido",
            "description": "Una aventura emocionante en busca de un tesoro perdido en las montañas de América del Sur. Practica español mientras exploras lugares exóticos.",
            "creator_id": sample_creator_id,
            "language": LanguageEnum.ES.value,
            "target_level": TargetLevelEnum.A2.value,
            "genre": GenreEnum.ADVENTURE.value,
            "privacy_setting": PrivacySettingEnum.PUBLIC.value,
            "learning_objectives": {
                "primary_focus": PrimaryFocusEnum.GRAMMAR.value,
                "target_structures": [
                    "Preterite vs imperfect tense",
                    "Commands and directions",
                    "Future tense for plans"
                ],
                "vocabulary_themes": [
                    "Adventure and exploration",
                    "Geography and nature",
                    "Travel and transportation"
                ]
            },
            "world_state": {
                "current_plot_point": "El grupo ha encontrado el primer mapa que lleva a una cueva misteriosa en las montañas. Necesitan decidir qué equipo llevar.",
                "active_characters": [
                    {
                        "name": "Carlos Mendoza",
                        "role": "Guía Local",
                        "description": "Un experimentado guía de montaña que conoce todos los senderos secretos"
                    },
                    {
                        "name": "Ana Rodríguez",
                        "role": "Arqueóloga",
                        "description": "Una experta en civilizaciones antiguas que puede interpretar los símbolos del mapa"
                    }
                ],
                "locations": [
                    {
                        "name": "El Pueblo Base",
                        "description": "Un pequeño pueblo en las montañas donde comienza la aventura"
                    },
                    {
                        "name": "La Cueva Misteriosa",
                        "description": "Una cueva antigua con pinturas rupestres y pasajes secretos"
                    }
                ],
                "important_items": [
                    {
                        "name": "El Mapa Antiguo",
                        "significance": "Un mapa de 300 años que muestra la ubicación del tesoro"
                    },
                    {
                        "name": "La Brújula Dorada",
                        "significance": "Una brújula especial que apunta hacia el tesoro"
                    }
                ]
            },
            "collaboration_settings": {
                "max_contributors": 8,
                "session_duration_minutes": 12,
                "requires_approval": False,
                "contribution_order": ContributionOrderEnum.RANDOM.value
            },
            "statistics": {
                "total_sessions": 0,
                "total_contributors": 1,
                "average_session_rating": 0.0,
                "completion_rate": 0.0,
                "learning_effectiveness_score": 0.0
            },
            "contributors": [sample_creator_id],
            "status": WorldStatusEnum.ACTIVE.value,
            "tags": ["aventura", "tesoro", "montañas", "principiante"],
            "featured": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_contribution_at": None
        }
        worlds.append(adventure_world)
        
        # 3. French Cultural World (B2 Level)
        cultural_world = {
            "_id": ObjectId(),
            "title": "Le Festival de Cuisine Française",
            "description": "Participez à l'organisation d'un festival culinaire à Lyon. Découvrez la culture française tout en perfectionnant votre français.",
            "creator_id": sample_creator_id,
            "language": LanguageEnum.FR.value,
            "target_level": TargetLevelEnum.B2.value,
            "genre": GenreEnum.CULTURAL.value,
            "privacy_setting": PrivacySettingEnum.PUBLIC.value,
            "learning_objectives": {
                "primary_focus": PrimaryFocusEnum.CULTURAL.value,
                "target_structures": [
                    "Subjunctive mood for opinions",
                    "Complex sentence structures",
                    "Formal and informal registers"
                ],
                "vocabulary_themes": [
                    "French cuisine and cooking",
                    "Cultural events and festivals",
                    "Business and organization"
                ]
            },
            "world_state": {
                "current_plot_point": "Le comité d'organisation doit choisir les chefs participants et planifier les événements spéciaux du festival. Les sponsors attendent une présentation.",
                "active_characters": [
                    {
                        "name": "Chef Marie Dubois",
                        "role": "Chef Étoilée",
                        "description": "Une chef renommée spécialisée dans la cuisine lyonnaise traditionnelle"
                    },
                    {
                        "name": "Pierre Moreau",
                        "role": "Organisateur d'Événements",
                        "description": "Un expert en organisation de festivals culturels avec 15 ans d'expérience"
                    }
                ],
                "locations": [
                    {
                        "name": "Place Bellecour",
                        "description": "La grande place de Lyon où se déroulera le festival principal"
                    },
                    {
                        "name": "Les Halles de Lyon",
                        "description": "Le marché couvert célèbre pour ses produits gastronomiques"
                    }
                ],
                "important_items": [
                    {
                        "name": "Le Budget du Festival",
                        "significance": "Un budget de 50 000 euros à répartir entre les différentes activités"
                    },
                    {
                        "name": "La Liste des Sponsors",
                        "significance": "Les entreprises locales qui soutiennent financièrement l'événement"
                    }
                ]
            },
            "collaboration_settings": {
                "max_contributors": 5,
                "session_duration_minutes": 20,
                "requires_approval": True,
                "contribution_order": ContributionOrderEnum.SCHEDULED.value
            },
            "statistics": {
                "total_sessions": 0,
                "total_contributors": 1,
                "average_session_rating": 0.0,
                "completion_rate": 0.0,
                "learning_effectiveness_score": 0.0
            },
            "contributors": [sample_creator_id],
            "status": WorldStatusEnum.ACTIVE.value,
            "tags": ["culture", "cuisine", "festival", "lyon", "intermédiaire"],
            "featured": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_contribution_at": None
        }
        worlds.append(cultural_world)
        
        # 4. German Business World (C1 Level)
        business_world = {
            "_id": ObjectId(),
            "title": "Die Startup-Gründung",
            "description": "Gründen Sie gemeinsam ein innovatives Tech-Startup in Berlin. Üben Sie Geschäftsdeutsch in realistischen Situationen.",
            "creator_id": sample_creator_id,
            "language": LanguageEnum.DE.value,
            "target_level": TargetLevelEnum.C1.value,
            "genre": GenreEnum.BUSINESS.value,
            "privacy_setting": PrivacySettingEnum.PUBLIC.value,
            "learning_objectives": {
                "primary_focus": PrimaryFocusEnum.VOCABULARY.value,
                "target_structures": [
                    "Complex business terminology",
                    "Conditional sentences for negotiations",
                    "Passive voice in formal contexts"
                ],
                "vocabulary_themes": [
                    "Business and entrepreneurship",
                    "Technology and innovation",
                    "Finance and investment"
                ]
            },
            "world_state": {
                "current_plot_point": "Das Team hat eine innovative App-Idee entwickelt und muss nun Investoren überzeugen. Die erste Präsentation vor Venture Capital-Gebern steht bevor.",
                "active_characters": [
                    {
                        "name": "Dr. Klaus Weber",
                        "role": "Investor",
                        "description": "Ein erfahrener Venture Capital-Investor, der in Tech-Startups spezialisiert ist"
                    },
                    {
                        "name": "Sarah Müller",
                        "role": "Marketing-Expertin",
                        "description": "Eine kreative Marketing-Strategin mit Erfahrung in der Startup-Szene"
                    }
                ],
                "locations": [
                    {
                        "name": "Das Startup-Büro",
                        "description": "Ein moderner Co-Working-Space in Berlin-Mitte mit allem nötigen Equipment"
                    },
                    {
                        "name": "Der Konferenzraum",
                        "description": "Ein eleganter Besprechungsraum für wichtige Investoren-Meetings"
                    }
                ],
                "important_items": [
                    {
                        "name": "Der Businessplan",
                        "significance": "Ein detaillierter 50-seitiger Plan mit Marktanalyse und Finanzprognosen"
                    },
                    {
                        "name": "Der Prototyp",
                        "significance": "Eine funktionsfähige Beta-Version der innovativen App"
                    }
                ]
            },
            "collaboration_settings": {
                "max_contributors": 4,
                "session_duration_minutes": 25,
                "requires_approval": True,
                "contribution_order": ContributionOrderEnum.SEQUENTIAL.value
            },
            "statistics": {
                "total_sessions": 0,
                "total_contributors": 1,
                "average_session_rating": 0.0,
                "completion_rate": 0.0,
                "learning_effectiveness_score": 0.0
            },
            "contributors": [sample_creator_id],
            "status": WorldStatusEnum.ACTIVE.value,
            "tags": ["business", "startup", "technologie", "berlin", "fortgeschritten"],
            "featured": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_contribution_at": None
        }
        worlds.append(business_world)
        
        # 5. Dutch Historical World (A2 Level)
        historical_world = {
            "_id": ObjectId(),
            "title": "De Gouden Eeuw van Amsterdam",
            "description": "Reis terug naar de 17e eeuw en beleef de Gouden Eeuw van Amsterdam. Leer Nederlands terwijl je de rijke geschiedenis ontdekt.",
            "creator_id": sample_creator_id,
            "language": LanguageEnum.NL.value,
            "target_level": TargetLevelEnum.A2.value,
            "genre": GenreEnum.HISTORICAL.value,
            "privacy_setting": PrivacySettingEnum.PUBLIC.value,
            "learning_objectives": {
                "primary_focus": PrimaryFocusEnum.PRONUNCIATION.value,
                "target_structures": [
                    "Past tense for historical events",
                    "Descriptive adjectives",
                    "Time expressions"
                ],
                "vocabulary_themes": [
                    "Historical periods and events",
                    "Dutch culture and traditions",
                    "Architecture and art"
                ]
            },
            "world_state": {
                "current_plot_point": "Het is 1650 en Amsterdam bloeit als handelscentrum. Jullie zijn kooplieden die een belangrijke handelsmissie naar Azië moeten voorbereiden.",
                "active_characters": [
                    {
                        "name": "Kapitein Jan van der Berg",
                        "role": "Scheepskapitein",
                        "description": "Een ervaren zeeman die vele reizen naar de Oost heeft gemaakt"
                    },
                    {
                        "name": "Mevrouw Elisabeth de Wit",
                        "role": "Rijke Koopvrouw",
                        "description": "Een invloedrijke handelaar in specerijen en luxegoederen"
                    }
                ],
                "locations": [
                    {
                        "name": "De Amsterdamse Haven",
                        "description": "Een drukke haven vol met schepen uit alle delen van de wereld"
                    },
                    {
                        "name": "Het Koopmanshuis",
                        "description": "Een prachtig grachtenpand waar belangrijke handelsbeslissingen worden genomen"
                    }
                ],
                "important_items": [
                    {
                        "name": "De Handelskaart",
                        "significance": "Een gedetailleerde kaart van de handelsroutes naar Azië"
                    },
                    {
                        "name": "Het VOC-Contract",
                        "significance": "Een officieel contract met de Verenigde Oost-Indische Compagnie"
                    }
                ]
            },
            "collaboration_settings": {
                "max_contributors": 6,
                "session_duration_minutes": 15,
                "requires_approval": False,
                "contribution_order": ContributionOrderEnum.RANDOM.value
            },
            "statistics": {
                "total_sessions": 0,
                "total_contributors": 1,
                "average_session_rating": 0.0,
                "completion_rate": 0.0,
                "learning_effectiveness_score": 0.0
            },
            "contributors": [sample_creator_id],
            "status": WorldStatusEnum.ACTIVE.value,
            "tags": ["geschiedenis", "gouden eeuw", "amsterdam", "handel"],
            "featured": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_contribution_at": None
        }
        worlds.append(historical_world)
        
        return worlds
    
    @staticmethod
    async def seed_database():
        """Seed the database with sample worlds"""
        try:
            print("🌱 [SEED_DATA] Starting world building seed data generation...")
            
            # Initialize indexes first
            await world_building_service.initialize_indexes()
            
            # Check if seed data already exists
            existing_worlds = await world_building_service.story_worlds.count_documents({})
            if existing_worlds > 0:
                print(f"⚠️ [SEED_DATA] Found {existing_worlds} existing worlds, skipping seed data")
                return
            
            # Create sample worlds
            sample_worlds = WorldBuildingSeedData.create_sample_worlds()
            
            # Insert worlds into database
            result = await world_building_service.story_worlds.insert_many(sample_worlds)
            
            print(f"✅ [SEED_DATA] Successfully created {len(result.inserted_ids)} sample worlds:")
            for i, world in enumerate(sample_worlds):
                print(f"   {i+1}. {world['title']} ({world['language'].upper()}, {world['target_level']})")
            
            print("🌱 [SEED_DATA] World building seed data generation completed!")
            
        except Exception as e:
            print(f"❌ [SEED_DATA] Error seeding database: {str(e)}")
            raise

# Standalone script execution
async def main():
    """Run seed data generation as standalone script"""
    await WorldBuildingSeedData.seed_database()

if __name__ == "__main__":
    asyncio.run(main())

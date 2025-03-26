import os
import json
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv
from openai import OpenAI

# Import sentence assessment functionality
from sentence_assessment import SentenceAssessmentRequest, SentenceAssessmentResponse, GrammarIssue, \
    recognize_speech, analyze_sentence, generate_exercises

# Load environment variables
load_dotenv()

# Check if OpenAI API key is configured
if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: OPENAI_API_KEY is not configured in .env file")
    print("Please add OPENAI_API_KEY=your_api_key to your .env file")

app = FastAPI(title="Language Tutor Backend API")

# CORS configuration
origins = []
if os.getenv("ENVIRONMENT") == "production":
    # In Railway, we need to be more permissive with CORS
    # Use the correct Railway URL as the default
    frontend_url = os.getenv("FRONTEND_URL", "https://taco.up.railway.app")
    
    # Add the Railway URL as the origin
    origins = [
        frontend_url,
        "https://taco.up.railway.app",  # Correct URL
    ]
    
    print(f"Configured CORS with origins: {origins}")
    
    # If we're in Railway, also allow the request from any origin
    # This is more permissive but ensures the app works in Railway's environment
    if os.getenv("RAILWAY") == "true":
        origins = ["*"]
        print("Running in Railway environment, allowing all origins")
else:
    # Allow all origins during development
    origins = ["*"]

print(f"Configured CORS with origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler for better debugging in Railway
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        # Process the request and get the response
        response = await call_next(request)
        return response
    except Exception as e:
        # Log the error with traceback
        error_detail = f"Error processing request: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        
        # Return a JSON response with error details
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(e),
                "path": request.url.path,
                "railway": os.getenv("RAILWAY") == "true",
                "environment": os.getenv("ENVIRONMENT", "development")
            }
        )

# Simple test endpoint to verify API connectivity
@app.get("/api/test")
async def test_endpoint():
    return {"message": "Backend API is working correctly"}

# Enhanced health check endpoint with detailed status information
@app.get("/api/health")
async def health_check():
    import platform
    import sys
    import time
    
    # Get environment information
    is_production = os.getenv("ENVIRONMENT") == "production"
    environment = "production" if is_production else "development"
    
    # Get system information
    system_info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "timestamp": time.time(),
        "environment": environment,
        "railway": os.getenv("RAILWAY") == "true"
    }
    
    # Return comprehensive health data
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime": time.time(),  # You could track actual uptime if needed
        "system_info": system_info,
        "api_routes": [
            "/api/languages",
            "/api/realtime/token",
            "/api/test"
        ]
    }

# Serve static files in production
if os.getenv("ENVIRONMENT") == "production":
    # Check for Docker environment first
    docker_frontend_path = Path("/app/frontend")
    local_frontend_path = Path(__file__).parent.parent / "frontend"
    
    # Determine which path to use
    frontend_path = docker_frontend_path if docker_frontend_path.exists() else local_frontend_path
    out_path = frontend_path / "out"
    
    print(f"Serving Next.js files from: {frontend_path}")
    
    # Mount static files only if the directories exist
    # Check if the out directory exists (for export mode)
    if out_path.exists():
        # Check and mount _next directory if it exists
        next_static_path = out_path / "_next"
        if next_static_path.exists():
            print(f"Mounting /_next from {next_static_path}")
            app.mount("/_next", StaticFiles(directory=str(next_static_path)), name="next-static")
        
        # Check and mount static directory if it exists
        static_path = out_path / "static"
        if static_path.exists():
            print(f"Mounting /static from {static_path}")
            app.mount("/static", StaticFiles(directory=str(static_path)), name="static-files")
    
    # Fallback to .next directory (for standalone mode)
    next_path = frontend_path / ".next"
    if next_path.exists():
        print(f"Mounting /_next from {next_path}")
        app.mount("/_next", StaticFiles(directory=str(next_path)), name="next-static")
        
        # Check and mount public directory if it exists
        public_path = frontend_path / "public"
        if public_path.exists():
            print(f"Mounting /static from {public_path}")
            app.mount("/static", StaticFiles(directory=str(public_path)), name="public")

# Define models for request validation
class TutorSessionRequest(BaseModel):
    language: str
    level: str
    voice: Optional[str] = "alloy"  # Options: alloy, echo, fable, onyx, nova, shimmer
    topic: Optional[str] = None  # Topic to focus the conversation on
    user_prompt: Optional[str] = None  # User prompt for custom topics

# Simple endpoint for testing connection
@app.get("/api/test")
async def test_connection():
    return {"message": "Backend connection successful"}

# Mock ephemeral key endpoint for testing when OpenAI API key is not available
@app.post("/api/mock-token")
async def mock_token(request: TutorSessionRequest):
    # Log the request data for debugging
    print(f"Providing mock ephemeral key for testing with language: {request.language}, level: {request.level}, voice: {request.voice}, topic: {request.topic}")
    print(f"Request body received: language={request.language}, level={request.level}, voice={request.voice}, topic={request.topic}")
    
    from datetime import datetime, timedelta
    
    expiry = datetime.now() + timedelta(hours=1)
    return {
        "ephemeral_key": "mock_ephemeral_key_for_testing",
        "expires_at": expiry.isoformat()
    }

# Endpoint to get available languages and levels
@app.get("/api/languages")
async def get_languages():
    try:
        # Load the tutor instructions from the JSON file
        instructions_path = Path(__file__).parent / "tutor_instructions.json"
        if not instructions_path.exists():
            raise HTTPException(status_code=404, detail="Tutor instructions not found")
        
        with open(instructions_path, "r") as f:
            tutor_data = json.load(f)
        
        # Extract just the languages and levels structure (without the full instructions)
        languages_data = {}
        for lang_code, lang_data in tutor_data.get("languages", {}).items():
            languages_data[lang_code] = {
                "name": lang_data.get("name", ""),
                "levels": {level: data.get("description", "") for level, data in lang_data.get("levels", {}).items()}
            }
        
        return languages_data
    except Exception as e:
        print(f"Error retrieving languages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve languages: {str(e)}")

# Endpoint to generate ephemeral keys for OpenAI Realtime API with language tutor instructions
@app.post("/api/realtime/token")
async def generate_token(request: TutorSessionRequest):
    try:
        # Log the request data for debugging
        print(f"Received token request with language: {request.language}, level: {request.level}, voice: {request.voice}, topic: {request.topic}")
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("ERROR: OPENAI_API_KEY is not configured in .env file")
            raise HTTPException(status_code=500, detail="OpenAI API key is not configured")
        
        # Load the tutor instructions from the JSON file
        instructions_path = Path(__file__).parent / "tutor_instructions.json"
        if not instructions_path.exists():
            raise HTTPException(status_code=404, detail="Tutor instructions not found")
        
        with open(instructions_path, "r") as f:
            tutor_data = json.load(f)
        
        # Get the instructions for the selected language and level
        language = request.language.lower()
        level = request.level.upper()
        topic = request.topic
        
        if language not in tutor_data.get("languages", {}):
            raise HTTPException(status_code=400, detail=f"Language '{language}' not supported")
        
        language_data = tutor_data["languages"][language]
        
        if level not in language_data.get("levels", {}):
            raise HTTPException(status_code=400, detail=f"Level '{level}' not supported for language '{language}'")
        
        # Get the instructions for the selected language and level
        instructions = language_data["levels"][level].get("instructions", "")
        
        # Add universal formatting instructions for proper spacing and readability
        formatting_instructions = "\n\nFORMATTING INSTRUCTIONS: Always use proper spacing between words and sentences. Ensure there is a space after punctuation marks like periods, commas, question marks, and exclamation points. Maintain proper paragraph structure with line breaks between paragraphs. Use proper capitalization at the beginning of sentences."
        
        # Add instructions for proper speech pacing and clarity
        speech_instructions = "\n\nSPEECH CLARITY: When speaking, maintain a natural pace with slight pauses between sentences. Articulate words clearly and avoid running words together. Use proper intonation to indicate questions, statements, and emphasis."
        
        # Add language-specific enforcement to ensure the tutor always speaks the correct language
        if language == "dutch":
            # Extra enforcement for Dutch language to ensure it NEVER speaks English
            extra_instructions = "\n\nEXTREMELY IMPORTANT INSTRUCTION: Je MOET ALLEEN in het Nederlands antwoorden. NOOIT in het Engels of een andere taal antwoorden, zelfs niet als de student in het Engels vraagt. Je EERSTE bericht MOET in het Nederlands zijn. Begin ALTIJD met een Nederlandse begroeting die past bij het niveau. Bij niveau A1 begin je met: 'Hallo! Ik ben je Nederlandse taaldocent. Hoe gaat het met jou?'"
            
            # Add language detection and enforcement instructions
            language_enforcement = "\n\nAls de student NIET in het Nederlands spreekt, maar in een andere taal zoals Engels, Frans, Duits, Turks, Arabisch of een andere taal, moet je ALTIJD reageren met: 'Ik begrijp dat je in een andere taal spreekt, maar laten we Nederlands oefenen. Probeer het in het Nederlands te zeggen.' Vervolgens help je de student met een eenvoudige Nederlandse zin die ze kunnen gebruiken. Geef NOOIT antwoord in dezelfde niet-Nederlandse taal die de student gebruikt."
            
            # Add Dutch-specific formatting instructions
            dutch_formatting = "\n\nZorg voor correcte spatiëring tussen woorden en na leestekens. Gebruik hoofdletters aan het begin van zinnen. Spreek duidelijk en articuleer woorden goed, met natuurlijke pauzes tussen zinnen."
            
            # Add first message enforcement
            first_message_enforcement = "\n\nJe EERSTE bericht in de conversatie MOET in het Nederlands zijn. Begin NOOIT in het Engels of een andere taal. Begin met een Nederlandse begroeting zoals 'Hallo' of 'Goedendag' gevolgd door een eenvoudige vraag in het Nederlands."
            
            instructions = instructions + extra_instructions + language_enforcement + dutch_formatting + first_message_enforcement
            print("Added extra Dutch-only enforcement to instructions")
        elif language == "spanish":
            # Extra enforcement for Spanish language
            extra_instructions = "\n\nINSTRUCCIÓN EXTREMADAMENTE IMPORTANTE: DEBES responder SOLO en español. NUNCA respondas en inglés u otro idioma, incluso si el estudiante pregunta en inglés. Tu PRIMER mensaje DEBE ser en español. Siempre comienza con un saludo en español apropiado para el nivel. Para el nivel A1, comienza con: '¡Hola! Soy tu profesor de español. ¿Cómo estás hoy?'"
            
            # Add language detection and enforcement instructions
            language_enforcement = "\n\nSi el estudiante NO habla en español, sino en otro idioma como inglés, francés, alemán u otro, SIEMPRE debes responder con: 'Entiendo que estás hablando en otro idioma, pero practiquemos español. Intenta decirlo en español.' Luego, ayuda al estudiante con una frase simple en español que puedan usar. NUNCA respondas en el mismo idioma no español que usa el estudiante."
            
            # Add Spanish-specific formatting instructions
            spanish_formatting = "\n\nAsegúrate de usar el espaciado correcto entre palabras y después de signos de puntuación. Usa mayúsculas al comienzo de las oraciones. Habla claramente y articula bien las palabras, con pausas naturales entre oraciones."
            
            # Add first message enforcement
            first_message_enforcement = "\n\nTu PRIMER mensaje en la conversación DEBE ser en español. NUNCA comiences en inglés u otro idioma. Comienza con un saludo en español como '¡Hola!' o '¡Buenos días!' seguido de una pregunta simple en español."
            
            instructions = instructions + extra_instructions + language_enforcement + spanish_formatting + first_message_enforcement
            print("Added extra Spanish-only enforcement to instructions")
            
        elif language == "german":
            # Extra enforcement for German language
            extra_instructions = "\n\nÄUßERST WICHTIGE ANWEISUNG: Du MUSST NUR auf Deutsch antworten. NIEMALS auf Englisch oder in einer anderen Sprache antworten, auch wenn der Schüler auf Englisch fragt. Deine ERSTE Nachricht MUSS auf Deutsch sein. Beginne immer mit einer deutschen Begrüßung, die dem Niveau entspricht. Für Niveau A1 beginne mit: 'Hallo! Ich bin dein Deutschlehrer. Wie geht es dir heute?'"
            
            # Add language detection and enforcement instructions
            language_enforcement = "\n\nWenn der Schüler NICHT auf Deutsch spricht, sondern in einer anderen Sprache wie Englisch, Französisch, Spanisch oder einer anderen Sprache, musst du IMMER antworten mit: 'Ich verstehe, dass du in einer anderen Sprache sprichst, aber lass uns Deutsch üben. Versuche es auf Deutsch zu sagen.' Dann hilfst du dem Schüler mit einem einfachen deutschen Satz, den sie verwenden können. Antworte NIEMALS in der gleichen nicht-deutschen Sprache, die der Schüler verwendet."
            
            # Add German-specific formatting instructions
            german_formatting = "\n\nAchte auf korrekte Abstände zwischen Wörtern und nach Satzzeichen. Verwende Großbuchstaben am Anfang von Sätzen. Sprich deutlich und artikuliere Wörter gut, mit natürlichen Pausen zwischen Sätzen."
            
            # Add first message enforcement
            first_message_enforcement = "\n\nDeine ERSTE Nachricht in der Konversation MUSS auf Deutsch sein. Beginne NIEMALS auf Englisch oder in einer anderen Sprache. Beginne mit einer deutschen Begrüßung wie 'Hallo' oder 'Guten Tag', gefolgt von einer einfachen Frage auf Deutsch."
            
            instructions = instructions + extra_instructions + language_enforcement + german_formatting + first_message_enforcement
            print("Added extra German-only enforcement to instructions")
            
        elif language == "french":
            # Extra enforcement for French language
            extra_instructions = "\n\nINSTRUCTION EXTRÊMEMENT IMPORTANTE: Tu DOIS répondre UNIQUEMENT en français. Ne réponds JAMAIS en anglais ou dans une autre langue, même si l'étudiant pose une question en anglais. Ton PREMIER message DOIT être en français. Commence toujours par une salutation en français adaptée au niveau. Pour le niveau A1, commence par: 'Bonjour! Je suis ton professeur de français. Comment vas-tu aujourd'hui?'"
            
            # Add language detection and enforcement instructions
            language_enforcement = "\n\nSi l'étudiant NE parle PAS français, mais une autre langue comme l'anglais, l'allemand, l'espagnol ou une autre langue, tu dois TOUJOURS répondre avec: 'Je comprends que tu parles dans une autre langue, mais pratiquons le français. Essaie de le dire en français.' Ensuite, aide l'étudiant avec une phrase simple en français qu'il peut utiliser. Ne réponds JAMAIS dans la même langue non française que l'étudiant utilise."
            
            # Add French-specific formatting instructions
            french_formatting = "\n\nAssure-toi d'utiliser un espacement correct entre les mots et après les signes de ponctuation. Utilise des majuscules au début des phrases. Parle clairement et articule bien les mots, avec des pauses naturelles entre les phrases."
            
            # Add first message enforcement
            first_message_enforcement = "\n\nTon PREMIER message dans la conversation DOIT être en français. Ne commence JAMAIS en anglais ou dans une autre langue. Commence par une salutation en français comme 'Bonjour' ou 'Salut' suivie d'une question simple en français."
            
            instructions = instructions + extra_instructions + language_enforcement + french_formatting + first_message_enforcement
            print("Added extra French-only enforcement to instructions")
            
        elif language == "portuguese":
            # Extra enforcement for Portuguese language
            extra_instructions = "\n\nINSTRUÇÃO EXTREMAMENTE IMPORTANTE: Você DEVE responder APENAS em português. NUNCA responda em inglês ou em outro idioma, mesmo que o aluno pergunte em inglês. Sua PRIMEIRA mensagem DEVE ser em português. Sempre comece com uma saudação em português apropriada para o nível. Para o nível A1, comece com: 'Olá! Eu sou seu professor de português. Como você está hoje?'"
            
            # Add language detection and enforcement instructions
            language_enforcement = "\n\nSe o aluno NÃO estiver falando em português, mas em outro idioma como inglês, francês, alemão ou outro idioma, você deve SEMPRE responder com: 'Eu entendo que você está falando em outro idioma, mas vamos praticar português. Tente dizer isso em português.' Em seguida, ajude o aluno com uma frase simples em português que ele possa usar. NUNCA responda no mesmo idioma não português que o aluno está usando."
            
            # Add Portuguese-specific formatting instructions
            portuguese_formatting = "\n\nCertifique-se de usar o espaçamento correto entre palavras e após sinais de pontuação. Use letras maiúsculas no início das frases. Fale claramente e articule bem as palavras, com pausas naturais entre as frases."
            
            # Add first message enforcement
            first_message_enforcement = "\n\nSua PRIMEIRA mensagem na conversa DEVE ser em português. NUNCA comece em inglês ou em outro idioma. Comece com uma saudação em português como 'Olá' ou 'Bom dia' seguida de uma pergunta simples em português."
            
            instructions = instructions + extra_instructions + language_enforcement + portuguese_formatting + first_message_enforcement
            print("Added extra Portuguese-only enforcement to instructions")
            
        else:
            # For English language
            if language == "english":
                # Add English-specific instructions
                english_instructions = "\n\nEXTREMELY IMPORTANT INSTRUCTION: You MUST ONLY respond in English. Your FIRST message MUST be in English. Always start with an English greeting appropriate for the level. For A1 level, start with: 'Hello! I am your English language tutor. How are you today?'"
                
                # Add language detection and enforcement instructions
                language_enforcement = "\n\nIf the student is NOT speaking in English, but in another language such as Dutch, Spanish, German, French, or any other language, you must ALWAYS respond with: 'I understand you're speaking in another language, but let's practice English. Try to say it in English.' Then help the student with a simple English sentence they can use. NEVER respond in the same non-English language that the student is using."
                
                # Add English-specific formatting instructions
                english_formatting = "\n\nEnsure correct spacing between words and after punctuation marks. Use capital letters at the beginning of sentences. Speak clearly and articulate words well, with natural pauses between sentences."
                
                # Add first message enforcement
                first_message_enforcement = "\n\nYour FIRST message in the conversation MUST be in English. NEVER start in another language. Begin with an English greeting like 'Hello' or 'Good day' followed by a simple question in English."
                
                instructions = instructions + english_instructions + language_enforcement + english_formatting + first_message_enforcement
                print("Added English-only enforcement to instructions")
            else:
                # For other languages, add general language quality instructions
                language_quality = "\n\nLANGUAGE QUALITY: Use natural, conversational language appropriate for the student's level. Avoid overly complex vocabulary or grammar for lower levels. For higher levels, introduce more sophisticated language patterns gradually. ALWAYS start with a greeting in the selected language."
                
                # Add first message enforcement for other languages
                first_message_enforcement = "\n\nYour FIRST message in the conversation MUST be in the selected language. NEVER start in any other language."
                
                instructions = instructions + language_quality + first_message_enforcement
        
        # Add universal formatting and speech instructions
        instructions = instructions + formatting_instructions + speech_instructions
        
        # Add topic-specific instructions if a topic is provided
        if topic:
            # Find this section in the /api/realtime/token endpoint where topic-specific instructions are generated for Dutch
            if language == "dutch":
                topic_instructions = f"\n\nLET OP: In dit gesprek moet je ALLEEN over het volgende onderwerp praten: '{topic}'. Focus al je vragen, opmerkingen en discussies op dit onderwerp. Gebruik dit onderwerp als het centrale thema van het gesprek. Als de student over een ander onderwerp begint, breng het gesprek subtiel terug naar '{topic}'."

                # Add instruction to start by mentioning the topic
                topic_instructions += f"\n\nBELANGRIJK: Begin je EERSTE bericht door het onderwerp '{topic}' te noemen. Bijvoorbeeld: 'Hallo! Laten we vandaag over {topic} praten. Wat vind je van {topic}?'"
                
                # Add Dutch vocabulary suggestions for the topic
                if topic == "travel" or topic == "reizen":
                    topic_vocabulary = "\n\nGebruik deze woorden in het gesprek: reis, vakantie, bestemming, hotel, vliegen, trein, strand, bergen, paspoort, koffer, boeken, reserveren."
                elif topic == "food" or topic == "eten":
                    topic_vocabulary = "\n\nGebruik deze woorden in het gesprek: eten, drinken, restaurant, menu, bestellen, lekker, recept, koken, proeven, ingrediënten, maaltijd, ontbijt, lunch, diner."
                elif topic == "hobbies" or topic == "hobby's":
                    topic_vocabulary = "\n\nGebruik deze woorden in het gesprek: hobby, vrije tijd, sport, lezen, muziek, film, dansen, schilderen, wandelen, fietsen, verzamelen, spelen."
                elif topic == "custom" and hasattr(request, 'user_prompt') and request.user_prompt:
                    # For custom topics with user prompts in Dutch, fetch information using web search
                    print(f"Processing custom topic with user prompt in Dutch: {request.user_prompt[:50]}...")
                    try:
                        # Call the custom_topic function to get web search results
                        custom_topic_request = CustomTopicRequest(
                            language=language,
                            level=level,
                            voice=request.voice,
                            topic="custom",
                            user_prompt=request.user_prompt
                        )
                        
                        # Use the custom_topic function directly (not as an endpoint)
                        custom_response = await custom_topic(custom_topic_request)
                        
                        # Extract a topic name from the user prompt (first 100 chars)
                        short_topic_name = request.user_prompt[:100] + "..." if len(request.user_prompt) > 100 else request.user_prompt
                        
                        # Override the topic instructions to use the actual user prompt instead of 'custom'
                        topic_instructions = f"\n\nLET OP: In dit gesprek moet je ALLEEN over het volgende onderwerp praten: '{short_topic_name}'. Focus al je vragen, opmerkingen en discussies op dit onderwerp. Gebruik dit onderwerp als het centrale thema van het gesprek. Als de student over een ander onderwerp begint, breng het gesprek subtiel terug naar dit onderwerp."
                        
                        # Add instruction to start by mentioning the actual topic content
                        topic_instructions += f"\n\nBELANGRIJK: Begin je EERSTE bericht door het onderwerp '{short_topic_name}' te noemen. Bijvoorbeeld: 'Hallo! Laten we vandaag over {short_topic_name} praten. Wat vind je van dit onderwerp?'"
                        
                        # Add the web search results to the topic instructions
                        topic_vocabulary = f"\n\nHier is de nieuwste informatie over dit onderwerp die je in je gesprek kunt verwerken:\n{custom_response['response']}\n\nIntroduceer geleidelijk relevante woordenschat uit deze informatie, passend bij het niveau van de student."
                        print("Successfully added web search results to Dutch topic instructions")
                    except Exception as e:
                        print(f"Error fetching web search results for Dutch: {str(e)}")
                        topic_vocabulary = "\n\nIntroduceer geleidelijk relevante woordenschat voor dit onderwerp, passend bij het niveau van de student."
                else:
                    topic_vocabulary = "\n\nIntroduceer geleidelijk relevante woordenschat voor dit onderwerp, passend bij het niveau van de student."
                
                topic_instructions += topic_vocabulary
            else:  # English or other languages
                topic_instructions = f"\n\nIMPORTANT: In this conversation, you must ONLY talk about the following topic: '{topic}'. Focus all your questions, comments, and discussions on this topic. Use this topic as the central theme of the conversation. If the student starts talking about something else, gently bring the conversation back to '{topic}'."

                # Add instruction to start by mentioning the topic
                topic_instructions += f"\n\nCRITICAL: In your FIRST message, explicitly mention the topic '{topic}'. For example: 'Hello! Today we're going to talk about {topic}. What are your thoughts on {topic}?'"
                
                # Add English vocabulary suggestions for the topic
                if topic == "travel":
                    topic_vocabulary = "\n\nIncorporate these words in the conversation: travel, vacation, destination, hotel, flight, train, beach, mountains, passport, suitcase, booking, reservation."
                elif topic == "food":
                    topic_vocabulary = "\n\nIncorporate these words in the conversation: food, drink, restaurant, menu, order, delicious, recipe, cook, taste, ingredients, meal, breakfast, lunch, dinner."
                elif topic == "hobbies":
                    topic_vocabulary = "\n\nIncorporate these words in the conversation: hobby, free time, sports, reading, music, movies, dancing, painting, walking, cycling, collecting, playing."
                elif topic == "custom" and hasattr(request, 'user_prompt') and request.user_prompt:
                    # For custom topics with user prompts, fetch information using web search
                    print(f"Processing custom topic with user prompt: {request.user_prompt[:50]}...")
                    try:
                        # Call the custom_topic function to get web search results
                        custom_topic_request = CustomTopicRequest(
                            language=language,
                            level=level,
                            voice=request.voice,
                            topic="custom",
                            user_prompt=request.user_prompt
                        )
                        
                        # Use the custom_topic function directly (not as an endpoint)
                        custom_response = await custom_topic(custom_topic_request)
                        
                        # Extract a topic name from the user prompt (first 100 chars)
                        short_topic_name = request.user_prompt[:100] + "..." if len(request.user_prompt) > 100 else request.user_prompt
                        
                        # Override the topic instructions to use the actual user prompt instead of 'custom'
                        topic_instructions = f"\n\nIMPORTANT: In this conversation, you must ONLY talk about the following topic: '{short_topic_name}'. Focus all your questions, comments, and discussions on this topic. Use this topic as the central theme of the conversation. If the student starts talking about something else, gently bring the conversation back to this topic."
                        
                        # Add instruction to start by mentioning the actual topic content
                        topic_instructions += f"\n\nCRITICAL: In your FIRST message, explicitly mention that we'll be discussing '{short_topic_name}'. For example: 'Hello! Today we're going to talk about {short_topic_name}. What are your thoughts on this topic?'"
                        
                        # Add the web search results to the topic instructions
                        topic_vocabulary = f"\n\nHere is the latest information about this topic that you should incorporate in your conversation:\n{custom_response['response']}\n\nGradually introduce relevant vocabulary from this information, appropriate to the student's level."
                        print("Successfully added web search results to topic instructions")
                    except Exception as e:
                        print(f"Error fetching web search results: {str(e)}")
                        topic_vocabulary = "\n\nGradually introduce relevant vocabulary for this topic, appropriate to the student's level."
                else:
                    topic_vocabulary = "\n\nGradually introduce relevant vocabulary for this topic, appropriate to the student's level."
                
                topic_instructions += topic_vocabulary
            
            instructions = instructions + topic_instructions
            print(f"Added topic-specific instructions for topic: {topic}")
        
        print(f"Generating ephemeral key with OpenAI API for {language} at level {level}...")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/realtime/sessions",
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini-realtime-preview-2024-12-17",
                    "voice": request.voice,
                    "instructions": instructions,
                    "modalities": ["audio", "text"]
                },
                timeout=30.0
            )
        
        if response.status_code != 200:
            error_text = response.text
            print(f"OpenAI API error: {error_text}")
            raise HTTPException(
                status_code=response.status_code,
                detail={"error": "Error from OpenAI API", "details": error_text}
            )
        
        return response.json()
    except httpx.RequestError as e:
        print(f"Error generating ephemeral key: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate ephemeral key: {str(e)}")

# Define a new model for custom topic prompts
class CustomTopicRequest(BaseModel):
    language: str
    level: str
    voice: Optional[str] = "alloy"  # Options: alloy, echo, fable, onyx, nova, shimmer
    topic: Optional[str] = None  # Topic to focus the conversation on
    user_prompt: str  # The custom prompt from the user

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Warning: OPENAI_API_KEY not found in environment variables")

# Initialize OpenAI client with error handling
try:
    client = OpenAI(api_key=api_key)
    print("OpenAI client initialized successfully")
except TypeError as e:
    if "proxies" in str(e):
        print("Detected 'proxies' error in OpenAI initialization. Using alternative initialization...")
        # Alternative initialization without proxies
        client = OpenAI(api_key=api_key, http_client=httpx.Client())
        print("OpenAI client initialized with alternative method")
    else:
        print(f"Error initializing OpenAI client: {str(e)}")
        raise

# Endpoint to handle custom topic prompts
@app.post("/api/custom-topic")
async def custom_topic(request: CustomTopicRequest):
    try:
        # Extract user input from request
        user_prompt = request.user_prompt
        language = request.language.lower()
        level = request.level.upper()
        
        # Log the request for debugging
        print(f"Processing custom topic request: language={language}, level={level}, prompt={user_prompt[:50]}...")
        
        # Prepare system prompt based on language learning context
        system_prompt = f"You are a helpful language tutor for {language.capitalize()} at {level} level. "
        system_prompt += "Provide information that helps the user learn the language while answering their question. "
        system_prompt += "Include relevant vocabulary and phrases in your response when appropriate. "
        system_prompt += "Use web search to get the latest information when needed."
        
        try:
            # First try to use the OpenAI API with web search capabilities
            import httpx
            import json
            
            # Prepare the request payload
            payload = {
                "model": "gpt-4o-mini",
                "input": [
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "input_text",
                                "text": system_prompt
                            }
                        ]
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": user_prompt
                            }
                        ]
                    }
                ],
                "tools": [
                    {
                        "type": "web_search_preview",
                        "search_context_size": "medium"
                    }
                ],
                "temperature": 1,
                "max_output_tokens": 2048,
                "top_p": 1,
                "store": True
            }
            
            # Make the API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            async with httpx.AsyncClient() as async_client:
                response = await async_client.post(
                    "https://api.openai.com/v1/responses",
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                
                # Process the response
                if response.status_code == 200:
                    response_data = response.json()
                    print("Web search response received successfully")
                    
                    # Extract the response content
                    for output_item in response_data.get("output", []):
                        if output_item.get("type") == "message":
                            for content_item in output_item.get("content", []):
                                if content_item.get("type") == "output_text":
                                    return {"response": content_item.get("text", "")}
                    
                    # If we couldn't find the expected structure, return the raw response
                    return {"response": str(response_data)}
                else:
                    print(f"Web search API request failed with status code: {response.status_code}")
                    print(f"Response: {response.text}")
                    raise Exception(f"API request failed with status code: {response.status_code}")
                    
        except Exception as web_search_error:
            # If web search fails, fall back to standard chat completions
            print(f"Web search failed, falling back to standard chat: {str(web_search_error)}")
            
            # Call OpenAI API to generate response using the standard chat completions endpoint
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=1,
                max_tokens=2048,
                top_p=1
            )
            
            # Extract the response content
            if response and hasattr(response, 'choices') and response.choices:
                # Get the first choice's message content
                content = response.choices[0].message.content
                return {"response": content}
            
            # Fallback if response structure is unexpected
            return {"response": "I couldn't process your request at this time. Please try again later."}
    
    except Exception as e:
        print(f"Error processing custom topic request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process custom topic request: {str(e)}")

# Fallback route for serving the index.html in production
@app.get("/", response_class=HTMLResponse)
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str = "", request: Request = None):
    # Log request details for debugging Railway issues
    print(f"Requested path: {full_path}")
    if request:
        print(f"Request headers: {request.headers}")
    
    # Skip API routes
    if full_path and full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not Found")
    
    if os.getenv("NODE_ENV") == "production":
        # Check for Docker environment first
        docker_frontend_path = Path("/app/frontend")
        local_frontend_path = Path(__file__).parent.parent / "frontend"
        
        # Determine which path to use
        frontend_path = docker_frontend_path if docker_frontend_path.exists() else local_frontend_path
        print(f"Looking for index.html in: {frontend_path}")
        
        # Log the request headers for debugging
        print(f"Request headers: {request.headers if request else 'No request object'}")
        
        # First check for Next.js static files
        if full_path.startswith('_next/') or full_path.startswith('static/'):
            # Try to find the file in various locations
            possible_static_paths = [
                frontend_path / ".next" / full_path.replace('_next/', ''),
                frontend_path / ".next" / full_path,
                frontend_path / full_path,
                frontend_path / "public" / full_path,
            ]
            
            for path in possible_static_paths:
                if path.exists() and path.is_file():
                    print(f"Serving Next.js static file from: {path}")
                    return FileResponse(str(path))
        
        # Check if the request is for a static file (has extension)
        if '.' in full_path and not full_path.endswith('.html'):
            # Try to serve the static file directly
            static_file_paths = [
                frontend_path / "public" / full_path,
                frontend_path / full_path,
                frontend_path / ".next" / "static" / full_path,
            ]
            
            for path in static_file_paths:
                if path.exists() and path.is_file():
                    print(f"Serving static file from: {path}")
                    return FileResponse(str(path))
        
        # SPECIAL HANDLING FOR CLIENT-SIDE ROUTES
        # Check for specific client-side routes and serve appropriate content
        client_side_routes = ["language-selection", "level-selection", "speech", "topic-selection"]
        
        # For client-side routes, we want to serve the specific HTML file if it exists
        # Otherwise, serve a version of index.html that has the correct meta tags for the route
        if full_path in client_side_routes:
            print(f"Detected client-side route: {full_path}, looking for specific HTML file")
            
            # Look for route-specific HTML
            route_specific_paths = [
                frontend_path / ".next/server/app" / full_path / "index.html",
                frontend_path / ".next/server/pages" / full_path / "index.html",
                frontend_path / "out" / full_path / "index.html",
                frontend_path / ".next/server/app" / f"{full_path}.html"
            ]
            
            for path in route_specific_paths:
                if path.exists():
                    print(f"Found route-specific file for {full_path} at {path}")
                    return FileResponse(str(path))
            
            # If we're in Railway and it's a known client-side route but no specific file exists,
            # we need to create a custom HTML that will properly redirect on the client side
            print(f"No specific HTML found for {full_path}, creating a special redirect page")
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
              <head>
                <title>Language Tutor - {full_path.replace('-', ' ').title()}</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <meta name="route" content="/{full_path}">
                <script>
                  // Handle client-side routing for Next.js
                  window.addEventListener('DOMContentLoaded', function() {{
                    // Force the browser to the correct route path
                    const targetPath = '{full_path}';
                    if (window.location.pathname.endsWith(targetPath)) {{
                      // We're on the right URL, let Next.js take over when loaded
                      console.log('Target route already in URL - waiting for Next.js');
                    }} else {{
                      // Redirect to the proper URL
                      window.location.href = window.location.origin + '/' + targetPath;
                    }}
                  }});
                </script>
                <!-- Pull in Next.js scripts -->
                <link rel="stylesheet" href="/_next/static/css/cc3ec16c3199f2fd.css" />
              </head>
              <body>
                <div id="__next">
                  <div style="display: flex; justify-content: center; align-items: center; height: 100vh; flex-direction: column;">
                    <h1 style="color: #6466f1;">Language Tutor</h1>
                    <div style="margin-top: 20px;">
                      <div style="border: 4px solid #6466f1; border-radius: 50%; width: 40px; height: 40px; border-top-color: transparent; animation: spin 1s linear infinite;"></div>
                    </div>
                    <p style="margin-top: 20px;">Redirecting to {full_path.replace('-', ' ')}...</p>
                  </div>
                </div>
                <style>
                  @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                  }}
                </style>
                <script src="/_next/static/chunks/webpack-2e864253d8c6645c.js" defer></script>
                <script src="/_next/static/chunks/fd9d1056-bfe8cd6c9c7c7e45.js" defer></script>
                <script src="/_next/static/chunks/938-a9dc5eeaa9cbd612.js" defer></script>
                <script src="/_next/static/chunks/main-app-c5d0a9511a5ba1de.js" defer></script>
                <script src="/_next/static/chunks/app/page-5f60a265695a008d.js" defer></script>
              </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        
        # For all other paths, try standard Next.js file locations
        possible_paths = [
            # For root path
            frontend_path / ".next/server/app/index.html",  # Next.js 13+ app router
            frontend_path / ".next/server/pages/index.html", # Next.js pages router
            frontend_path / ".next/standalone/frontend/app/index.html",
            frontend_path / ".next/standalone/index.html",
            frontend_path / ".next/standalone/frontend/index.html",
            frontend_path / "out/index.html",
            frontend_path / ".next/static/index.html",
            frontend_path / ".next/index.html",
            frontend_path / "public/index.html",
            frontend_path / "index.html",
            frontend_path / ".next/standalone/frontend/out/index.html",
        ]
        
        for path in possible_paths:
            try:
                if path.exists():
                    print(f"Serving index.html from: {path}")
                    return FileResponse(str(path))
            except Exception as e:
                print(f"Error checking path {path}: {str(e)}")
                continue
        
        # If no index.html is found, send a basic HTML response
        html_content = f"""
        <!DOCTYPE html>
        <html>
          <head>
            <title>Tutor App</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
          </head>
          <body>
            <h1>Welcome to Tutor App</h1>
            <p>The application is running, but the frontend build was not found.</p>
            <p>Requested path: {full_path}</p>
          </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    
    # In development, return a 404 for non-API routes
    raise HTTPException(status_code=404, detail="Not Found")

# Add endpoint for sentence construction assessment
@app.post("/api/sentence/assess", response_model=SentenceAssessmentResponse)
async def assess_sentence_construction(request: SentenceAssessmentRequest):
    try:
        # Determine the text to analyze - prioritize transcript over audio
        recognized_text = None
        
        # First check if a transcript is provided - prioritize this
        if request.transcript and request.transcript.strip():
            print(f"Using provided transcript: '{request.transcript}'")
            recognized_text = request.transcript
        # If no transcript, try to transcribe audio if provided
        elif request.audio_base64:
            try:
                print("Attempting to transcribe audio...")
                recognized_text = await recognize_speech(request.audio_base64, request.language)
                print(f"Successfully transcribed audio: '{recognized_text}'")
            except Exception as audio_err:
                print(f"Error transcribing audio: {str(audio_err)}")
                # No need to fall back to transcript as we already checked it
        # Use context as last resort if provided
        elif request.context:
            print(f"Using context as fallback: '{request.context}'")
            recognized_text = request.context
        
        if not recognized_text or recognized_text.strip() == "":
            print("No valid text found for analysis")
            raise HTTPException(status_code=400, detail="No speech detected or text provided for analysis")
        
        print(f"Proceeding with analysis of: '{recognized_text}'")
        
        # Analyze sentence
        assessment = await analyze_sentence(
            text=recognized_text,
            language=request.language,
            level=request.level,
            exercise_type=request.exercise_type,
            target_grammar=request.target_grammar
        )
        
        # Combine the recognized text with the assessment results
        result = SentenceAssessmentResponse(
            recognized_text=recognized_text,
            **assessment
        )
        
        return result
    
    except Exception as e:
        print(f"Error in sentence assessment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sentence assessment failed: {str(e)}")


# Define a model for exercise requests
class ExerciseRequest(BaseModel):
    language: str
    level: str
    exercise_type: str
    target_grammar: Optional[List[str]] = None


# Add endpoint for generating practice exercises
@app.post("/api/sentence/exercises")
async def generate_sentence_exercises(request: ExerciseRequest):
    try:
        # Generate exercises
        exercises = await generate_exercises(
            language=request.language,
            level=request.level,
            exercise_type=request.exercise_type,
            target_grammar=request.target_grammar
        )
        
        return exercises
    
    except Exception as e:
        print(f"Error generating exercises: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Exercise generation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

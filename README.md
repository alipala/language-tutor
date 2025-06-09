# 🌍 Language Tutor Application

A modern, production-ready language learning platform for interactive voice-based learning, powered by FastAPI (backend), Next.js (frontend), and OpenAI models. Built for robust deployment on Railway, with a focus on real-time speaking, assessment, and personalized learning plans.

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-0.104.1-009688?style=for-the-badge&logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Next.js-14.0.4-000000?style=for-the-badge&logo=next.js" alt="Next.js"/>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/WebRTC-Real--time-4285F4?style=for-the-badge&logo=webrtc" alt="WebRTC"/>
  <img src="https://img.shields.io/badge/MongoDB-4.4-47A248?style=for-the-badge&logo=mongodb" alt="MongoDB"/>
  <img src="https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=for-the-badge&logo=openai" alt="OpenAI"/>
</p>

## 📚 Documentation

This repository contains comprehensive documentation to help you understand, use, and contribute to the Language Tutor application:

- [Frontend Architecture](./docs/FRONTEND.md) - Next.js application structure, components, and state management
- [Backend Architecture](./docs/BACKEND.md) - FastAPI server, endpoints, and database integration
- [Speech Recognition System](./docs/SPEECH_RECOGNITION.md) - WebRTC and OpenAI Realtime API integration
- [Authentication System](./docs/AUTHENTICATION.md) - User management, JWT tokens, and Google OAuth
- [Database Structure](./docs/DATABASE.md) - MongoDB collections and data models
- [Guest User Experience](./docs/GUEST_EXPERIENCE.md) - Limited functionality for non-authenticated users
- [Deployment Guide](./docs/DEPLOYMENT.md) - Railway deployment and environment configuration
- [Local Development](./docs/LOCAL_DEVELOPMENT.md) - Setting up your development environment

## ✨ Core Features

- 🎙️ **Real-time Conversation**: Voice-based interaction with AI tutor using WebRTC and OpenAI's Realtime API
- 🔊 **Pronunciation Assessment**: Detailed feedback with color-coded highlighting and improvement suggestions
- 📝 **Language Proficiency Analysis**: CEFR level determination and personalized recommendations
- 📋 **Custom Learning Plans**: AI-generated study plans based on assessment results and goals
- 🗣️ **Topic-based Practice**: Predefined topics or custom conversations with web search integration
- 🌍 **Multi-language Support**: Currently Dutch and English with all CEFR levels (A1-C2)
- 🔐 **Flexible Authentication**: Email/password, Google Sign-In, and guest user functionality
- 📱 **Responsive Design**: Modern UI optimized for both desktop and mobile devices
- 📊 **Comprehensive Data Export**: Export your complete learning journey in multiple formats
- 🚀 **Production-Ready**: Optimized for Railway deployment with robust error handling

### 📊 Data Export & Learning Analytics

Transform your learning journey into professional documents and comprehensive data packages:

#### 🎯 **Assessment & Learning Plans Export**
- **Professional PDF Reports**: Beautifully formatted documents showcasing your assessment results, skill breakdowns, and personalized learning plans
- **Detailed Analytics**: Comprehensive statistics including average scores, level distribution, and learning goal analysis
- **Progress Visualization**: Color-coded skill assessments with pronunciation, grammar, vocabulary, fluency, and coherence scores

#### 💬 **Conversation History & AI Analysis Export**
- **Complete Session Records**: Full transcripts of all your practice conversations with timestamps and metadata
- **Enhanced AI Insights**: Detailed analysis including conversation quality metrics, breakthrough moments, and areas for improvement
- **Multiple Formats**: Available in both PDF (professional reports) and CSV (data analysis) formats
- **Vocabulary Tracking**: Highlights of new vocabulary learned and usage patterns

#### 📦 **Complete Learning Data Package**
- **All-in-One ZIP Archive**: Comprehensive package containing all your learning data in multiple formats
- **Professional Documentation**: Ready-to-share course completion certificates and progress reports
- **Data Portability**: JSON format for advanced analysis and integration with other tools
- **Backup & Recovery**: Complete data export for personal backup and account migration

#### 🔒 **Privacy & Security**
- **Personal Data Only**: Exports contain only your individual learning information
- **Secure Generation**: All exports are generated on-demand and not stored on servers
- **GDPR Compliant**: Full data portability rights with comprehensive export functionality

**Access your export options through the Profile → Export Data tab for instant downloads of your learning achievements.**

- **API endpoints** for authentication, learning plan management, real-time conversation, speaking/sentence assessment, and web search.
- **Authentication** using JWT and Google OAuth, with secure password storage and token validation.
- **User management** and **learning plan assignment** for both guests and authenticated users.
- **Real-time and batch assessment** of speech and sentences using OpenAI models, with detailed feedback.
- **Database integration** with MongoDB for persistent storage of users, plans, and progress.
- **Centralized error handling** and robust logging for reliability.
- **Environment configuration** for secure and flexible deployment.
- **Comprehensive testing** for API reliability.

### Key Backend Modules

| File/Module               | Purpose                                                                 |
|---------------------------|-------------------------------------------------------------------------|
| `main.py`                 | FastAPI app, router registration, middleware, error handling            |
| `auth.py`, `auth_routes.py` | Auth logic, JWT, Google OAuth, endpoints for login/registration         |
| `learning_routes.py`      | Learning plan CRUD, goal management, plan assignment                    |
| `speaking_assessment.py`, `sentence_assessment.py` | AI-powered assessment endpoints and logic                  |
| `database.py`, `models.py`, `models/` | MongoDB connection and data models                               |
| `utils/`                  | Utilities for validation, error formatting, etc.                        |
| `test_api.py`, `tests/`   | Unit and integration tests                                              |

---

---

## 🤖 OpenAI Model Usage

| Model Name                                 | What For                              | When To Use / How To Use |
|--------------------------------------------|---------------------------------------|-------------------------|
| `gpt-4o-mini-realtime-preview-2024-12-17` | Real-time speaking (voice chat)       | Used for streaming, low-latency AI conversation during live speech sessions. Backend issues ephemeral tokens via `/api/realtime/token`. |
| `gpt-4o-mini`                             | Web search with OpenAI API            | Used when user requests a conversation on a custom topic; backend performs web search and uses this model to synthesize up-to-date responses. |
| `gpt-4o`                                  | Sentence & speaking assessment        | Used for detailed sentence analysis, grammar/vocab feedback, and scoring of user responses. Backend endpoints: `/api/assessment/speaking`. |
| `gpt-4o-mini-transcribe`                   | Transcription (speech-to-text)        | Used to transcribe user audio for assessment and feedback. Invoked internally by backend for audio inputs. |

- All OpenAI API calls require a valid `OPENAI_API_KEY` set in backend environment variables.
- Models are selected automatically by backend logic according to user action and endpoint.

---

## 🚶 User Flows

### 1. New User Onboarding
- Visit home page → Click "Get Started"
- Select language (Dutch/English)
- Select proficiency level (A1–C2)
- Choose a topic or enter a custom topic
- (Optional) Sign up with email/password or Google

### 2. Authenticated User Journey
- Log in (email/password or Google)
- Resume existing learning plan or create new one
- Access profile, progress, and assessment history

### 3. Learning Plan Creation/Assignment
- Select learning goals and duration
- System generates a personalized plan (optionally assigned to user account)
- Plan can be used immediately or after login (pending plan assignment logic)

### 4. Real-time Conversation & Assessment
- Start a voice conversation with AI tutor (WebRTC + OpenAI Realtime)
- Receive instant feedback, color-coded transcript, and pronunciation scores
- Option to review pronunciation and get detailed assessment

### 5. Pronunciation Review
- After speaking, review transcript with:
  - 🟢 Green: Correct
  - 🟡 Yellow: Minor issues
  - 🔴 Red: Major errors
- Get actionable feedback and suggestions

### 6. Web Search for Custom Topics
- Enter a custom topic (e.g., "Current events in Istanbul")
- Backend performs web search, synthesizes up-to-date info using OpenAI
- Tutor incorporates real-world facts into conversation

---

## 🛠️ Local Development

1. **Clone the repo**
- **Framer Motion**: Smooth animations and transitions for UI elements
- **React Context API**: Global authentication state management
- **Next.js API Routes**: Secure backend communication
- **Responsive Components**: Tailwind CSS for adaptive layouts

## Architecture

The application follows a modern architecture with a clear separation between frontend and backend:

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Next.js   │◄────►│   FastAPI   │◄────►│   OpenAI    │
│  Frontend   │      │   Backend   │      │     API     │
└─────────────┘      └─────────────┘      └─────────────┘
       ▲                     ▲
       │                     │
       └─────────┬───────────┘
                 │
         ┌───────▼──────┐
         │    WebRTC    │
         │ Communication │
         └───────────────┘
```

## Railway.app Deployment Guide

This application is configured for easy deployment on Railway.app with optimized settings for reliable production performance.

### Prerequisites

1. A Railway.app account
2. OpenAI API key for the voice conversation functionality

### Deployment Steps

1. **Fork or clone this repository to your GitHub account**

2. **Connect your Railway.app account to GitHub**
   - Log in to Railway.app
   - Go to your dashboard
   - Click "New Project" → "Deploy from GitHub repo"
   - Select this repository

3. **Configure Environment Variables**
   In your Railway.app project settings, add the following environment variables:

   **Required Variables:**
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `NODE_ENV`: Set to `production`

   **Optional Variables:**
   - `PORT`: The port for your backend (Railway sets this automatically)
   - `FRONTEND_URL`: URL of your frontend (if deployed separately)

4. **Deploy the Application**
   - Railway will automatically detect the configuration and deploy your application

### Railway-Specific Optimizations

This application includes several optimizations for reliable production deployment on Railway:

1. **Next.js Configuration:**
   - Uses `output: 'standalone'` instead of 'export' for proper server-side rendering
   - Sets `reactStrictMode: false` to prevent double rendering in production
   - Sets `trailingSlash: false` to prevent redirect loops

2. **Smart API URL Detection:**
   - Automatically detects whether the application is running in development or production
   - Uses `window.location.origin` in production to ensure frontend connects to the correct backend URL
   - Falls back to environment variables or localhost during development
   - Eliminates the need for manual API URL configuration in different environments
   - Implemented through a centralized `getApiUrl()` function for consistent behavior

3. **Optimized Deployment Configuration:**
   - Enhanced Dockerfile with proper working directory settings
   - Improved railway.toml and nixpacks.toml configurations
   - Updated Procfile to avoid using `cd` commands for better compatibility
   - CORS configuration that allows all origins (`origins=["*"]`) in production for maximum compatibility

4. **Custom UI Components:**
   - Replaced external UI dependencies with custom implementations
   - Reduced dependency on third-party libraries for better build reliability
   - Implemented custom Progress component without external dependencies

4. **Navigation System:**
   - Uses direct `window.location.replace()` for reliable page transitions in production
   - Implements stuck-state detection and automatic recovery
   - Provides fallback navigation through multiple methods
   - Enhanced error handling and user feedback during transitions
   - Session storage flags to track navigation state and prevent unwanted redirects
   - Comprehensive logging for debugging navigation issues
   - Fallback timers to detect and recover from navigation failures

3. **Backend Routing:**
   - Smart path detection and normalization
   - Custom HTML generation for client-side routes
   - Improved static file handling for Next.js assets
   - Comprehensive logging for production debugging
   - The deployment process will:
     - Install Python dependencies for the backend
     - Install Node.js dependencies and build the Next.js frontend
     - Start the FastAPI server

5. **Access Your Application**
   - Once deployed, Railway will provide a URL to access your application
   - You can also configure a custom domain in Railway settings

### Local Development

To run the application locally:

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/tutor.git
   cd tutor
   ```

2. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env  # Then edit .env to add your OpenAI API key
   ```

3. Set up the frontend:
   ```bash
   cd frontend
   npm install
   cp .env.example .env.local  # Then edit as needed
   ```

4. Start the backend server:
   ```bash
   # In the backend directory with venv activated
   python -m backend.run
   ```

5. Start the frontend development server:
   ```bash
   # In the frontend directory
   npm run dev
   ```

6. Access the application at http://localhost:3000

## Project Structure

```
├── backend/                # FastAPI backend
│   ├── main.py            # Main FastAPI application
│   ├── run.py             # Entry point for running the server
│   ├── requirements.txt   # Python dependencies
│   └── test_api.py        # API tests
├── frontend/              # Next.js frontend
│   ├── components/        # React components
│   ├── lib/               # Utility functions and services
│   ├── pages/             # Next.js pages
│   ├── public/            # Static assets
│   └── styles/            # CSS styles
├── Dockerfile             # Docker configuration
├── railway.json           # Railway deployment configuration
└── README.md             # Project documentation
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check endpoint |
| `/api/test` | GET | Test connection endpoint |
| `/api/realtime/token` | POST | Generate ephemeral key for OpenAI Realtime API |
| `/api/mock-token` | POST | Mock token for testing |
| `/api/assessment/speaking/prompts` | GET | Get speaking assessment prompts |
| `/api/speaking-prompts` | GET | Alternative endpoint for speaking prompts |
| `/api/export/learning-plans` | GET | Export learning plans and assessments (PDF/CSV/JSON) |
| `/api/export/conversations` | GET | Export conversation history and AI analysis (PDF/CSV/JSON) |
| `/api/export/data` | GET | Export complete learning data package (ZIP/JSON) |

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

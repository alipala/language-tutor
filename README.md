# 🌍 Language Tutor Application

A modern, production-ready language learning platform for interactive voice-based learning, powered by FastAPI (backend), Next.js (frontend), and OpenAI models. Built for robust deployment on Railway, with a focus on real-time speaking, assessment, and personalized learning plans.

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-0.104.1-009688?style=for-the-badge&logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Next.js-14.0.4-000000?style=for-the-badge&logo=next.js" alt="Next.js"/>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/WebRTC-Real--time-4285F4?style=for-the-badge&logo=webrtc" alt="WebRTC"/>
</p>

---

## ✨ Core Features
- 🎙️ Voice conversation with AI tutor (real-time, streaming)
- 🔊 Pronunciation assessment with color-coded feedback and review
- 📝 Sentence and speaking assessment with actionable feedback
- 📋 Custom learning plan creation and management
- 🗣️ Topic selection (built-in and custom, with web search)
- 🌍 Support for multiple languages and CEFR levels
- 🔐 Modern authentication (email/password & Google Sign-In)
- 📱 Responsive, animated UI for mobile and desktop
- 🚀 Optimized for Railway deployment

---

## 🗣️ Supported Languages & Levels
- **Dutch**: All CEFR levels (A1, A2, B1, B2, C1, C2)
- **English**: All CEFR levels (A1, A2, B1, B2, C1, C2)

The application follows the Common European Framework of Reference for Languages (CEFR) for proficiency tracking and personalized content.

---

## 🧠 Pronunciation & Learning
- **Real-time pronunciation assessment**: Color-coded feedback (🟢 correct, 🟡 minor issue, 🔴 error)
- **Interactive review modal**: Review your pronunciation and get actionable feedback after each speaking turn
- **Sentence assessment**: Receive grammar, vocabulary, and structure suggestions tailored to your level
- **Progress tracking**: Monitor your advancement through custom learning plans

---

## 📋 Custom Learning Plans
- Create a personalized learning plan by selecting language, level, goals, and duration
- Flexible goal selection: Choose from built-in categories or add your own custom goals
- Set your preferred timeline (1–12 months)
- Plans can be used without authentication or assigned to your account after login
- Progress is tracked and plans can be resumed at any time

---

## 🗂️ Topic Selection
- Choose from a variety of built-in conversation topics (e.g., Travel, Work, Culture, Current Events)
- Enter a custom topic for up-to-date, web-searched conversations
- Web search integration: For custom topics, the backend fetches current information and the AI tutor incorporates it into the conversation
- Skip topic selection for free-form practice

---

## 📦 Technical Implementation

- **Frontend**: Next.js 14, custom React components, modern animated UI, dark theme, responsive for mobile/desktop
- **Backend**: FastAPI (Python), REST API endpoints for authentication, learning plans, speaking assessments, real-time conversation, and web search
- **Real-time Voice**: WebRTC for low-latency audio streaming; OpenAI Realtime API for conversational AI
- **Authentication**: Email/password and Google Sign-In (Google Identity Services SDK)
- **State Management**: Context-based, with session storage for navigation and recovery
- **Navigation**: Direct `window.location` navigation for reliability in production (esp. Railway)
- **Error Handling**: Centralized error service, robust logging, stuck-state detection and recovery
- **API URL Config**: Environment-aware, supports both local and Railway deployment
- **Deployment**: Optimized for Railway (standalone output, CORS, custom domain support)
- **Database**: MongoDB (Railway-managed), user/account/plan storage

---

## 🛠️ Backend Deep Dive

The backend, built with FastAPI, is responsible for:

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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

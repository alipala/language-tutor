# 🌍 Language Tutor Application

> Forked from the original [Tutor Application](https://github.com/yourusername/tutor) on March 14, 2025.

A cutting-edge language learning voice conversation application with a sleek, modern UI that enables interactive voice-based learning. The application combines FastAPI's backend performance with Next.js's frontend capabilities and WebRTC for seamless real-time communication. Designed specifically for language learning with robust production deployment on Railway.

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-0.104.1-009688?style=for-the-badge&logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Next.js-14.0.4-000000?style=for-the-badge&logo=next.js" alt="Next.js"/>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/WebRTC-Real--time-4285F4?style=for-the-badge&logo=webrtc" alt="WebRTC"/>
</p>

## ✨ Features

### Core Features
- 🎙️ Language learning voice conversation with OpenAI integration
- 🌍 Support for multiple languages (currently Dutch and English)
- 🎓 Six proficiency levels (A1, A2, B1, B2, C1, C2) following CEFR standards
- 🗣️ Topic selection for focused conversation practice
- 📝 Advanced sentence assessment with grammar and vocabulary feedback
- 🔍 Web search functionality for custom topics with real-time information

### Pronunciation & Learning
- 🔊 Real-time pronunciation assessment with color-coded feedback
- 📊 Visual confidence indicators for pronunciation quality
- 🎯 Interactive pronunciation review modal with detailed feedback
- 📝 Scrollable real-time transcript with custom styling
- 🔄 "Continue Learning" functionality to seamlessly resume conversations

### Technical Features
- 🌐 WebRTC for real-time communication
- 🚀 FastAPI backend for high performance
- 🎨 Modern dark gradient UI with animations
- 📱 Responsive design for mobile and desktop
- 🔄 Seamless frontend-backend integration
- 🔐 Modern authentication system with animated UI components
- ⚡ Robust navigation with automatic recovery from stuck states
- 🔍 Advanced debugging with comprehensive logging system
- 🛡️ Enhanced error handling and user feedback
- 🌊 Optimized for reliable production deployment on Railway

## 🔍 About This Fork

This Language Tutor Application is a specialized fork of the original Tutor Application, focused on language learning capabilities. The core architecture and functionality remain the same, with enhancements specifically for language learning features and an improved user experience.

## 🎓 Language Learning Features

### 🌐 Supported Languages
- **Dutch**: Complete support with all proficiency levels
- **English**: Complete support with all proficiency levels

### 📊 Proficiency Levels
The application follows the Common European Framework of Reference for Languages (CEFR) with six levels:

| Level | Name | Description |
|-------|------|-------------|
| **A1** | Beginner | Can understand and use familiar everyday expressions and very basic phrases |
| **A2** | Elementary | Can communicate in simple and routine tasks on familiar topics |
| **B1** | Intermediate | Can deal with most situations likely to arise while traveling |
| **B2** | Upper Intermediate | Can interact with a degree of fluency and spontaneity |
| **C1** | Advanced | Can express ideas fluently and spontaneously without much searching for expressions |
| **C2** | Proficiency | Can express with precision in complex situations |

### 🗣️ Topic Selection
The application offers a variety of conversation topics to focus your language practice:

- **Travel** ✈️: Discuss travel destinations, experiences, and planning trips
- **Food & Cooking** 🍲: Talk about cuisines, recipes, restaurants, and cooking techniques
- **Hobbies & Interests** 🎨: Share your favorite activities, sports, games, or pastimes
- **Culture & Traditions** 🏛️: Explore cultural aspects, traditions, festivals, and customs
- **Movies & TV Shows** 🎬: Discuss films, series, actors, directors, and entertainment
- **Music** 🎵: Talk about music genres, artists, concerts, and preferences
- **Technology** 💻: Discuss gadgets, apps, innovations, and digital trends
- **Environment & Nature** 🌳: Explore environmental issues, sustainability, and the natural world
- **Custom Topic** 🔍: Enter any topic of your interest and the tutor will use web search to provide up-to-date information

You can also choose to skip topic selection for a free-form conversation.

### Conversation Flow
1. Select your target language (Dutch or English)
2. Choose a conversation topic or enter a custom topic with the web search feature
3. Select your proficiency level (A1-C2)
4. Start a voice conversation with the language tutor
5. Practice speaking and receive feedback appropriate to your level

### 🔊 Pronunciation Assessment
The application provides real-time pronunciation assessment with color-coded feedback:

- **🟢 Green**: Correctly pronounced words
- **🟡 Yellow**: Minor pronunciation issues
- **🔴 Red**: Significant pronunciation errors

Users can review their pronunciation after speaking to get detailed feedback on their language skills.

#### New Pronunciation Features
- **Interactive Review Modal**: Review your pronunciation with a dedicated modal interface
- **Visual Feedback**: Animated microphone states show recording status clearly
- **Seamless Learning Flow**: Continue your conversation after reviewing pronunciation
- **Real-time Scrolling Transcript**: Never lose track of your conversation with auto-scrolling transcript

### 📝 Sentence Assessment
The application features a powerful sentence assessment system that provides detailed feedback on your language production:

#### Key Features
- **Grammar Analysis**: Identifies grammatical errors and suggests corrections
- **Vocabulary Evaluation**: Assesses word choice and suggests more appropriate alternatives
- **Sentence Structure Feedback**: Analyzes sentence construction and provides improvement tips
- **Level-Appropriate Feedback**: Tailors assessment to your selected proficiency level
- **Context-Aware Evaluation**: Considers the conversation context when assessing your sentences

#### Technical Implementation
- **Smart API Integration**: Dynamically connects to the correct backend API regardless of environment
- **Environment-Aware Configuration**: Automatically detects development vs. production environments
- **Robust Error Handling**: Gracefully manages connection issues and provides helpful error messages
- **Efficient Data Processing**: Optimized for quick assessment response times

#### How It Works
1. **Speech Recognition**: Your spoken language is transcribed to text
2. **Assessment Request**: The transcribed text is sent to the backend API for analysis
3. **AI Processing**: Advanced language models evaluate your sentence based on grammar, vocabulary, and context
4. **Feedback Generation**: Detailed, actionable feedback is generated and returned to the frontend
5. **Visual Presentation**: Results are displayed with color-coding and specific improvement suggestions

### 🔍 Web Search for Custom Topics

The Language Tutor now features an integrated web search capability that allows tutors to access real-time information about any topic you choose.

#### How to Use Web Search

1. **Select a Custom Topic**:
   - On the topic selection page, choose "Custom Topic" or enter your own topic in the input field
   - Type a specific query, question, or topic you'd like to discuss (e.g., "Latest developments in quantum computing" or "Current situation in Istanbul politics")

2. **Benefit from Real-time Information**:
   - The tutor will use web search to gather the latest information about your topic
   - All responses will incorporate up-to-date facts and details relevant to your chosen topic
   - The tutor will start the conversation by explicitly mentioning your chosen topic

3. **Learn with Current Context**:
   - Practice language skills while discussing current events, recent developments, or specialized topics
   - Receive vocabulary and expressions that are contextually relevant to your topic of interest
   - Engage in more meaningful conversations with accurate and timely information

#### Example Use Cases

- **Current Events**: "Recent elections in France" or "Latest climate change agreements"
- **Technology**: "New features in iOS 19" or "Advancements in electric vehicles"
- **Culture**: "Traditional festivals in Japan this month" or "Recent art exhibitions in Paris"
- **Sports**: "Results from yesterday's football matches" or "Upcoming Olympic events"
- **Science**: "Recent discoveries about black holes" or "Latest COVID-19 research"

#### Technical Details

- The web search feature uses OpenAI's browsing capabilities to retrieve current information
- Search results are processed and integrated into the tutor's knowledge base
- The tutor is instructed to incorporate this information naturally into the conversation
- The system can handle topics up to 100 characters in length for detailed queries

## 🔐 Authentication System

The Language Tutor features a modern, secure authentication system with an enhanced user experience:

### Features
- **Modern UI**: Sleek, animated forms with gradient text and interactive elements
- **Responsive Design**: Optimized for both mobile and desktop devices
- **Animated Backgrounds**: Subtle animated gradient backgrounds enhance visual appeal
- **Secure Authentication**: JWT-based authentication with proper token handling
- **Google Authentication**: Seamless login/signup with Google accounts using OAuth 2.0
- **Error Handling**: Clear error messages and loading states for better user feedback
- **Form Validation**: Client-side validation for immediate user feedback
- **Remember Me**: Option to stay logged in across sessions
- **Password Recovery**: Password reset functionality with email verification

### Google Authentication
The application supports Google OAuth 2.0 integration, allowing users to sign in with their Google accounts:

#### Features
- **One-Click Login**: Sign in with a single click using your Google account
- **Automatic Account Creation**: New users are automatically registered on first login
- **Secure Token Verification**: Backend verification of Google ID tokens
- **Seamless Integration**: Consistent user experience with standard authentication
- **Cross-Device Support**: Works across all devices and browsers

#### Technical Implementation
- **Google Identity Services SDK**: Uses the latest Google Sign-In API
- **JWT Token Exchange**: Converts Google tokens to application JWT tokens
- **Environment-Aware Configuration**: Automatically adapts to development and production environments
- **Robust Error Handling**: Graceful handling of authentication failures
- **Session Management**: Proper session creation and token storage

### Technical Implementation
- **JWT Authentication**: Secure token-based authentication system
- **MongoDB Integration**: User data stored securely in MongoDB
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

4. **Navigation System:**
   - Uses direct `window.location.href` for reliable page transitions in production
   - Implements stuck-state detection and automatic recovery
   - Provides fallback navigation through multiple methods
   - Enhanced error handling and user feedback during transitions

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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

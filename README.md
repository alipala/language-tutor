# Language Tutor Application

> Forked from the original [Tutor Application](https://github.com/yourusername/tutor) on March 14, 2025.

A language learning voice conversation application with a modern UI that allows users to interact through voice. The application uses FastAPI for the backend and Next.js for the frontend, with WebRTC for real-time communication. This project is specialized for language learning and practice with robust production deployment on Railway.

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-0.104.1-009688?style=for-the-badge&logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Next.js-14.0.4-000000?style=for-the-badge&logo=next.js" alt="Next.js"/>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/WebRTC-Real--time-4285F4?style=for-the-badge&logo=webrtc" alt="WebRTC"/>
</p>

## Features

- 🎙️ Language learning voice conversation with OpenAI integration
- 🌍 Support for multiple languages (currently Dutch and English)
- 🎓 Six proficiency levels (A1, A2, B1, B2, C1, C2) following CEFR standards
- 🌐 WebRTC for real-time communication
- 🚀 FastAPI backend for high performance
- 🎨 Modern dark gradient UI
- 📱 Responsive design for mobile and desktop
- 🔄 Seamless frontend-backend integration
- ⚡ Robust navigation with automatic recovery from stuck states
- 🔍 Advanced debugging with comprehensive logging system
- 🛡️ Enhanced error handling and user feedback
- 🌊 Optimized for reliable production deployment on Railway

## About This Fork

This Language Tutor Application is a specialized fork of the original Tutor Application, focused on language learning capabilities. The core architecture and functionality remain the same, with enhancements specifically for language learning features.

## Language Learning Features

### Supported Languages
- **Dutch**: Complete support with all proficiency levels
- **English**: Complete support with all proficiency levels

### Proficiency Levels
The application follows the Common European Framework of Reference for Languages (CEFR) with six levels:

- **A1 (Beginner)**: Can understand and use familiar everyday expressions and very basic phrases
- **A2 (Elementary)**: Can communicate in simple and routine tasks on familiar topics
- **B1 (Intermediate)**: Can deal with most situations likely to arise while traveling
- **B2 (Upper Intermediate)**: Can interact with a degree of fluency and spontaneity
- **C1 (Advanced)**: Can express ideas fluently and spontaneously without much searching for expressions
- **C2 (Proficiency)**: Can express with precision in complex situations

### Conversation Flow
1. Select your target language (Dutch or English)
2. Choose your proficiency level (A1-C2)
3. Start a voice conversation with the language tutor
4. Practice speaking and receive feedback appropriate to your level

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

2. **Navigation System:**
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

# Language Tutor Application Integration Summary

## Overview
This document provides a comprehensive overview of the Language Tutor application ecosystem, including the main application, backend API, and admin panel.

---

## 🚀 Application Components

### 1. **Main Frontend Application** (Next.js)
- **Location**: `/Users/alipala/CascadeProjects/language-tutor/frontend`
- **Technology**: Next.js 14.0.4, React 18.2.0, TypeScript
- **Port**: 3000 (development)

#### Run Commands:
```bash
cd frontend
npm run dev          # Start development server
npm run build        # Build for production
npm start            # Start production server
npm run lint         # Run linter
```

#### Key Features:
- Language learning interface
- Real-time voice conversation with AI tutor
- Speaking assessments
- Learning plan management
- User authentication and profiles
- Subscription management (Stripe integration)

---

### 2. **Backend API** (FastAPI)
- **Location**: `/Users/alipala/CascadeProjects/language-tutor/backend`
- **Technology**: FastAPI, Python 3.11, MongoDB
- **Port**: 8000 (default)

#### Run Commands:
```bash
cd backend
python run_with_venv.py    # Start backend with virtual environment
# OR
source venv/bin/activate   # Activate virtual environment first
python run.py              # Then run the application
```

#### Key API Endpoints:
- `/api/health` - Health check
- `/api/realtime/token` - OpenAI Realtime API token generation
- `/api/speaking/assess` - Speaking assessment
- `/api/sentence/assess` - Sentence construction assessment
- `/auth/*` - Authentication endpoints
- `/api/admin/*` - Admin panel endpoints
- `/api/learning/*` - Learning plan management
- `/api/stripe/*` - Payment processing

#### Database:
- **MongoDB** - User data, conversations, learning plans, assessments
- Connection configured via environment variables

---

### 3. **Admin Panel** (React Admin)
- **Location**: `/Users/alipala/Documents/Cline/MCP/language-tutor-admin`
- **Technology**: React Admin 5.8, Material-UI 7.0, TypeScript, Vite
- **Port**: 5173 (development)

#### Run Commands:
```bash
cd ../language-tutor-admin
npm run dev          # Start development server (Vite)
npm run build        # Build for production
npm start            # Preview production build
npm run serve        # Alternative preview command
```

#### Admin Panel Features:
- **Dashboard**: Key metrics and system overview
- **User Management**: View, edit, create, and manage users
- **Conversations**: Monitor conversation sessions
- **User Statistics**: Analytics and usage data
- **Badge System**: Gamification management
- **Assessment History**: Track user assessments
- **Learning Plans**: Oversee learning plan progress
- **Notification Center**: Send and manage notifications
- **Promotions**: Create and manage promotional campaigns

#### Admin Resources:
1. **Users** (`/users`)
   - List, show, edit, create operations
   - User profile management
   - Subscription status

2. **Conversation Sessions** (`/conversation_sessions`)
   - View conversation history
   - Monitor session details

3. **User Statistics** (`/user_stats`)
   - Usage analytics
   - Performance metrics

4. **Badges** (`/badges`)
   - Badge system management
   - Achievement tracking

5. **Assessment History** (`/assessment_history`)
   - Speaking assessment records
   - Progress tracking

6. **Learning Plans** (`/learning_plans`)
   - Plan management
   - Progress monitoring

7. **Notifications** (`/notifications`)
   - Create and send notifications
   - Notification history

8. **Promotions** (`/promotions`)
   - Create promotional campaigns
   - Manage active promotions

---

## 🔗 Integration Points

### Frontend ↔ Backend
- **API Base URL**: `https://mytacoai.com` (production) or `http://localhost:8000` (development)
- **Authentication**: JWT tokens stored in localStorage
- **Real-time Communication**: OpenAI Realtime API for voice conversations
- **WebSocket**: Session heartbeat monitoring

### Admin Panel ↔ Backend
- **API Base URL**: Configured via `VITE_API_URL` environment variable
- **Default**: `https://mytacoai.com`
- **Authentication**: JWT tokens via `/api/admin/login`
- **Data Provider**: React Admin data provider with Axios
- **Required Backend Endpoints**:
  - `POST /api/admin/login` - Admin authentication
  - `GET /api/admin/health` - Health check
  - `GET /api/admin/users` - User management
  - `GET /api/admin/dashboard` - Dashboard metrics
  - All resource endpoints for CRUD operations

---

## 🔧 Environment Configuration

### Frontend (.env)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

### Backend (.env)
```env
MONGODB_URL=mongodb://...
OPENAI_API_KEY=sk-...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
```

### Admin Panel (.env)
```env
VITE_API_URL=http://localhost:8000
```

---

## 📦 Dependencies

### Frontend
- Next.js 14.0.4
- React 18.2.0
- Stripe.js 7.4.0
- Axios 1.11.0
- Chart.js 4.5.0
- Framer Motion 12.6.2

### Backend
- FastAPI
- OpenAI Python SDK
- Motor (async MongoDB driver)
- Stripe Python SDK
- Pydantic for validation

### Admin Panel
- React Admin 5.8.0
- Material-UI 7.0.1
- React 18.3.1
- Axios 1.10.0
- Vite 6.2.6

---

## 🚦 Quick Start Guide

### 1. Start Backend
```bash
cd /Users/alipala/CascadeProjects/language-tutor/backend
python run_with_venv.py
```
Backend will be available at `http://localhost:8000`

### 2. Start Frontend
```bash
cd /Users/alipala/CascadeProjects/language-tutor/frontend
npm run dev
```
Frontend will be available at `http://localhost:3000`

### 3. Start Admin Panel
```bash
cd /Users/alipala/Documents/Cline/MCP/language-tutor-admin
npm run dev
```
Admin panel will be available at `http://localhost:5173`

---

## 🔐 Authentication Flow

### User Authentication (Frontend)
1. User signs up/logs in via `/auth/login` or `/auth/signup`
2. Backend validates credentials and returns JWT token
3. Token stored in localStorage
4. Token included in Authorization header for all API requests
5. Automatic token refresh on expiration

### Admin Authentication (Admin Panel)
1. Admin logs in via admin panel login page
2. Credentials sent to `/api/admin/login`
3. Backend validates admin credentials
4. JWT token returned and stored in localStorage
5. Token included in all subsequent admin API requests
6. Automatic logout on token expiration

---

## 📊 Key Features Integration

### Real-time Voice Conversations
- **Frontend**: WebRTC audio capture
- **Backend**: OpenAI Realtime API token generation
- **Flow**: Frontend → Backend (token) → OpenAI Realtime API → Voice conversation

### Speaking Assessments
- **Frontend**: Audio recording and submission
- **Backend**: Whisper transcription + GPT-4 analysis
- **Admin Panel**: View assessment history and results

### Learning Plans
- **Frontend**: Display and track progress
- **Backend**: Generate personalized plans based on assessments
- **Admin Panel**: Monitor all user learning plans

### Subscription Management
- **Frontend**: Stripe checkout integration
- **Backend**: Webhook handling and subscription tracking
- **Admin Panel**: View user subscription status

---

## 🛠️ Development Workflow

### Making Changes to Frontend
1. Edit files in `frontend/` directory
2. Changes hot-reload automatically in development
3. Test changes at `http://localhost:3000`
4. Build for production: `npm run build`

### Making Changes to Backend
1. Edit files in `backend/` directory
2. Restart backend server to see changes
3. Test API endpoints at `http://localhost:8000/docs` (FastAPI auto-docs)
4. Run tests: `python run_tests.py`

### Making Changes to Admin Panel
1. Edit files in `language-tutor-admin/src/` directory
2. Changes hot-reload automatically (Vite HMR)
3. Test at `http://localhost:5173`
4. Build for production: `npm run build`

---

## 🐛 Troubleshooting

### Backend Won't Start
- Check MongoDB connection string in `.env`
- Verify OpenAI API key is set
- Ensure virtual environment is activated
- Check port 8000 is not in use

### Frontend Won't Start
- Run `npm install` to ensure dependencies are installed
- Check `NEXT_PUBLIC_API_URL` in `.env`
- Verify port 3000 is available
- Clear `.next` cache: `rm -rf .next`

### Admin Panel Won't Start
- Run `npm install` to ensure dependencies are installed
- Check `VITE_API_URL` in `.env`
- Verify backend is running
- Clear Vite cache: `rm -rf node_modules/.vite`

### Admin Panel Can't Connect to Backend
- Verify backend is running at the configured URL
- Check CORS settings in backend `main.py`
- Ensure admin endpoints are implemented in backend
- Check browser console for CORS errors

---

## 📝 Notes

### Admin Panel Architecture
- **Clean Architecture**: Separation of concerns with services, providers, and components
- **Type Safety**: Full TypeScript implementation
- **Modular Resources**: Each resource (users, conversations, etc.) is self-contained
- **React Admin**: Leverages React Admin's powerful data provider pattern

### Backend Architecture
- **FastAPI**: Modern, fast Python web framework
- **Async/Await**: Asynchronous MongoDB operations
- **Modular Routes**: Separate route files for different features
- **Middleware**: CORS, monitoring, error handling

### Frontend Architecture
- **Next.js App Router**: Modern routing with server components
- **Component-Based**: Reusable React components
- **State Management**: React hooks and context
- **Real-time Features**: WebSocket and WebRTC integration

---

## 🎯 Current Status

✅ **Backend**: Fully operational with comprehensive API endpoints
✅ **Frontend**: Production-ready with all core features
✅ **Admin Panel**: Fully functional with 8 resource types
✅ **Integration**: All three components properly connected
✅ **Authentication**: JWT-based auth working for both user and admin
✅ **Database**: MongoDB properly configured and connected

---

## 📚 Additional Resources

- **Backend API Docs**: `http://localhost:8000/docs` (when running)
- **Frontend**: Next.js documentation at https://nextjs.org/docs
- **Admin Panel**: React Admin docs at https://marmelab.com/react-admin/
- **Backend**: FastAPI docs at https://fastapi.tiangolo.com/

---

**Last Updated**: January 10, 2025
**Version**: 3.1.1

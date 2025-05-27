# Frontend Architecture

## Overview

The Language Tutor frontend is built with Next.js 14, using the App Router pattern for modern, efficient page routing and server components. The application features a component-based architecture with a focus on reusability, maintainability, and performance.

## Directory Structure

```
frontend/
├── app/                  # Next.js App Router pages and layouts
│   ├── api/              # API routes for client-side API calls
│   ├── assessment/       # Speaking assessment pages
│   ├── auth/             # Authentication pages (login, signup)
│   ├── language-selection/ # Language selection page
│   ├── level-selection/  # Level selection page
│   ├── profile/          # User profile page
│   ├── speech/           # Conversation interface
│   ├── topic-selection/  # Topic selection page
│   ├── globals.css       # Global styles
│   ├── layout.tsx        # Root layout component
│   └── page.tsx          # Home page component
├── components/           # Reusable React components
│   ├── assessment-card.tsx      # Assessment result card
│   ├── auth-form.tsx            # Authentication form
│   ├── google-auth-button.tsx   # Google Sign-In button
│   ├── learning-plan-modal.tsx  # Learning plan creation modal
│   ├── nav-bar.tsx              # Navigation bar
│   ├── pronunciation-assessment.tsx # Pronunciation assessment component
│   ├── sentence-construction-assessment.tsx # Sentence assessment component
│   ├── speaking-assessment.tsx  # Speaking assessment component
│   ├── time-up-modal.tsx        # Time expiration modal for guest users
│   └── ui/                      # UI components (buttons, inputs, etc.)
├── lib/                  # Utility functions and services
│   ├── api/              # API client functions
│   ├── api-utils.ts      # API URL configuration
│   ├── auth-utils.ts     # Authentication utilities
│   ├── auth.tsx          # Authentication context provider
│   ├── guest-utils.ts    # Guest user utilities
│   ├── healthCheck.ts    # Backend health check
│   ├── navigation/       # Navigation services
│   ├── realtimeService.ts # WebRTC and OpenAI Realtime API service
│   ├── speaking-assessment-api.ts # Speaking assessment API client
│   ├── types.ts          # TypeScript type definitions
│   └── useRealtime.ts    # Real-time communication hook
├── public/               # Static assets
└── styles/               # CSS styles
```

## Key Components

### Speaking Assessment

The `speaking-assessment.tsx` component (42KB) is a core feature that handles:

- Audio recording using the MediaRecorder API
- Processing and sending recordings to the backend
- Displaying assessment results with detailed feedback
- Time-limited assessments (15s for guests, 60s for authenticated users)

```typescript
// Example of recording functionality
const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorderRef.current = mediaRecorder;
    audioChunksRef.current = [];
    
    // Set up event handlers
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunksRef.current.push(event.data);
      }
    };
    
    // Start recording
    mediaRecorder.start();
    setStatus('recording');
    setIsTimerActive(true);
  } catch (error) {
    setError('Could not access your microphone. Please check your browser permissions.');
  }
};
```

### Speech Client

The `speech-client.tsx` component (63KB) manages the conversation interface:

- Real-time communication with the AI tutor
- WebRTC audio streaming
- Message display and history
- Time limits for conversations (1 minute for guests, 5 minutes for authenticated users)

### Authentication Components

- `auth-form.tsx`: Handles login and registration forms
- `google-auth-button.tsx`: Implements Google Sign-In
- `auth.tsx`: Provides authentication context to the application

## State Management

The application uses a combination of state management approaches:

1. **React Context**: For global state like authentication and error handling
2. **Local Component State**: For component-specific state using `useState` and `useReducer`
3. **Session Storage**: For persisting state across page navigation, especially for guest users
4. **Custom Hooks**: For encapsulating complex logic like real-time communication

Example of the authentication context:

```typescript
// From auth.tsx
export const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  login: async () => false,
  logout: async () => {},
  register: async () => false,
  googleLogin: async () => false,
});

export const useAuth = () => useContext(AuthContext);
```

## Navigation System

The application implements a robust navigation system that handles:

- Client-side routing with Next.js router
- Fallback navigation with `window.location` for reliability in production
- Session storage flags to track navigation state
- Stuck-state detection and automatic recovery

```typescript
// Example of reliable navigation
const navigateToPage = (path) => {
  try {
    router.push(path);
    
    // Fallback navigation after timeout
    setTimeout(() => {
      if (window.location.pathname !== path) {
        console.log('Router navigation failed, using direct navigation');
        window.location.href = path;
      }
    }, 1000);
  } catch (error) {
    // Direct navigation as ultimate fallback
    window.location.href = path;
  }
};
```

## API Communication

The frontend communicates with the backend through a set of API client functions:

- `api-utils.ts`: Determines the correct API URL based on the environment
- Service-specific API clients (e.g., `speaking-assessment-api.ts`)
- `healthCheck.ts`: Verifies backend connectivity with retry logic

```typescript
// From api-utils.ts
export function getApiUrl(): string {
  // Check if we're in a browser
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    // If we're on Railway, use empty string (same domain)
    if (hostname.includes('railway.app')) {
      return '';
    }
    // If we're not on localhost, use the same origin for API calls
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      return window.location.origin;
    }
  }
  // Default to environment variable or localhost
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}
```

## Real-time Communication

The application uses WebRTC and the OpenAI Realtime API for voice conversations:

- `realtimeService.ts`: Manages WebRTC connection and data channel
- `useRealtime.ts`: React hook for using the real-time service

This enables bi-directional audio streaming with the AI tutor, providing a natural conversation experience.

## Guest User Experience

The frontend implements a limited experience for guest users:

- Time-limited assessments (15 seconds vs. 60 seconds for authenticated users)
- Time-limited conversations (1 minute vs. 5 minutes for authenticated users)
- Session storage for persisting guest preferences
- Clear upgrade messaging at key moments

```typescript
// From guest-utils.ts
export function getAssessmentDuration(): number {
  return isAuthenticated() ? 60 : 15; // 60s for authenticated users, 15s for guests
}

export function getConversationDuration(): number {
  return isAuthenticated() ? 300 : 60; // 5 minutes for authenticated users, 1 minute for guests
}
```

## Responsive Design

The application uses Tailwind CSS for responsive design, ensuring a good user experience on both desktop and mobile devices. The UI adapts to different screen sizes with:

- Flexible layouts using Flexbox and Grid
- Mobile-first approach with responsive breakpoints
- Custom components optimized for touch interaction on mobile

## Error Handling

The application implements comprehensive error handling:

- Try/catch blocks for API calls and critical operations
- Fallback UI states for error conditions
- User-friendly error messages
- Detailed console logging for debugging

## Build and Optimization

The Next.js application is configured for optimal production deployment:

- `output: 'standalone'` for proper server-side rendering
- `reactStrictMode: false` to prevent double rendering in production
- `trailingSlash: false` to prevent redirect loops
- Custom Tailwind configuration for optimized CSS

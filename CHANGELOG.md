# Changelog

All notable changes to the Language Tutor Application will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.7.0] - 2025-03-19

### Added
- Interactive pronunciation review modal with exit button and escape key support
- Gray-out effect with backdrop blur during microphone initialization
- Scrollable real-time transcript with custom scrollbar styling
- Microphone button animations and visual feedback during recording
- "Continue Learning" button functionality to seamlessly resume conversations
- Audio wave animations for better visual feedback during recording

### Changed
- Enhanced user experience with improved visual feedback during state transitions
- Optimized component rendering for smoother animations
- Improved accessibility with clearer visual indicators for microphone states
- Added consistent styling across modals and interactive elements

### Fixed
- Resolved scrolling issues in the real-time transcript window
- Fixed microphone initialization feedback to provide clearer user guidance
- Corrected "Continue Learning" functionality to properly resume conversations
- Improved modal behavior with proper focus management

## [2.6.0] - 2025-03-19

### Added
- Pronunciation assessment feature with real-time feedback
- Color-coded transcript segments based on pronunciation quality
- Review button to stop recording and assess pronunciation
- Segmentation of speech into manageable chunks for assessment
- Visual confidence indicators for pronunciation quality

### Changed
- Enhanced speech client UI to include pronunciation assessment panel
- Improved transcript processing for better assessment accuracy
- Updated conversation layout to accommodate pronunciation feedback

## [2.5.0] - 2025-03-18

### Added
- Topic selection feature allowing users to choose conversation topics
- Eight predefined topics including Travel, Food & Cooking, Hobbies, Culture, Movies & TV, Music, Technology, and Environment
- Skip topic option for free-form conversations

### Fixed
- Resolved issue with concurrent model responses in conversations
- Fixed message handling logic to ensure proper text formatting
- Corrected topic selection route handling in Railway deployment
- Improved session storage management for navigation between screens

### Changed
- Enhanced conversation flow with better message spacing
- Improved error handling and logging for debugging
- Optimized navigation between language, topic, and level selection screens

## [2.4.0] - 2025-03-16

### Added
- Modern UI design with consistent dark theme across all application screens
- Animated UI elements with subtle fade-ins and hover effects
- Gradient backgrounds and buttons with interactive hover states
- Fixed-height level buttons for consistent visual appearance
- Enhanced loading animations with pulsing effects

### Changed
- Redesigned language selection page with modern animated elements
- Updated level selection interface with consistent styling
- Modernized speech screen with matching dark theme
- Standardized navigation buttons across all screens
- Improved modal dialogs with gradient backgrounds

### Fixed
- Ensured conversation transcript window maintains fixed height with proper scrolling
- Maintained reliable navigation between screens using direct URL approach
- Preserved all Railway deployment compatibility fixes

## [2.3.0] - 2025-03-15

### Added
- Enhanced server-side routing for improved SPA behavior in Railway environments
- Custom HTML generation for client-side routes to ensure seamless navigation
- Advanced stuck-state detection and auto-recovery for navigation issues
- Loading indicators during page transitions for better user experience
- Comprehensive logging system for debugging production environments

### Fixed
- Resolved navigation issues with "Start Learning" button in Railway deployment
- Fixed infinite loading states when navigating between pages
- Corrected routing inconsistencies between development and production environments
- Improved resilience against client-side routing failures

### Changed
- Refactored backend route handling for better Next.js compatibility
- Improved error state visualization and feedback across the application
- Enhanced Railway compatibility with more robust SSR support
- Optimized client-side navigation with direct URL handling

## [2.2.0] - 2025-03-14

### Fixed
- Fixed API issues with language and level parameters not being properly passed to the backend
- Resolved CORS issues when accessing the API from different origins
- Added proper error handling for missing language and level parameters
- Fixed TypeScript errors in the speech-client component
- Ensured language and level parameters are preserved during conversation reinitialization

### Added
- Added test endpoint to verify API connectivity
- Improved debugging logs throughout the application
- Added type declarations for speech-client component

## [2.1.0] - 2025-03-14

### Added
- Forked project from original Tutor Application
- Updated documentation to reflect the new language learning focus
- Prepared codebase for future language learning features

## [2.0.0] - 2025-03-14

### Added
- FastAPI backend implementation
- Python-based API endpoints for health checks, connection tests, and token generation
- Comprehensive error handling for API requests
- Graceful handling of static file serving
- Docker-based deployment configuration
- Unit tests for API endpoints

### Changed
- Migrated backend from Node.js/Express to Python/FastAPI
- Updated CORS configuration to support both local and production environments
- Improved static file mounting with conditional checks
- Enhanced frontend-backend integration
- Optimized Docker build process

### Removed
- Node.js Express server implementation
- Node.js backend dependencies
- Redundant configuration files

### Fixed
- Static file serving issues in Docker environments
- Module import path problems
- CORS configuration for production deployment
- Frontend URL configuration for Railway deployment

## [1.0.0] - 2025-03-01

### Added
- Initial release of the Tutor Application
- Voice conversation functionality with OpenAI integration
- Modern dark gradient UI
- WebRTC integration for real-time communication
- Responsive design for mobile and desktop
- Railway.app deployment configuration

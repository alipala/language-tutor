# Changelog

All notable changes to the Language Tutor Application will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

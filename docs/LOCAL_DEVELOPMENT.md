# Local Development Setup

## Overview

This guide provides comprehensive instructions for setting up the Language Tutor application for local development. The application consists of a Next.js frontend and a FastAPI backend, both of which need to be configured and run locally for development.

## Prerequisites

Before setting up the Language Tutor application, ensure you have the following installed:

1. **Node.js**: Version 18.x or higher
2. **Python**: Version 3.9 or higher
3. **MongoDB**: Local installation or access to a MongoDB instance
4. **Git**: For version control
5. **npm** or **yarn**: For managing frontend dependencies
6. **pip**: For managing backend dependencies

## Repository Structure

The Language Tutor application has the following structure:

```
language-tutor/
├── backend/                 # FastAPI backend
│   ├── auth_routes.py       # Authentication endpoints
│   ├── database.py          # Database connection
│   ├── learning_routes.py   # Learning plan endpoints
│   ├── main.py              # FastAPI application
│   ├── models.py            # Data models
│   ├── requirements.txt     # Python dependencies
│   └── speaking_assessment.py # Speaking assessment logic
├── frontend/                # Next.js frontend
│   ├── app/                 # Next.js app directory
│   ├── components/          # React components
│   ├── lib/                 # Utility functions
│   ├── public/              # Static assets
│   ├── styles/              # CSS styles
│   ├── next.config.js       # Next.js configuration
│   └── package.json         # Node.js dependencies
├── docs/                    # Documentation
└── README.md                # Project overview
```

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/language-tutor.git
cd language-tutor
```

### 2. Set Up the Backend

#### Install Python Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Configure Environment Variables

Create a `.env` file in the `backend` directory with the following variables:

```
OPENAI_API_KEY=your-openai-api-key
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=language_tutor
SECRET_KEY=your-secret-key-at-least-32-chars-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GOOGLE_CLIENT_ID=your-google-client-id
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
```

Replace `your-openai-api-key` with your actual OpenAI API key, which you can obtain from the [OpenAI Dashboard](https://platform.openai.com/account/api-keys).

#### Run the Backend Server

```bash
uvicorn main:app --reload --port 8000
```

The backend server will be available at `http://localhost:8000`.

### 3. Set Up the Frontend

#### Install Node.js Dependencies

```bash
cd frontend
npm install
```

#### Configure Environment Variables

Create a `.env.local` file in the `frontend` directory with the following variables:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id
```

Replace `your-google-client-id` with your actual Google Client ID.

#### Run the Frontend Development Server

```bash
npm run dev
```

The frontend development server will be available at `http://localhost:3000`.

## MongoDB Setup

### Local MongoDB

If you're using a local MongoDB installation:

1. **Install MongoDB Community Edition**:
   - [MongoDB Installation Guide](https://docs.mongodb.com/manual/installation/)

2. **Start MongoDB**:
   ```bash
   mongod --dbpath /path/to/data/directory
   ```

3. **Create the Database**:
   ```bash
   mongosh
   use language_tutor
   ```

### MongoDB Atlas

If you prefer using MongoDB Atlas:

1. **Create a MongoDB Atlas Account**:
   - [MongoDB Atlas Signup](https://www.mongodb.com/cloud/atlas/register)

2. **Create a Cluster**:
   - Follow the Atlas UI to create a free tier cluster

3. **Configure Network Access**:
   - Add your IP address to the IP Access List

4. **Create a Database User**:
   - Create a user with read/write access to the database

5. **Get the Connection String**:
   - Click "Connect" on your cluster
   - Select "Connect your application"
   - Copy the connection string and replace `<password>` with your database user's password
   - Update the `MONGODB_URL` in your `.env` file

## OpenAI API Setup

To use the language model and speech recognition features:

1. **Create an OpenAI Account**:
   - [OpenAI Signup](https://platform.openai.com/signup)

2. **Generate an API Key**:
   - Go to [API Keys](https://platform.openai.com/account/api-keys)
   - Create a new secret key
   - Copy the key and add it to your `.env` file as `OPENAI_API_KEY`

3. **Set Up Billing**:
   - The application uses paid OpenAI models
   - Add a payment method to your OpenAI account

## Google OAuth Setup

To enable Google Sign-In:

1. **Create a Google Cloud Project**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project

2. **Configure OAuth Consent Screen**:
   - Go to "APIs & Services" > "OAuth consent screen"
   - Select "External" user type
   - Fill in the required information
   - Add the scopes: `email` and `profile`

3. **Create OAuth Client ID**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Web application" as the application type
   - Add authorized JavaScript origins:
     - `http://localhost:3000`
   - Add authorized redirect URIs:
     - `http://localhost:3000/api/auth/callback/google`
   - Click "Create"
   - Copy the Client ID and add it to your environment variables

## Development Workflow

### Backend Development

The backend uses FastAPI with automatic reloading. When you make changes to the backend code, the server will automatically restart.

#### API Documentation

FastAPI provides automatic API documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

#### Testing Backend Endpoints

You can test the backend endpoints using the Swagger UI or tools like curl or Postman:

```bash
# Example: Test the health check endpoint
curl http://localhost:8000/api/health
```

### Frontend Development

The frontend uses Next.js with hot reloading. When you make changes to the frontend code, the browser will automatically update.

#### Component Structure

The frontend is organized into reusable components:

- `components/`: Shared React components
- `app/`: Next.js app directory with page components
- `lib/`: Utility functions and API clients

#### API Communication

The frontend communicates with the backend using the `fetch` API:

```typescript
// Example: Fetch user data
const fetchUserData = async () => {
  const apiUrl = getApiUrl();
  const response = await fetch(`${apiUrl}/api/user`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
  });
  
  if (response.ok) {
    const userData = await response.json();
    return userData;
  } else {
    throw new Error('Failed to fetch user data');
  }
};
```

## Database Management

### MongoDB Compass

MongoDB Compass is a graphical user interface for MongoDB that can help you manage your database:

1. **Install MongoDB Compass**:
   - [MongoDB Compass Download](https://www.mongodb.com/try/download/compass)

2. **Connect to Your Database**:
   - Use the same connection string as in your `.env` file
   - For local MongoDB: `mongodb://localhost:27017/language_tutor`
   - For MongoDB Atlas: Your Atlas connection string

3. **Explore Collections**:
   - View and edit documents
   - Create indexes
   - Run queries

### Database Initialization

The backend automatically initializes the database with required collections and indexes:

```python
# From database.py
async def init_db():
    """Initialize database connection and indexes"""
    if database is None or client is None:
        print("WARNING: Cannot initialize database indexes - no database connection")
        return
    
    try:
        # Verify connection
        await client.admin.command('ping')
        print("MongoDB connection verified with ping")
        
        # Create indexes
        await sessions_collection.create_index("created_at", expireAfterSeconds=7 * 24 * 60 * 60)
        await password_reset_collection.create_index("created_at", expireAfterSeconds=60 * 60)
        await users_collection.create_index("email", unique=True)
        
        print("Database indexes initialized successfully")
    except Exception as e:
        print(f"ERROR initializing database indexes: {str(e)}")
```

## Testing

### Backend Testing

The backend includes unit tests using pytest:

```bash
cd backend
pytest
```

### Frontend Testing

The frontend includes unit tests using Jest and React Testing Library:

```bash
cd frontend
npm test
```

## Debugging

### Backend Debugging

You can enable debug logging in the backend:

```python
# From main.py
# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG") == "1" else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

To enable debug logging, set the `DEBUG` environment variable:

```bash
DEBUG=1 uvicorn main:app --reload --port 8000
```

### Frontend Debugging

You can use the browser's developer tools to debug the frontend:

1. **React Developer Tools**:
   - Install the [React Developer Tools](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi) browser extension
   - Use it to inspect React components and state

2. **Network Tab**:
   - Use the browser's Network tab to monitor API requests
   - Check for failed requests and error responses

3. **Console Logging**:
   - Add `console.log` statements to debug code
   - Check the browser console for output

## Code Style and Linting

### Backend Code Style

The backend follows PEP 8 style guidelines. You can use flake8 for linting:

```bash
cd backend
pip install flake8
flake8
```

### Frontend Code Style

The frontend uses ESLint and Prettier for code style:

```bash
cd frontend
npm run lint
npm run format
```

## Git Workflow

1. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes and Commit**:
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

3. **Push to Remote**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a Pull Request**:
   - Go to the repository on GitHub
   - Click "New Pull Request"
   - Select your branch
   - Add a description of your changes
   - Request a review

## Troubleshooting

### Common Issues

1. **CORS Errors**:
   - Ensure the `FRONTEND_URL` in the backend `.env` file matches your frontend URL
   - Check the CORS configuration in `main.py`

2. **Database Connection Issues**:
   - Verify the `MONGODB_URL` in your `.env` file
   - Ensure MongoDB is running
   - Check network access if using MongoDB Atlas

3. **OpenAI API Errors**:
   - Verify your `OPENAI_API_KEY` is correct
   - Check your OpenAI account billing status
   - Ensure you have sufficient API credits

4. **Google OAuth Issues**:
   - Verify your `GOOGLE_CLIENT_ID` is correct
   - Ensure the authorized origins and redirect URIs are configured correctly
   - Check the browser console for OAuth errors

### Getting Help

If you encounter issues not covered in this guide:

1. **Check the Documentation**:
   - Review the relevant documentation files in the `docs` directory

2. **Search Issues**:
   - Check the GitHub repository's Issues tab for similar problems

3. **Ask for Help**:
   - Create a new issue with a detailed description of your problem
   - Include error messages, logs, and steps to reproduce

## Performance Optimization

### Backend Optimization

1. **Database Indexes**:
   - Ensure indexes are created for frequently queried fields
   - Monitor query performance using MongoDB's explain plan

2. **Asynchronous Operations**:
   - Use FastAPI's asynchronous features for I/O-bound operations
   - Avoid blocking the event loop with CPU-intensive tasks

### Frontend Optimization

1. **Code Splitting**:
   - Use Next.js's automatic code splitting
   - Import components and libraries dynamically when possible

2. **Image Optimization**:
   - Use Next.js's Image component for automatic image optimization
   - Compress and resize images before adding them to the project

3. **Performance Monitoring**:
   - Use the Lighthouse tab in Chrome DevTools to analyze performance
   - Address issues identified by Lighthouse

## Contributing

To contribute to the Language Tutor project:

1. **Follow the Git Workflow**:
   - Create feature branches
   - Make focused, well-documented commits
   - Submit pull requests for review

2. **Code Style**:
   - Follow the established code style guidelines
   - Run linting tools before committing

3. **Documentation**:
   - Update documentation to reflect your changes
   - Add comments to complex code sections

4. **Testing**:
   - Write tests for new features
   - Ensure existing tests pass

## Conclusion

This guide provides a comprehensive overview of setting up the Language Tutor application for local development. By following these instructions, you should be able to run both the frontend and backend components locally and start contributing to the project.

For deployment instructions, please refer to the [Deployment Guide](DEPLOYMENT.md).

# Use Python for the backend and Node.js for frontend build
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install Node.js for frontend build only
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire project
COPY . .

# Install Python backend dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Install frontend dependencies and build
WORKDIR /app/frontend
RUN npm install
RUN npm run build

# Back to app directory
WORKDIR /app

# Set environment variables
ENV PORT=3001
ENV NODE_ENV=production

# Expose the port
EXPOSE 3001

# Command to run the application
# Use a more direct approach to start the application
CMD ["python3", "-c", "import os, uvicorn; uvicorn.run('backend.main:app', host='0.0.0.0', port=int(os.environ.get('PORT', '3001')))"]

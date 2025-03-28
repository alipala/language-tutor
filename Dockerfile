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
# Clean npm cache and ensure a fresh install
RUN npm cache clean --force
# Install dependencies with explicit framer-motion
RUN npm install
RUN npm install framer-motion@12.6.2 --save
# Build with increased memory allocation
RUN NODE_OPTIONS="--max-old-space-size=4096" npm run build

# For standalone output mode, copy the standalone output to a location the backend can find
RUN mkdir -p /app/frontend/public
RUN cp -r /app/frontend/.next/standalone/frontend/* /app/frontend/
RUN cp -r /app/frontend/.next/static /app/frontend/public/
# Create a symlink to help the backend find the build
RUN ln -sf /app/frontend/.next/standalone /app/frontend/out

# Back to app directory
WORKDIR /app

# Set environment variables
ENV PORT=3001
ENV ENVIRONMENT=production

# Expose the port
EXPOSE 3001

# Command to run the application
# Use a more direct approach to start the application
WORKDIR /app/backend
CMD ["python3", "-c", "import os, uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=int(os.environ.get('PORT', '3001')))"]

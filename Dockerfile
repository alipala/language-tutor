# Use Python for the backend and Node.js for frontend build
# Updated to fix domain configuration for mytacoai.com
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install Node.js for frontend build AND WeasyPrint system dependencies
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    curl \
    # WeasyPrint system dependencies
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libgdk-pixbuf-xlib-2.0-dev \
    libffi-dev \
    shared-mime-info \
    libcairo2 \
    libcairo-gobject2 \
    libglib2.0-0 \
    libgtk-3-0 \
    fontconfig \
    fonts-dejavu-core \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire project
COPY . .

# Install Python backend dependencies with exact versions
# First install pymongo and motor with specific versions to ensure compatibility
RUN pip install --no-cache-dir pymongo==4.6.1 motor==3.3.2
# Then install the rest of the requirements
RUN pip install --no-cache-dir -r backend/requirements.txt

# Install frontend dependencies and build
WORKDIR /app/frontend
# Clean npm cache and ensure a fresh install
RUN npm cache clean --force
# Install dependencies with explicit framer-motion
RUN npm install
RUN npm install framer-motion@12.6.2 --save

# Set production environment variables BEFORE build
ENV NODE_ENV=production
ENV ENVIRONMENT=production

# Build with increased memory allocation and production environment
RUN NODE_OPTIONS="--max-old-space-size=4096" NODE_ENV=production npm run build

# Verify the build output exists
RUN ls -la /app/frontend/out/ || echo "Build output directory not found"
RUN ls -la /app/frontend/out/*.html || echo "No HTML files found in build output"

# For static export mode, the build output is already in the 'out' directory
# No need to copy files - the backend will serve directly from frontend/out
# The static export creates all necessary files in frontend/out

# Back to app directory
WORKDIR /app

# Set additional environment variables
ENV PORT=3001

# Expose the port
EXPOSE 3001

# Command to run the application
# Use the same approach as nixpacks.toml for consistency
WORKDIR /app/backend
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-3001}"]

# Production-ready Dockerfile for Railway deployment
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV NODE_MAJOR=20
ENV PYTHON_VERSION=3.11

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    wget \
    gnupg \
    ca-certificates \
    && add-apt-repository ppa:deadsnakes/ppa \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    nodejs \
    build-essential \
    pkg-config \
    # WeasyPrint system dependencies
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    shared-mime-info \
    libcairo2 \
    libcairo2-dev \
    libcairo-gobject2 \
    libglib2.0-0 \
    libglib2.0-dev \
    libgtk-3-0 \
    libgtk-3-dev \
    fontconfig \
    fonts-dejavu-core \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    tcl8.6-dev \
    tk8.6-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python3.11
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && ln -sf /usr/bin/python3.11 /usr/bin/python

# Upgrade pip with specific version
RUN python3 -m pip install --no-cache-dir --upgrade pip==24.0 setuptools==69.5.1 wheel==0.43.0

# Copy the entire project
COPY . .

# Install Python backend dependencies
RUN python3 -m pip install --no-cache-dir -r backend/requirements.txt

# Install frontend dependencies and build
WORKDIR /app/frontend
RUN npm cache clean --force
RUN npm install

# Set production environment variables BEFORE build
ENV NODE_ENV=production
ENV ENVIRONMENT=production

# Build with increased memory allocation and production environment
RUN NODE_OPTIONS="--max-old-space-size=4096" NODE_ENV=production npm run build

# Verify the build output exists
RUN ls -la /app/frontend/out/ || echo "Build output directory not found"

# Back to app directory
WORKDIR /app

# Set additional environment variables
ENV PORT=3001

# Expose the port
EXPOSE 3001

# Command to run the application
WORKDIR /app/backend
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-3001}"]

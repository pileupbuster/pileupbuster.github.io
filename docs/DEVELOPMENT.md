# Development Setup Guide

## Prerequisites

### Docker Setup (Recommended)
- Docker Desktop or Docker Engine
- docker-compose (included with Docker Desktop)

### Manual Setup
- Node.js 16+ and npm
- Python 3.8+
- MongoDB Atlas account (or local MongoDB)

## Quick Start with Docker

### 1. Clone Repository
```bash
git clone https://github.com/brianbruff/pileup-buster.git
cd pileup-buster
```

### 2. Start Development Environment
```bash
# Start development stack with hot reload
make dev
# OR
docker compose -f docker-compose.dev.yml up
```

This will start:
- Backend API on http://localhost:5000 (with hot reload)
- Frontend dev server on http://localhost:3000 (with hot reload)
- MongoDB on localhost:27017

### 3. Development Commands

See all available commands:
```bash
make help
```

Common commands:
- `make dev` - Start development environment
- `make logs` - View logs from all services  
- `make test-api` - Test the backend API
- `make down` - Stop all services

## Manual Setup (Without Docker)

### 1. Clone Repository
```bash
git clone https://github.com/brianbruff/pileup-buster.git
cd pileup-buster
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your MongoDB Atlas connection string
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

## Running the Application

### Development Mode

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

### MongoDB Atlas Setup

1. Create a MongoDB Atlas account
2. Create a new cluster
3. Create a database user
4. Get connection string
5. Update `MONGO_URI` in `backend/.env`

## GitHub Codespaces

This repository is pre-configured for GitHub Codespaces development:

1. **Open in Codespaces**: Click the "Code" button and select "Open with Codespaces"
2. **Automatic Setup**: The dev container will automatically:
   - Install all dependencies
   - Configure the development environment
   - Forward necessary ports (3000, 5000, 27017)
3. **Start Development**: Run `make dev` to start all services

The Codespaces configuration includes:
- VS Code extensions for Python and React development
- Docker-in-Docker support
- Pre-configured port forwarding
- Automatic dependency installation

## Project Architecture

- **Frontend**: Single-page React application
- **Backend**: RESTful API using Flask
- **Database**: MongoDB for queue persistence
- **Communication**: HTTP/JSON between frontend and backend
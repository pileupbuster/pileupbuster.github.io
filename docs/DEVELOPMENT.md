# Development Setup Guide

## Prerequisites

- Node.js 16+ and npm
- Python 3.9+
- Poetry (Python dependency management)
- MongoDB Atlas account (or local MongoDB)

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/brianbruff/pileup-buster.git
cd pileup-buster
```

### 2. Backend Setup
```bash
cd backend

# Install Poetry if not already installed
pip install poetry

# Install dependencies
poetry install

# Copy environment file and configure
cp .env.example .env
# Edit .env with your MongoDB connection string
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
# Quick start script (recommended)
./run.sh

# OR use Poetry directly
poetry run dev
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- API Documentation: http://localhost:5000/docs

### Production Mode

**Backend:**
```bash
cd backend
poetry run start-server
```

**Frontend:**
```bash
cd frontend
npm run build
# Serve the build folder with your preferred web server
```

## Available Backend Commands

- `./run.sh` - Quick start with dependency checks
- `poetry run dev` - Development server with auto-reload
- `poetry run start-server` - Production server
- `poetry run black .` - Code formatting
- `poetry run flake8` - Code linting
- `poetry run pytest` - Run tests

## MongoDB Setup

### Option 1: MongoDB Atlas (Recommended)
1. Create a MongoDB Atlas account
2. Create a new cluster
3. Create a database user
4. Get connection string
5. Update `MONGO_URI` in `backend/.env`

### Option 2: Local MongoDB
1. Install MongoDB locally
2. Start MongoDB service
3. Set `MONGO_URI=mongodb://localhost:27017/pileup_buster` in `backend/.env`

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure:

```bash
# Database configuration
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/pileup_buster
SECRET_KEY=your-secret-key-here

# FastAPI configuration
ENVIRONMENT=development
DEBUG=true

# Admin authentication configuration
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-admin-password
```

## Project Architecture

- **Frontend**: Single-page React application
- **Backend**: RESTful API using FastAPI
- **Database**: MongoDB for queue persistence
- **Communication**: HTTP/JSON between frontend and backend

## Development Workflow

1. Make changes to backend code
2. The development server will automatically reload
3. Make changes to frontend code
4. The React dev server will automatically reload
5. Test your changes in the browser
6. Commit your changes to Git

## Testing

### Backend Tests
```bash
cd backend
poetry run pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Troubleshooting

### Backend won't start
- Check that Poetry is installed: `poetry --version`
- Ensure dependencies are installed: `poetry install`
- Check MongoDB connection in `.env` file
- Check if port 5000 is already in use

### Frontend won't start
- Check Node.js version: `node --version` (should be 16+)
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check if port 3000 is already in use

### Database connection issues
- Verify MongoDB Atlas connection string
- Check network connectivity
- Ensure database user has proper permissions
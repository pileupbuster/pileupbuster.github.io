# Pileup Buster

A web application for ham radio operators to register their callsign on a callback queue.

## Project Structure

```
pileup-buster/
├── frontend/          # React frontend application
├── backend/           # Python Flask API server
├── docs/             # Documentation
└── README.md         # This file
```

## Features

- **User Interface**: React-based frontend for callsign registration
- **Admin Panel**: Secured admin interface for queue management
- **API Backend**: Python FastAPI REST API
- **Database**: MongoDB Atlas for data persistence
- **Queue Management**: FIFO queue system for callsign callbacks
- **QRZ.com Integration**: Automatic lookup of amateur radio callsign information

## Quick Start

### 🐳 Docker (Recommended)

Run the complete application with Docker:

```bash
# Clone the repository
git clone https://github.com/brianbruff/pileup-buster.git
cd pileup-buster

# Start all services
docker compose up -d
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- MongoDB: localhost:27017

For development with hot-reload:
```bash
docker compose -f docker-compose.dev.yml up
```

See [Docker Setup Guide](docs/DOCKER.md) for detailed instructions.

### Manual Setup

### Frontend Development

```bash
cd frontend
npm install
npm start
```

The frontend will be available at http://localhost:3000

### Backend Development

```bash
cd backend
pip install -r requirements.txt
python app.py
```

The API will be available at http://localhost:5000

### Environment Setup

1. Copy `backend/.env.example` to `backend/.env`
2. Update MongoDB connection string and secret key
3. **Optional: Configure QRZ.com integration**:
   - Set `QRZ_USERNAME` to your QRZ.com username
   - Set `QRZ_PASSWORD` to your QRZ.com password
   - If not configured, QRZ.com lookups will return "not configured" message
4. Ensure MongoDB Atlas cluster is accessible

## API Endpoints

### Queue Management
- `POST /api/queue/register` - Register a callsign
- `GET /api/queue/status/<callsign>` - Get callsign position with QRZ.com profile data
- `GET /api/queue/list` - List current queue

### Admin Functions
- `GET /api/admin/queue` - Admin view of queue
- `DELETE /api/admin/queue/<callsign>` - Remove callsign
- `POST /api/admin/queue/clear` - Clear entire queue
- `POST /api/admin/queue/next` - Process next callsign

## Technology Stack

- **Frontend**: React 18, CSS3, HTML5
- **Backend**: Python 3, FastAPI, uvicorn
- **Database**: MongoDB (MongoDB Atlas or local)
- **Containerization**: Docker, Docker Compose
- **Development**: Node.js, npm, pip

## GitHub Codespaces

This repository includes dev container configurations for GitHub Codespaces. Simply open the repository in Codespaces and the development environment will be automatically configured.

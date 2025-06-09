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
- **API Backend**: Python Flask REST API
- **Database**: MongoDB Atlas for data persistence
- **Queue Management**: FIFO queue system for callsign callbacks

## Quick Start

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
3. Ensure MongoDB Atlas cluster is accessible

## API Endpoints

### Queue Management
- `POST /api/queue/register` - Register a callsign
- `GET /api/queue/status/<callsign>` - Get callsign position
- `GET /api/queue/list` - List current queue

### Admin Functions
- `GET /api/admin/queue` - Admin view of queue
- `DELETE /api/admin/queue/<callsign>` - Remove callsign
- `POST /api/admin/queue/clear` - Clear entire queue
- `POST /api/admin/queue/next` - Process next callsign

## Technology Stack

- **Frontend**: React 18, CSS3, HTML5
- **Backend**: Python 3, Flask, Flask-CORS
- **Database**: MongoDB Atlas
- **Development**: Node.js, npm, pip

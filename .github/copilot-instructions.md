# Pileup Buster - Copilot Instructions

## Project Overview

Pileup Buster is a web application designed for ham radio operators to register their callsign on a callback queue. This is a pers### Real-time**: Efficient SSE implementation for live updates
- **WebSocket**: Full WebSocket API with authentication for external integrations

### Maintenance
- **Dependencies**: Keep dependencies updated and secure
- **Documentation**: Maintain up-to-date documentation for setup and deployment
- **Backwards Compatibility**: Consider migration paths for schema or API changes

## WebSocket Integration

### Qt6 Logging Software Integration
- **Pure WebSocket Protocol**: Complete admin operations without HTTP mixing
- **Authentication**: Token-based sessions with 24-hour expiry
- **Real-time Updates**: Automatic broadcasting of queue and QSO changes
- **Comprehensive Operations**: All admin functions available via WebSocket
- **Error Handling**: Detailed error codes and messages for troubleshooting

### WebSocket API Features
- **Endpoint**: `ws://localhost:8000/api/ws`
- **Authentication**: Message-based auth with session tokens
- **Admin Operations**: Queue management, QSO operations, system control
- **Public Operations**: Callsign registration, status queries
- **Broadcasting**: Real-time updates to all connected clients
- **Protocol Documentation**: Complete API reference in `/docs/WEBSOCKET_API_DOCUMENTATION.md`

### External Integration Benefits
- **Single Protocol**: Qt6 applications can use WebSocket exclusively
- **Real-time Synchronization**: Immediate updates across all connected clients
- **Robust Authentication**: Secure session management
- **Comprehensive Coverage**: All admin functions available via WebSocket
- **Clean Architecture**: No protocol mixing requiredool focused on providing an interactive, real-time experience for managing amateur radio pileup situations.

### Key Characteristics
- **100% AI-Driven Development**: All design elements, features, and implementation are powered by AI
- **Single-User Focus**: Designed as a personal tool rather than multi-tenant platform
- **Real-time Updates**: Interactive experience without manual page refreshing
- **Universal Deployment**: Supports cloud platforms, servers, or local environments

## Project Structure

```
pileup-buster/
├── .github/                    # GitHub configurations and workflows
├── backend/                    # Python FastAPI server
│   ├── app/                   # Main application code
│   │   ├── __init__.py
│   │   ├── app.py            # FastAPI application entry point
│   │   ├── auth.py           # Authentication middleware
│   │   ├── database.py       # MongoDB connection and models
│   │   ├── validation.py     # Input validation utilities
│   │   ├── websocket_protocol.py     # WebSocket message definitions
│   │   ├── websocket_handlers.py     # WebSocket connection management
│   │   ├── routes/           # API route handlers
│   │   │   ├── admin.py      # Admin-protected endpoints
│   │   │   ├── events.py     # Server-sent events
│   │   │   ├── public.py     # Public endpoints
│   │   │   ├── queue.py      # Queue management endpoints
│   │   │   └── websocket.py  # WebSocket endpoints
│   │   └── services/         # Business logic services
│   │       ├── events.py     # Event handling service
│   │       └── qrz.py        # QRZ.com integration service
│   ├── tests/                # Comprehensive test suite
│   ├── static/               # Static assets (logos, etc.)
│   ├── docker-compose.yml    # Docker compose configuration
│   ├── Dockerfile           # Backend containerization
│   ├── pyproject.toml       # Poetry dependencies and configuration
│   └── poetry.lock          # Locked dependency versions
├── frontend/                 # React TypeScript frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── contexts/         # React contexts (theme, etc.)
│   │   ├── services/         # API service layers
│   │   ├── assets/           # Static assets (images, etc.)
│   │   ├── App.tsx          # Main application component
│   │   ├── App.css          # Application styles
│   │   └── main.tsx         # React entry point
│   ├── public/              # Public assets
│   ├── package.json         # npm dependencies
│   ├── vite.config.ts       # Vite build configuration
│   └── tsconfig.json        # TypeScript configuration
├── docs/                    # Documentation
│   ├── DEVELOPMENT.md       # Development setup guide
│   ├── CLIPBOARD_FUNCTIONALITY.md
│   ├── WEBSOCKET_API_DOCUMENTATION.md  # WebSocket API reference
│   ├── images/              # Documentation screenshots
│   └── clipboard-test.html  # Testing utilities
├── LICENSE                  # MIT License
├── README.md               # Main project documentation
├── PERFORMANCE_OPTIMIZATION.md
├── STATUS_PAGE.md
├── LOGO_SETUP.md
├── WEBSOCKET_IMPLEMENTATION_COMPLETE.md  # WebSocket implementation status
├── QT6_WEBSOCKET_IMPLEMENTATION_GUIDE.md # Guide for Qt6 integration
└── WEBSOCKET_AUTH_REQUIREMENTS.md        # Authentication requirements
```

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **Database**: MongoDB (Atlas or local)
- **Authentication**: 
  - HTTP Basic Auth for admin functions (legacy REST API)
  - WebSocket session-based authentication with tokens (modern API)
- **WebSocket Support**: Full WebSocket API with authentication and admin operations
- **Dependencies Management**: Poetry
- **Testing**: pytest with asyncio support
- **Code Quality**: black (formatting), flake8 (linting), isort (import sorting)
- **External Integrations**: QRZ.com API via callsignlookuptools
- **Server**: uvicorn with auto-reload support

### Frontend
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite 6.x
- **Styling**: CSS3 with custom properties (CSS variables)
- **State Management**: React hooks and context
- **Theme Support**: Light/dark mode toggle
- **Code Quality**: ESLint with TypeScript rules
- **Real-time Communication**: Server-Sent Events (SSE) and WebSocket support

### Infrastructure
- **Containerization**: Docker and Docker Compose
- **Development**: Hot-reload for both frontend and backend
- **Deployment**: GitHub Pages (frontend), containerized backend
- **Environment**: GitHub Codespaces support
- **External Integration**: Qt6 logging software via WebSocket API

## Key Features

### Core Functionality
- **Callsign Registration**: Users can register their amateur radio callsign
- **FIFO Queue System**: First-in-first-out queue management
- **Real-time Updates**: Live queue status via Server-Sent Events and WebSocket
- **QRZ.com Integration**: Automatic callsign information lookup
- **Admin Panel**: Secure queue management interface
- **System Status**: Enable/disable registration system
- **External Integration**: Qt6 logging software integration via WebSocket API
- **Dual Protocol Support**: Both REST API and WebSocket API available

### User Interface
- **Responsive Design**: Mobile-first approach with responsive breakpoints
- **Theme Support**: Light and dark mode with system preference detection
- **Accessibility**: Reduced motion support and proper ARIA labels
- **Visual Design**: Color-coded sections (green for active, red for queue, yellow for items, blue for entry, purple for admin)
- **Admin Controls**: Integrated admin controls when authenticated
- **QSO Source Indicators**: Visual indicators showing "Worked from Pileupbuster" vs direct contacts

### Technical Features
- **REST API**: Comprehensive API with OpenAPI documentation
- **WebSocket API**: Full-featured WebSocket API with authentication and real-time updates
- **Database Persistence**: MongoDB for reliable data storage
- **Authentication**: 
  - HTTP Basic Auth for REST endpoints
  - Session-based tokens for WebSocket connections
- **Error Handling**: Comprehensive error handling and user feedback
- **Performance**: Optimized for fast load times and responsive experience
- **External Integration**: Clean WebSocket interface for logging software integration

## Development Guidelines

### Code Style
- **Backend**: Use black formatting, flake8 linting, follow FastAPI best practices
- **Frontend**: Use ESLint rules, TypeScript strict mode, React hooks patterns
- **Comments**: Document complex logic and business rules
- **Testing**: Maintain comprehensive test coverage for both unit and integration tests

### API Design
- **RESTful**: Follow REST principles for endpoint design
- **WebSocket**: Comprehensive WebSocket API for real-time operations
- **Authentication**: 
  - Protect admin REST endpoints with HTTP Basic Auth
  - Session-based authentication for WebSocket connections
- **Error Responses**: Consistent error format with appropriate HTTP status codes
- **Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Protocol Choice**: Support both REST and WebSocket for different use cases

### Database Schema
- **Collections**: Efficient MongoDB collections for queue and metadata
- **Validation**: Input validation at both API and database levels
- **Indexing**: Proper indexing for performance

### Environment Configuration
- **Required Variables**: MONGO_URI, SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD
- **Optional Variables**: QRZ_USERNAME, QRZ_PASSWORD, MAX_QUEUE_SIZE
- **Development**: Use .env files for local development
- **Production**: Environment variables for deployment

## Development Workflow

### Getting Started
1. **Docker (Recommended)**: `docker compose up -d` for full stack
2. **Manual Setup**: Separate terminal sessions for frontend and backend
3. **Environment**: Copy `.env.example` to `.env` and configure

### Testing Strategy
- **Backend Tests**: pytest with asyncio for async code testing
- **Frontend Tests**: Component and integration testing
- **End-to-End**: System integration tests
- **Coverage**: Maintain high test coverage across all components

### Deployment
- **Frontend**: Static build deployed to GitHub Pages
- **Backend**: Containerized deployment with environment variables
- **Database**: MongoDB Atlas for production, local MongoDB for development

## Important Notes for AI Development

### Project Philosophy
- This project embraces AI-driven development at all levels
- Maintain clean, readable code that can be easily understood and modified by AI
- Follow established patterns and conventions for consistency

### Architecture Decisions
- **Separation of Concerns**: Clear boundaries between frontend, backend, and database
- **Modular Design**: Components and services should be independently testable
- **Configuration**: Environment-based configuration for different deployment scenarios
- **Security**: Secure defaults with configurable authentication

### Performance Considerations
- **Frontend**: Minimize bundle size, optimize re-renders, use efficient state management
- **Backend**: Async/await patterns, database query optimization, caching strategies
- **Real-time**: Efficient SSE implementation for live updates

### Maintenance
- **Dependencies**: Keep dependencies updated and secure
- **Documentation**: Maintain up-to-date documentation for setup and deployment
- **Backwards Compatibility**: Consider migration paths for schema or API changes

This project serves as a reference implementation for modern web application development with AI assistance, focusing on clean architecture, comprehensive testing, and production-ready deployment strategies.

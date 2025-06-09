#!/bin/bash

# Docker Setup Validation Script
set -e

echo "🐳 Testing Pileup Buster Docker Setup"
echo "======================================"

# Check Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

echo "✅ Docker is available"

# Check if docker compose is available  
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available"
    exit 1
fi

echo "✅ Docker Compose is available"

# Start the services
echo "🚀 Starting services..."
docker compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Test backend API
echo "🧪 Testing backend API..."
if curl -s http://localhost:5000/api/queue/list | grep -q "queue"; then
    echo "✅ Backend API is responding"
else
    echo "❌ Backend API is not responding"
    docker compose logs backend
    exit 1
fi

# Test registering a callsign
echo "📝 Testing callsign registration..."
curl -s -X POST http://localhost:5000/api/queue/register \
    -H "Content-Type: application/json" \
    -d '{"callsign": "DOCKER-TEST"}' | grep -q "successfully"
    
if [ $? -eq 0 ]; then
    echo "✅ Callsign registration works"
else
    echo "❌ Callsign registration failed"
    exit 1
fi

# Clean up
echo "🧹 Cleaning up..."
docker compose down

echo ""
echo "🎉 All Docker tests passed!"
echo "✅ Backend containerization: Working"
echo "✅ Database connectivity: Working" 
echo "✅ API endpoints: Working"
echo "✅ Docker Compose: Working"
echo ""
echo "Next steps:"
echo "- Run 'docker compose up -d' to start all services"
echo "- Open http://localhost:3000 for frontend"
echo "- Use http://localhost:5000 for API"
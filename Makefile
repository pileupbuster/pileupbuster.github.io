# Pileup Buster - Development Commands

.PHONY: help up up-dev down build clean logs test

help: ## Show this help message
	@echo "Pileup Buster - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Start production stack
	docker compose up -d

up-dev: ## Start development stack with hot reload
	docker compose -f docker-compose.dev.yml up

down: ## Stop all services
	docker compose down

down-clean: ## Stop all services and remove volumes
	docker compose down -v

build: ## Build all Docker images
	docker compose build

clean: ## Clean up Docker images and containers
	docker system prune -f
	docker volume prune -f

logs: ## Show logs from all services
	docker compose logs -f

logs-backend: ## Show backend logs
	docker compose logs -f backend

logs-frontend: ## Show frontend logs
	docker compose logs -f frontend

logs-mongodb: ## Show MongoDB logs
	docker compose logs -f mongodb

test-api: ## Test the backend API
	@echo "Testing API endpoints..."
	@echo "Queue list:"
	@curl -s http://localhost:5000/api/queue/list | jq .
	@echo "\nRegistering test callsign..."
	@curl -s -X POST http://localhost:5000/api/queue/register -H "Content-Type: application/json" -d '{"callsign": "TEST123"}' | jq .
	@echo "\nQueue list after registration:"
	@curl -s http://localhost:5000/api/queue/list | jq .

status: ## Show status of all services
	docker compose ps

shell-backend: ## Open shell in backend container
	docker compose exec backend bash

shell-mongodb: ## Open MongoDB shell
	docker compose exec mongodb mongosh pileup_buster

# Development shortcuts
dev: up-dev ## Alias for up-dev
prod: up ## Alias for up
stop: down ## Alias for down
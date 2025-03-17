# Makefile for Zolkin Backend
# This file provides shortcuts for common deployment and development tasks

# Variables
DOCKER_COMPOSE = docker compose --project-name zolkin-backend
FLASK = flask
PIP = pip
UV = uv

.PHONY: help setup-env install-deps start-redis start-milvus start-services start stop clean docker-build docker-up docker-down

# Default target
help:
	@echo "Zolkin Backend Makefile"
	@echo ""
	@echo "Available commands:"
	@echo "  make help              - Show this help message"
	@echo "  make setup-env         - Create .env file from example"
	@echo "  make install-deps      - Install Python dependencies"
	@echo "  make start-redis       - Start Redis container"
	@echo "  make start-milvus      - Start Milvus container"
	@echo "  make start-services    - Start both Redis and Milvus"
	@echo "  make start             - Start the Flask application"
	@echo "  make stop              - Stop Redis and Milvus containers"
	@echo "  make clean             - Remove temporary files and containers"
	@echo "  make docker-build      - Build Docker containers"
	@echo "  make docker-up         - Start all services with Docker Compose"
	@echo "  make docker-down       - Stop all Docker Compose services"

# Setup environment
setup-env:
	@echo "Setting up environment variables..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env file created. Please edit it with your credentials."; \
	else \
		echo ".env file already exists."; \
	fi

# Install dependencies
install-deps:
	@echo "Installing dependencies..."
	@if command -v $(UV) > /dev/null; then \
		$(UV) sync; \
	elif command -v $(PIP) > /dev/null; then \
		$(PIP) install -r requirements.txt; \
	else \
		echo "Neither uv nor pip found. Please install one of them."; \
		exit 1; \
	fi

# Start Redis
start-redis:
	@echo "Starting Redis container..."
	docker run -d --name redis-stack-server -p 6379:6379 redis/redis-stack-server:latest || echo "Redis container may already be running"

# Start Milvus
start-milvus:
	@echo "Starting Milvus container..."
	@if [ ! -f standalone_embed.sh ]; then \
		curl -sfL https://raw.githubusercontent.com/milvus-io/milvus/master/scripts/standalone_embed.sh -o standalone_embed.sh; \
	fi
	bash standalone_embed.sh start

# Start both services
start-services: start-redis start-milvus

# Start the Flask application
start: start-services
	@echo "Starting Flask application..."
	$(FLASK) run

# Stop containers
stop:
	@echo "Stopping containers..."
	docker stop redis-stack-server || true
	docker rm redis-stack-server || true
	bash standalone_embed.sh stop || true

# Clean up
clean: stop
	@echo "Cleaning up..."
	rm -f standalone_embed.sh
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Docker commands
docker-build:
	@echo "Building Docker containers..."
	$(DOCKER_COMPOSE) build

docker-up: setup-env
	@echo "Starting all services with Docker Compose..."
	$(DOCKER_COMPOSE) up --build --detach

docker-down:
	@echo "Stopping all Docker Compose services..."
	$(DOCKER_COMPOSE) down
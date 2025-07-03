# HRIS Platform Development Makefile

.PHONY: help build up down restart logs shell test migrate createsuperuser clean backup

# Default target
help:
	@echo "Available commands:"
	@echo "  build          - Build Docker images"
	@echo "  up             - Start development environment"
	@echo "  up-prod        - Start production environment"
	@echo "  up-tools       - Start with development tools (pgAdmin, Redis Commander)"
	@echo "  down           - Stop all services"
	@echo "  restart        - Restart all services"
	@echo "  logs           - Show application logs"
	@echo "  logs-f         - Follow application logs"
	@echo "  shell          - Access Django shell"
	@echo "  bash           - Access container bash"
	@echo "  test           - Run tests"
	@echo "  test-cov       - Run tests with coverage"
	@echo "  migrate        - Run database migrations"
	@echo "  makemigrations - Create new migrations"
	@echo "  createsuperuser - Create Django superuser"
	@echo "  collectstatic  - Collect static files"
	@echo "  backup-db      - Backup database"
	@echo "  restore-db     - Restore database from backup"
	@echo "  clean          - Clean up containers and volumes"
	@echo "  clean-all      - Clean everything including images"

# Build Docker images
build:
	docker-compose build

# Development environment
up:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Production environment
up-prod:
	docker-compose --profile production up -d

# Development with tools
up-tools:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile dev-tools up -d

# Stop services
down:
	docker-compose down

# Restart services
restart:
	docker-compose restart

# View logs
logs:
	docker-compose logs

# Follow logs
logs-f:
	docker-compose logs -f

# Django shell
shell:
	docker-compose exec web python manage.py shell

# Container bash
bash:
	docker-compose exec web bash

# Run tests
test:
	docker-compose exec web python manage.py test

# Run tests with coverage
test-cov:
	docker-compose exec web coverage run manage.py test
	docker-compose exec web coverage report

# Database migrations
migrate:
	docker-compose exec web python manage.py migrate

# Create migrations
makemigrations:
	docker-compose exec web python manage.py makemigrations

# Create superuser
createsuperuser:
	docker-compose exec web python manage.py createsuperuser

# Collect static files
collectstatic:
	docker-compose exec web python manage.py collectstatic --noinput

# Backup database
backup-db:
	@echo "Creating database backup..."
	docker-compose exec postgres pg_dump -U postgres hris_platform > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup created: backup_$(shell date +%Y%m%d_%H%M%S).sql"

# Restore database (requires BACKUP_FILE variable)
restore-db:
	@if [ -z "$(BACKUP_FILE)" ]; then echo "Usage: make restore-db BACKUP_FILE=backup.sql"; exit 1; fi
	docker-compose exec -T postgres psql -U postgres hris_platform < $(BACKUP_FILE)

# Clean containers and volumes
clean:
	docker-compose down -v
	docker system prune -f

# Clean everything including images
clean-all:
	docker-compose down -v --rmi all
	docker system prune -af

# Setup development environment
setup-dev:
	@echo "Setting up development environment..."
	cp .env.example .env
	@echo "Please edit .env file with your configuration"
	@echo "Then run: make up"

# Quick development start
dev: up logs-f

# Production deployment
deploy: build up-prod

# Check services health
health:
	@echo "Checking service health..."
	@docker-compose ps
	@echo "\nTesting web service..."
	@curl -f http://localhost:8000/admin/ > /dev/null 2>&1 && echo "✓ Web service is healthy" || echo "✗ Web service is not responding"
	@echo "Testing database..."
	@docker-compose exec postgres pg_isready -U postgres > /dev/null 2>&1 && echo "✓ Database is healthy" || echo "✗ Database is not responding"
	@echo "Testing Redis..."
	@docker-compose exec redis redis-cli ping > /dev/null 2>&1 && echo "✓ Redis is healthy" || echo "✗ Redis is not responding"

# Initialize project (first time setup)
init:
	@echo "Initializing HRIS Platform..."
	@echo "Creating required directories..."
	@mkdir -p logs media staticfiles
	@chmod 755 logs media staticfiles
	make setup-dev
	make build
	make up
	@echo "Waiting for services to start..."
	@echo "Checking if services are ready..."
	@for i in $$(seq 1 30); do \
		if docker-compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1 && \
		   docker-compose exec -T web python -c "import django; print('Django ready')" >/dev/null 2>&1; then \
			echo "Services are ready!"; \
			break; \
		fi; \
		echo "Waiting... ($$i/30)"; \
		sleep 2; \
	done
	@echo "Running database migrations..."
	docker-compose exec web python manage.py migrate
	@echo "Creating superuser..."
	docker-compose exec web python manage.py shell -c "from accounts.models import User; User.objects.filter(email='admin@hris.local').exists() or User.objects.create_superuser(email='admin@hris.local', password='admin123', first_name='System', last_name='Administrator', role='admin')"
	@echo "\n🎉 Setup complete!"
	@echo "🌐 Access your D.A.N.I platform:"
	@VM_IP=$$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $$1}' || echo "localhost"); \
	echo "   Main app: http://$$VM_IP:8000/"; \
	echo "   Admin:    http://$$VM_IP:8000/admin/"
	@echo "🔐 Default credentials:"
	@echo "   Email:    admin@hris.local"
	@echo "   Password: admin123"
	@echo "⚠️  IMPORTANT: Change the default password after first login!"
# DANI Platform Makefile
# Provides automated deployment and management commands

.PHONY: help install update dev-setup test clean backup restore

# Default target
help:
	@echo "DANI Platform Management Commands"
	@echo "================================="
	@echo ""
	@echo "Deployment Commands:"
	@echo "  make install         - Fresh installation on new server"
	@echo "  make update          - Update existing installation"
	@echo "  make dev-setup       - Set up local development environment"
	@echo ""
	@echo "Management Commands:"
	@echo "  make backup          - Create backup of data and configuration"
	@echo "  make restore BACKUP= - Restore from backup directory"
	@echo "  make test            - Run test suite"
	@echo "  make clean           - Clean temporary files"
	@echo ""
	@echo "Service Commands:"
	@echo "  make start           - Start DANI platform service"
	@echo "  make stop            - Stop DANI platform service"
	@echo "  make restart         - Restart DANI platform service"
	@echo "  make status          - Show service status"
	@echo "  make logs            - Show service logs"
	@echo ""
	@echo "Database Commands:"
	@echo "  make migrate         - Run database migrations"
	@echo "  make superuser       - Create superuser account"
	@echo "  make shell           - Open Django shell"
	@echo ""

# Fresh installation
install:
	@echo "Starting fresh DANI Platform installation..."
	@if [ -f "/opt/dani/manage.py" ]; then \
		echo "ERROR: Existing installation detected. Use 'make update' instead."; \
		exit 1; \
	fi
	chmod +x deploy-fresh.sh
	./deploy-fresh.sh

# Update existing installation
update:
	@echo "Updating DANI Platform..."
	@if [ ! -f "/opt/dani/manage.py" ]; then \
		echo "ERROR: No existing installation found. Use 'make install' instead."; \
		exit 1; \
	fi
	chmod +x deploy-update.sh
	./deploy-update.sh

# Local development setup
dev-setup:
	@echo "Setting up local development environment..."
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt
	@if [ ! -f ".env" ]; then \
		cp .env.example .env; \
		echo "Created .env file from template. Please configure it."; \
	fi
	./venv/bin/python manage.py migrate
	@echo "Development setup complete!"
	@echo "Run: source venv/bin/activate && python manage.py runserver"

# Create backup
backup:
	@echo "Creating backup..."
	sudo /usr/local/bin/backup-dani.sh

# Restore from backup
restore:
	@if [ -z "$(BACKUP)" ]; then \
		echo "ERROR: Please specify backup directory: make restore BACKUP=/path/to/backup"; \
		exit 1; \
	fi
	@echo "Restoring from backup: $(BACKUP)"
	sudo systemctl stop dani-platform
	sudo -u postgres dropdb dani_platform || true
	sudo -u postgres createdb dani_platform
	sudo -u postgres psql dani_platform < $(BACKUP)/database.sql
	sudo cp -r $(BACKUP)/media/* /opt/dani/media/
	sudo cp $(BACKUP)/.env /opt/dani/
	sudo chown -R www-data:www-data /opt/dani
	sudo systemctl start dani-platform
	@echo "Restore completed"

# Run tests
test:
	@if [ -f "/opt/dani/manage.py" ]; then \
		sudo -u www-data /opt/dani/venv/bin/python /opt/dani/manage.py test; \
	elif [ -f "manage.py" ]; then \
		./venv/bin/python manage.py test; \
	else \
		echo "ERROR: No DANI installation found"; \
		exit 1; \
	fi

# Clean temporary files
clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.log" -delete
	@echo "Cleaned temporary files"

# Service management commands
start:
	sudo systemctl start dani-platform
	@echo "DANI Platform started"

stop:
	sudo systemctl stop dani-platform
	@echo "DANI Platform stopped"

restart:
	sudo systemctl restart dani-platform
	@echo "DANI Platform restarted"

status:
	sudo systemctl status dani-platform

logs:
	sudo journalctl -u dani-platform -f

# Database commands
migrate:
	@if [ -f "/opt/dani/manage.py" ]; then \
		sudo -u www-data /opt/dani/venv/bin/python /opt/dani/manage.py makemigrations; \
		sudo -u www-data /opt/dani/venv/bin/python /opt/dani/manage.py migrate; \
	elif [ -f "manage.py" ]; then \
		./venv/bin/python manage.py makemigrations; \
		./venv/bin/python manage.py migrate; \
	else \
		echo "ERROR: No DANI installation found"; \
		exit 1; \
	fi

superuser:
	@if [ -f "/opt/dani/manage.py" ]; then \
		sudo -u www-data /opt/dani/venv/bin/python /opt/dani/manage.py createsuperuser; \
	elif [ -f "manage.py" ]; then \
		./venv/bin/python manage.py createsuperuser; \
	else \
		echo "ERROR: No DANI installation found"; \
		exit 1; \
	fi

shell:
	@if [ -f "/opt/dani/manage.py" ]; then \
		sudo -u www-data /opt/dani/venv/bin/python /opt/dani/manage.py shell; \
	elif [ -f "manage.py" ]; then \
		./venv/bin/python manage.py shell; \
	else \
		echo "ERROR: No DANI installation found"; \
		exit 1; \
	fi

# Deployment verification
verify:
	@echo "Verifying DANI Platform deployment..."
	@if [ -f "/opt/dani/manage.py" ]; then \
		echo "✓ Application files present"; \
		sudo systemctl is-active --quiet dani-platform && echo "✓ Service running" || echo "✗ Service not running"; \
		sudo systemctl is-active --quiet nginx && echo "✓ Nginx running" || echo "✗ Nginx not running"; \
		sudo systemctl is-active --quiet postgresql && echo "✓ PostgreSQL running" || echo "✗ PostgreSQL not running"; \
		curl -f -s http://localhost/ > /dev/null && echo "✓ Application responding" || echo "✗ Application not responding"; \
		sudo -u www-data /opt/dani/venv/bin/python /opt/dani/manage.py check --database default && echo "✓ Database connection" || echo "✗ Database connection failed"; \
	else \
		echo "✗ No installation found"; \
	fi

# Show deployment information
info:
	@echo "DANI Platform Deployment Information"
	@echo "==================================="
	@if [ -f "/opt/dani/manage.py" ]; then \
		echo "Installation Path: /opt/dani"; \
		echo "Current Version: $$(cd /opt/dani && git describe --tags --always)"; \
		echo "Current Branch: $$(cd /opt/dani && git rev-parse --abbrev-ref HEAD)"; \
		echo "Database: dani_platform"; \
		echo "Service: dani-platform"; \
		echo "User: www-data"; \
		echo ""; \
		echo "Recent Backups:"; \
		ls -la /backups/ | tail -5 || echo "No backups found"; \
	else \
		echo "No installation found"; \
	fi
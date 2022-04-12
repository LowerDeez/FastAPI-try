start:
	# Clean orphan images
	docker system prune
	# Run container
	docker-compose -f docker/docker-compose.yml up --build

makemigrations:
	docker-compose -f docker/docker-compose.yml run --rm fastapi bash -c "alembic revision --autogenerate -m $(message)"

migrate:
	docker-compose -f docker/docker-compose.yml run --rm fastapi bash -c "alembic upgrade head"

bash:
	docker-compose -f docker/docker-compose.yml exec fastapi bash

test:
	docker-compose -f docker/docker-compose.yml run --rm fastapi bash -c "pytest $(test) -s"

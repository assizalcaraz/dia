.PHONY: up up-dev down logs restart

up:
	docker compose up --build

up-dev:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

restart:
	docker compose down
	docker compose up --build

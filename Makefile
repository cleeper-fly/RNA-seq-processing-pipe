PROJECT_NAME := rna-seq-pipeline

.PHONY: pull start build status stop logs download_files prepare_reference create_location first_start

pull:
	${INFO} "Pulling project..."
	@ docker-compose -p $(PROJECT_NAME) -f $(COMPOSE_FILE) pull
	${INFO} "Done pulling project"

start:
	${INFO} "Running project..."
	@ docker-compose -p $(PROJECT_NAME) -f $(COMPOSE_FILE) up -d
	${INFO} "Project successfully started..."

build:
    $(INFO) "Building project..."
    @ docker-compose -p $(PROJECT_NAME) -f $(COMPOSE_FILE) build
    ${INFO} "Done building project"

status:
	@ docker-compose -p $(PROJECT_NAME) -f $(COMPOSE_FILE) ps

stop:
	${INFO} "Stopping project..."
	@ docker-compose -p $(PROJECT_NAME) -f $(COMPOSE_FILE) down

logs:
	${INFO} "Logging project..."
	@ docker-compose -p $(PROJECT_NAME) -f $(COMPOSE_FILE) logs -f --tail=32

download_files:
    ${INFO} "Preparing first run. Downloading files..."
    ./upload.sh

prepare_reference:
    ${INFO} "Preparing first run. Preparing reference..."
    ./prepare_reference.sh

create_location:
    ${INFO} "Creating file with location path..."
    ./create_location.sh

first_start: build create_location download_files prepare_reference



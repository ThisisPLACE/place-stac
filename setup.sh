#!/bin/bash

set -e

if [[ "${CI}" ]]; then
    set -x
fi

function usage() {
    echo -n \
        "Usage: $(basename "$0")
Sets up this project for development.
"
}

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    # Check for local install of pypgstac
    if [[ ! -d "./pypgstac/pypgstac.egg-info" ]]; then

        IN_VIRTUAL_ENV=$(python -c "import sys; print(sys.prefix != sys.base_prefix)")
        if [[ "${IN_VIRTUAL_ENV}" == "True" ]]; then
            echo "Installing requirements and pypgstac into virtual environment..."
            pip install -r requirements.txt
        else
            echo "ERROR: You must be in a virtual environment to run scripts/setup."
            echo "Otherwise install pypgstac locally with scripts/install before running this script."
            exit 1;
        fi
    fi

    # Build docker containers
    echo "Installing/updating STAC FASTAPI..."
    git clone https://github.com/stac-utils/stac-fastapi.git
	cd stac-fastapi
	pip install -e \
    stac_fastapi/api -e \
    stac_fastapi/types -e \
    stac_fastapi/extensions -e \
    stac_fastapi/pgstac

	echo "Compiling docker image..."
	make image
	docker-compose run --rm loadjoplin-pgstac
	make docker-run-pgstac

fi

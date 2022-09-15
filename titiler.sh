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
            echo "Good, pypgstac is installed into virtual environment..."

    		echo "Installing/updating TiTiler..."
			export POSTGRES_USER=username
			export POSTGRES_PASS=password
			export POSTGRES_DBNAME=postgis
			export POSTGRES_HOST=database
			export POSTGRES_PORT=5439
			
			pip install titiler.pgstac["psycopg-binary"]
			uvicorn titiler.pgstac.main:app --reload
			
			echo "Done."
        else
            echo "ERROR: You must be in a virtual environment to run scripts/setup."
            echo "Otherwise install pypgstac locally with scripts/install before running this script."
            exit 1;
        fi
    fi

fi

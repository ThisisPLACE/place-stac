# Project Title

## Description

This project serves STAC indices and useful previews of a large body of drone imagery for hyperlocal mapping. It uses Python, FastAPI, Docker, TiTiler, Nginx, Postgres, PostGIS, GDAL, Rasterio, rio cogeo, and pgstac. The services deployed include two web applications (stac-fastapi and titiler) and a Postgres database with PostGIS extensions and pgstac.

## Getting Started

### Prerequisites

* Docker
* Python 3
* GDAL
* pyexiv2
* stac_pydantic
* boto3

### Installation

* Clone the repo: `git clone <repo_url>`
* Install dependencies: `<insert command if applicable>`

## Deployment

Deployment of this application is designed to be as simple as possible.

Run Docker Compose on the host machine network:
```bash
docker compose -f docker-compose.host-network.yml up -d
```

At this point, nginx, should be hosting on port 8080. From root (/) nginx delegates to a stac-fastapi instance which is backed by PgSTAC and Postgres. At /data/ an instance of titiler which is also backed by pgstac through titiler-pgstac is available for the preview, display, and exploration of relevant assets in the STAC catalog.

## Data Manipulation Scripts

There are a few scripts in the `scripts` directory to manipulate and prepare data.

* **add_gps.py**: Uses a TSV/CSV reference file to update the EXIF headers related to latitude/longitude and altitude (if available). By convention, Geotags.txt was the name of the file. As such, the script will look for that file and fall back on the first CSV file it finds in the user-supplied directory. 
* **build_stac.py**: A command-line utility for constructing a STAC collection and associated STAC JPG items. This script works with user-supplied arguments and reference to JPG headers to generate geometries and footprints unique to each item.
* **ingest_directory.py**: Will ingest all STAC collections stored in line-delimited JSON files that end in '_collection.json' and all STAC items stored in line-delimited JSON files that end in '_items.json' within the user-supplied directory.

Usage:

```bash
# Replace `script.py` with the script name and `[args]` with the necessary arguments.
python scripts/script.py [args]
```

## Reporting Issues

Issues can be reported via the GitHub issue tracker.
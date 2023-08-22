# PLACE STAC API

## Description

This project serves STAC indices and useful previews of a large body of drone imagery for hyperlocal mapping. It uses Python, FastAPI, Docker, TiTiler, Nginx, Postgres, PostGIS, GDAL, Rasterio, rio cogeo, and pgstac. The services deployed include two web applications (stac-fastapi and titiler) and a Postgres database with PostGIS extensions and pgstac.

## Deployment

### Deployment 1: the easy part

Deployment of this application is designed to be as simple as possible. To this end, deployment is as simple as starting the server using Docker Compose with host networking. Docker compose is generally used in the context of development. Using it to manage deployment is done here to make things user-friendly for teams with varying levels of technical expertise, and suitable for deployment on commodity hardware rather than on the many specific services provided by large cloud hosting services (e.g. AWS or Azure).


Assuming the host machine and its data are set up as expected (see the section on [directory conventions](#directory-conventions) below), deployment can be done in one line. Run Docker Compose on the host machine network in daemon mode (headless):
```bash
docker compose -f docker-compose.host-network.yml up -d
```

#### Verification of Deployment

Three services are (ideally!) now running.
1. A stac-api on port 8081
2. A titiler services on port 8082
3. A postgres instance on port 5433 (not 5432, as this will collide with other postgres instances that may - and currently do - live on the host machine)

You can verify successful deployment with:
```bash
docker ps
```

If things have gone well, the three services mentioned above should be seen. Their image names are `place-stac-server`, `place-stac-tiler`, and `ghcr.io/stac-utils/pgstac:v0.7.6` which correspond to the stac api, titiler, and postgres respectively.


### Deployment 2: The parts you can't see

While the primary deployment process is designed to be straightforward and user-friendly, there is underlying complexity that primarily "just works," but may require understanding if infrastructure changes are needed in the future.

#### Application Load Balancer (ALB) on AWS

An ALB is set up within AWS to streamline the addition of authentication. This ALB directs traffic to a specific EC2 instance.

#### EC2 Instance with WireGuard and nginx

The targeted EC2 instance leverages WireGuard and nginx to delegate traffic to the specific services, which are located on a machine outside of AWS. At this point, the reader may point out that nginx could be deployed with docker compose as well. This is true - and it was - but as of the writing of this document (08/2023) there exist other deployed applications on the host machine which nginx running on ports 80/443 would collide. Deployment of nginx on this external machine is not optimal but it is a simple, easy to understand workaround.

- **STAC API (Port 8081):** A spatio-temporal asset catalog (STAC) API that provides functionality for browsing and querying geospatial data.
- **Titiler (Port 8082):** A dynamic tile rendering service to manage and visualize raster data.

Here's a high-level overview of the flow:

1. **ALB on AWS:** Receives incoming requests and forwards them to the EC2 instance.
2. **EC2 Instance:** Utilizes WireGuard for secure tunneling and nginx for reverse proxying to delegate the traffic.
3. **STAC API & Titiler:** Handle the requests on ports 8081 and 8082, respectively, on an external machine.

#### Considerations for Future Changes

Understanding this hidden complexity is crucial if changes to the infrastructure are anticipated. Here are some key considerations:

- **Authentication:** The addition of authentication via Amazon Cognito can be enabled through an integration with the ALB. User-defined cognito user pools and/or third party authentication pools are available to ease this integration.
- **Logging:** Logging can happen at a few different application layers. The simplest option, which logs all access to the ALB, can be enabled via AWS console under the ALB "Monitoring" field when editing ALB attributes.
- **Routing and Traffic Management:** Updates to WireGuard, iptables, and/or nginx configurations might be required if there are changes in how traffic should be routed. These should be able to stay the same assuming infrastructure isn't modified down the line.
- **Service Endpoints:** Alterations to the STAC API or titiler endpoints may necessitate updates to the nginx configuration which is running on EC2.


## Data Handling Scripts

There are a few scripts in the `scripts` directory to manipulate and prepare data.

### Directory Conventions

A set of conventions exist for managing files. The directory structure mandated by these conventions is necessary for proper functioning of the STAC API, Tiling service, and of the various scripts for creating and ingesting STAC data. Conventions are somewhat dangerous as they are hard to remember and difficult to enforce. As such, they are as simple as possible and the data being managed is backed up to S3 in case of extreme system failure.

1. There exists a local directory (/home/storage/stac) which recursively bottoms out in files that end in either _items.json or _collection.json. These files are, themselves, stac records which are used to hydrate the postgres tables used by STAC FastAPI.
2. There exists a local directory (/home/storage/imagery) which contains subdirectories that organize data collected by PLACE. This data is further broken down into aerial (/home/storage/imagery/aerial) and ground (/home/storage/imagery/ground) data with further distinctions around file type encoded below that (e.g. cogs at /home/storage/imagery/aerial/cog and jpgs at /home/storage/imagery/aerial/jpg)
3. Both of these directories are *exactly* mirrored on S3. This enables bulk downloads for PLACE customers when desired and ensures that backups are available should catastrophe strike the machine hosting PLACE's STAC catalog. Currently, imagery is stored at `s3://place-data` whereas stac records are stored at `s3://place-stac`.

#### Synchronizing Data

Mirroring data between a local directory and S3 can be accomplished very easily with the AWS command line tools. In particular, `aws s3 sync` is a command that will copy all and only the files that are different between an S3 URI and a filesystem URI (or vice versa).

Supposing that we want to ensure that STAC records are backed up from the local path (i.e. /home/storage/stac) to the S3 path (i.e. s3://place-stac), we can use the following command:
```bash
aws s3 sync /home/storage/stac s3://place-stac
```

### Script usage

* **add_gps.py**: Uses a TSV/CSV reference file to update the EXIF headers related to latitude/longitude and altitude (if available). By convention, Geotags.txt was the name of the file. As such, the script will look for that file and fall back on the first CSV file it finds in the user-supplied directory. *NOTE*: This should not be necessary now that GPS headers are added in the field.
* **build_jpg_stac.py**: A command-line utility for constructing a STAC collection and associated STAC items for raw drone JPG imagery (assumes gps headers are available). This script works with user-supplied arguments and reference to JPG headers to generate geometries and footprints unique to each item.

collection_id,collection_description,collection_title,input_directory,output_directory,output_s3_backup
Assume that the directory /home/storage/stac/aerial/jpg contains the tif files that we want to index:
```bash
docker compose -f docker-compose.host-network.yml run -v /home/storage/stac/aerial/cog:/home/storage/stac/aerial/cog -e AWS_ACCESS_KEY_ID={AWS_ID} -e AWS_SECRET_ACCESS_KEY={AWS_SECRET} place-scripts /bin/bash -c "python3 scripts/build_jpg_stac.py --collection_id providenciales-raw --collection_description "Raw drone imagery from Providenciales" --collection_title "Providenciales raw imagery" --input-directory s3://place-data/aerial/jpg/providenciales --output_directory /home/storage/stac/aerial/jpg --output_s3_backup s3://place-stac/aerial/jpg"
```

That's a lot of arguments, but they have long names which should clarify their intent. Just be sure that imagery exists both locally (following covention, at /home/storage/imagery/aerial/jpg) and (mirroring local directory structure) at the S3 location passed in for the `--input_directory` argument. This is necessary because we advertise the s3 path (which is not public) via stac catalog but only serve data during the lifetime of the application from the filesystem of the machine hosting the tiler and stac service.

* **build_cog_stac.py**: A command-line utility for constructing a STAC collection and associated STAC items for orthorectified TIF imagery in COG format.

Like above, assume that the directory /home/storage/stac/aerial/cog contains the tif files that we want to index:
```bash
docker compose -f docker-compose.host-network.yml run -v /home/storage/stac/aerial/cog:/home/storage/stac/aerial/cog -e AWS_ACCESS_KEY_ID={AWS_ID} -e AWS_SECRET_ACCESS_KEY={AWS_SECRET} place-scripts /bin/bash -c "python3 scripts/build_cog_stac.py"
```
* **ingest_directory.py**: Will ingest all STAC collections stored in line-delimited JSON files that end in '_collection.json' and all STAC items stored in line-delimited JSON files that end in '_items.json' within the user-supplied directory.

```bash
docker compose -f docker-compose.host-network.yml run -v /home/storage/stac/aerial/jpg:/home/storage/stac/aerial/jpg place-scripts /bin/bash -c "python3 scripts/ingest_directory.py /home/storage/stac/aerial/jpg"
```

## Reporting Issues

Issues can be reported via the GitHub issue tracker.
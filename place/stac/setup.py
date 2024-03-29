"""stac_fastapi: pgstac module."""

from setuptools import find_namespace_packages, setup

install_requires = [
    "orjson",
    "stac-fastapi.pgstac==2.4.7",
    "stac-fastapi.api==2.4.7",
    "stac-fastapi.types==2.4.7",
    "stac-fastapi.extensions==2.4.7",
    "uvicorn[standard]",
    "pypgstac[psycopg]==0.7.6",
    "pygeoif==0.7",
    "boto3==1.28.28",
    "rio-stac==0.8.0"
]

extra_reqs = {
    "dev": [],
    "docs": []
}

setup(
    name="place.stac",
    description="An implementation of STAC API based on the FastAPI framework and using the pgstac backend for PLACE.",
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
    ],
    license="MIT",
    install_requires=install_requires,
    packages=find_namespace_packages(exclude=["alembic", "tests", "scripts"]),
    zip_safe=False,
    entry_points={
    },
)
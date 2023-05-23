"""stac_fastapi: pgstac module."""

from setuptools import find_namespace_packages, setup

install_requires = [
    "uvicorn[standard]",
    "psycopg[c]",
    "titiler.application==0.11.7",
    "titiler.pgstac==0.4.0",
    "titiler.pgstac[psycopg-c]==0.4.0",
    "orjson",
]

extra_reqs = {
    "dev": [],
    "docs": []
}

setup(
    name="place.tiles",
    description="A titiler implementation using the pgstac backend for PLACE.",
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
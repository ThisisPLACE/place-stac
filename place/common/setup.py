"""place: common module."""

from setuptools import find_namespace_packages, setup

install_requires = [
    "orjson",
    "pydantic",
]

setup(
    name="place.common",
    description="Code used in both the tiler and stac server",
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
)
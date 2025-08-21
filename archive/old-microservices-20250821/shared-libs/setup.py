"""
OpsConductor Shared Libraries
Common utilities and models for microservices
"""

from setuptools import setup, find_packages

setup(
    name="opsconductor-shared",
    version="1.0.0",
    description="Shared libraries for OpsConductor microservices",
    packages=find_packages(),
    install_requires=[
        "pydantic==2.5.0",
        "httpx==0.25.2",
        "structlog==23.2.0",
        "python-jose[cryptography]==3.3.0",
        "pika==1.3.2",  # RabbitMQ client
        "redis==5.0.1",
    ],
)
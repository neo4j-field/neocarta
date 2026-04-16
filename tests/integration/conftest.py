"""Shared pytest fixtures for all integration tests."""

import os

import pytest
from neo4j import GraphDatabase
from testcontainers.neo4j import Neo4jContainer


@pytest.fixture(scope="module")
def setup():
    """Start a Neo4j container once per test module."""
    container = Neo4jContainer("neo4j:5.26.23")
    print("\nStarting Neo4j container...")
    container.start()
    print(f"Neo4j container started at {container.get_connection_url()}")

    os.environ["NEO4J_URI"] = container.get_connection_url()
    os.environ["NEO4J_HOST"] = container.get_container_host_ip()
    os.environ["NEO4J_PORT"] = str(container.get_exposed_port(7687))

    yield container

    print("\nStopping Neo4j container...")
    try:
        if hasattr(container, "_container") and container._container:
            container.stop()
    except Exception as e:
        print(f"Error stopping container: {e}")


@pytest.fixture
def neo4j_driver(setup: Neo4jContainer):
    """Provide a Neo4j driver for each test, with database cleanup."""
    driver = GraphDatabase.driver(setup.get_connection_url(), auth=(setup.username, setup.password))

    with driver.session(database="neo4j") as session:
        session.run("MATCH (n) DETACH DELETE n")

    try:
        yield driver
    finally:
        with driver.session(database="neo4j") as session:
            session.run("MATCH (n) DETACH DELETE n")
        driver.close()

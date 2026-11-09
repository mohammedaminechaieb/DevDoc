#!/bin/bash
docker compose up neo4j -d
echo "Neo4j: bolt://localhost:7687  |  browser: http://localhost:7474"

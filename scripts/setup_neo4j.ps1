# Run from the repo root: .\scripts\setup_neo4j.ps1
docker compose up neo4j -d
Write-Host 'Neo4j: bolt://localhost:7687  |  browser: http://localhost:7474'

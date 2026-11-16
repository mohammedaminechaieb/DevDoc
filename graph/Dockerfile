# graph/Dockerfile - image du job d'extraction + chargement Neo4j (séparée de l'image API)
# Contexte de build = racine du dépôt (voir docker-compose.graph.yml)
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 HF_HOME=/hf_cache
# torch CPU uniquement : évite ~2 Go de bibliothèques CUDA inutiles
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY graph/requirements-extraction.txt /tmp/req.txt
RUN pip install --no-cache-dir -r /tmp/req.txt neo4j python-dotenv
COPY . .
CMD ["sh", "-c", "python -m graph.pipeline ${PIPELINE_ARGS:-} && python -m graph.neo4j_loader --wait 180 ${LOADER_ARGS:-}"]

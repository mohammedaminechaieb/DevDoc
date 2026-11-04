# graph/entity_extractor.py
# Primary owner: Oussema
#
# Input:  one chunk dict {chunk_id, text, framework, url, ...}
# Output: list[{name, type, chunk_id}]

import spacy
nlp = spacy.load("en_core_web_sm")

TECH_KEYWORDS = [
    "FastAPI","Pydantic","LangChain","LangGraph",
    "CrewAI","AutoGen","MCP","FAISS","Neo4j","React","Docker"
]

def extract_entities(chunk: dict) -> list[dict]:
    # TODO: NER + keyword matching on chunk["text"]
    raise NotImplementedError

# graph/neo4j_loader.py
# Primary owner: Oussema
#
# Reads CORPUS_PATH (full_corpus/full_corpus_clean.jsonl) -> extracts -> loads into Neo4j
# Run: python -m graph.neo4j_loader

from neo4j import GraphDatabase

from config.settings import CORPUS_PATH, NEO4J_PASS, NEO4J_URI, NEO4J_USER
from graph.entity_extractor import extract_entities
from graph.relation_extractor import extract_relations


def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))


def load_chunk(driver, chunk: dict):
    # TODO: MERGE (:Chunk {chunk_id}) with url, framework, concept, component, version
    raise NotImplementedError


def load_entities(driver, entities: list[dict]):
    # TODO: MERGE entity nodes + (entity)-[:MENTIONED_IN]->(:Chunk)
    raise NotImplementedError


def load_relations(driver, relations: list[dict]):
    # TODO: MERGE relationships with their provenance properties
    raise NotImplementedError


if __name__ == "__main__":
    import jsonlines

    driver = get_driver()
    with jsonlines.open(CORPUS_PATH) as reader:
        for chunk in reader:
            ents = extract_entities(chunk)
            rels = extract_relations(chunk, ents)
            load_chunk(driver, chunk)
            load_entities(driver, ents)
            load_relations(driver, rels)
    driver.close()
    print("Graph loaded.")

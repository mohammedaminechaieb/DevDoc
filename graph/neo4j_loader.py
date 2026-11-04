# graph/neo4j_loader.py
# Primary owner: Oussema
#
# Reads data/full_corpus_clean.jsonl -> extracts -> loads into Neo4j

from neo4j import GraphDatabase
from config.settings import NEO4J_URI, NEO4J_USER, NEO4J_PASS, CORPUS_PATH
from graph.entity_extractor import extract_entities
from graph.relation_extractor import extract_relations

def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

def load_entities(driver, entities: list[dict]):
    # TODO: MERGE nodes into Neo4j
    raise NotImplementedError

def load_relations(driver, relations: list[dict]):
    # TODO: MERGE relationships into Neo4j
    raise NotImplementedError

if __name__ == "__main__":
    import jsonlines
    driver = get_driver()
    with jsonlines.open(CORPUS_PATH) as reader:
        for chunk in reader:
            ents = extract_entities(chunk)
            rels = extract_relations(chunk, ents)
            load_entities(driver, ents)
            load_relations(driver, rels)
    driver.close()
    print("Graph loaded.")

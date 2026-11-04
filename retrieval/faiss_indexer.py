# retrieval/faiss_indexer.py
# Primary owner: Ghassen
#
# Reads data/full_corpus_clean.jsonl, embeds every chunk,
# builds FAISS IndexFlatL2, saves to FAISS_INDEX path.

import faiss
from config.settings import CORPUS_PATH, FAISS_INDEX

def build_index():
    # TODO: load corpus, embed chunks, build index, save
    raise NotImplementedError

def load_index() -> faiss.Index:
    # TODO: load from FAISS_INDEX path
    raise NotImplementedError

if __name__ == "__main__":
    build_index()
    print("FAISS index built.")

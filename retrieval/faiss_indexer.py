# retrieval/faiss_indexer.py
# Owner: Ghassen
#
# Reads CORPUS_PATH, embeds every chunk, builds a FAISS index and saves it to FAISS_INDEX.
# Also writes FAISS_META (one chunk per line, same order as the index) to map ids -> chunks.
# Run: python -m retrieval.faiss_indexer

from config.settings import CORPUS_PATH, FAISS_INDEX, FAISS_META


def build_index():
    # TODO: load corpus, embed chunks, build index, save index + metadata
    #       (create the data/ folder first)
    raise NotImplementedError


def load_index():
    # TODO: import faiss; return faiss.read_index(FAISS_INDEX)
    raise NotImplementedError


if __name__ == "__main__":
    build_index()
    print("FAISS index built.")

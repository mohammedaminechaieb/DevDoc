# generation/answer_generator.py
# Primary owner: Mariem

from generation.reranker import rerank
from generation.prompt_builder import build_prompt
from generation.llm_client import call_llm

def generate_answer(query: str, chunks: list[dict]) -> dict:
    # TODO: rerank -> build_prompt -> call_llm
    # Returns: {answer, sources: [{url, framework, text}], query}
    raise NotImplementedError

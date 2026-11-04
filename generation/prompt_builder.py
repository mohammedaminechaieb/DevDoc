# generation/prompt_builder.py
# Primary owner: Mariem

SYSTEM_PROMPT = (
    "You are DevDoc AI, an expert assistant for technical documentation. "
    "Answer ONLY from the provided context. "
    "If the answer is not in the context, say so explicitly. "
    "Always cite the source URL and framework."
)

def build_prompt(query: str, chunks: list[dict]) -> str:
    # TODO: format chunks as numbered context blocks, append question
    raise NotImplementedError

# graph/extractors/__init__.py
# Registre : get_extractor("dictionary" | "gliner" | "relex" | "llm", **options)
# Les imports sont paresseux : gliner / groq ne sont requis que si on utilise l'extracteur.


def get_extractor(name: str, **kw):
    if name == "dictionary":
        from graph.extractors.dictionary import DictionaryExtractor
        return DictionaryExtractor(**kw)
    if name == "gliner":
        from graph.extractors.gliner_extractor import GlinerExtractor
        return GlinerExtractor(**kw)
    if name == "relex":
        from graph.extractors.relex_extractor import GlinerRelexExtractor
        return GlinerRelexExtractor(**kw)
    if name == "llm":
        from graph.extractors.llm_extractor import LLMExtractor
        return LLMExtractor(**kw)
    raise ValueError(f"extracteur inconnu : {name} (dictionary | gliner | relex | llm)")


ALL_NAMES = ["dictionary", "gliner", "relex", "llm"]

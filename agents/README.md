# agents/ - LangGraph Orchestrator
Owner: _to assign_ | Branch: feat/agents

Implements the agentic architecture of NLP.pdf section 6.

## Flow
```
START -> intent_analyzer -> knowledge_retriever -> route by intent -> specialist -> reviewer -> END
```

| File | Role (NLP.pdf) | Intents |
|---|---|---|
| intent_analyzer.py | Intent Analyzer | sets `intent`, `entities` |
| knowledge_retriever.py | Knowledge Retrieval (FAISS + Neo4j) | all |
| responder.py | grounded RAG answer (generation/) | learn, explore |
| architecture_advisor.py | Architecture Advisor | recommend, design |
| code_assistant.py | Code Assistant | code |
| evaluation_assistant.py | Evaluation Assistant (`run` + `review`) | evaluate (+ reviews all) |
| orchestrator.py | builds the StateGraph, `run_copilot()` | - |
| state.py | `CopilotState`, `INTENTS` | - |

## Use
```python
from agents.orchestrator import run_copilot
result = run_copilot("Which framework should I use for a multi-agent research system?")
print(result["intent"], result["answer"])
```

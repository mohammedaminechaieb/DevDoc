# agents/ - LangGraph Orchestrator
Shared module: each file belongs to the person who owns that part of the pipeline.
Work on your own branch (see the root README).

Implements the agentic architecture of NLP.pdf section 6.

## Flow
~~~
START -> intent_analyzer -> knowledge_retriever -> route by intent -> specialist -> reviewer -> END
~~~

| File | Role (NLP.pdf) | Intents | Owner |
|---|---|---|---|
| orchestrator.py | builds the StateGraph, `run_copilot()` | - | Amine |
| state.py | `CopilotState`, `INTENTS` | - | Amine |
| intent_analyzer.py | Intent Analyzer | sets `intent`, `entities` | Amine |
| knowledge_retriever.py | Knowledge Retrieval (FAISS + Neo4j) | all | Mariem |
| responder.py | grounded RAG answer (generation/) | learn, explore | Ghassen |
| architecture_advisor.py | Architecture Advisor | recommend, design | Ghassen |
| code_assistant.py | Code Assistant | code | Ghassen |
| evaluation_assistant.py | Evaluation Assistant (`run` + `review`) | evaluate (+ reviews all) | Oussema |

## Use
~~~python
from agents.orchestrator import run_copilot
result = run_copilot("Which framework should I use for a multi-agent research system?")
print(result["intent"], result["answer"])
~~~

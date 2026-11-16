// frontend/src/lib/mock.js
// Owner: Oussema
// Demo response used while the backend is offline, so the UI can be developed and shown on its own.
// Same shape as POST /api/query (api/schemas/response.py); graph nodes/edges as built by graph/queries.py.

export function mockResponse(question) {
  return {
    query: question,
    intent: 'design',
    entities: ['LangGraph', 'Multi-Agent System', 'Memory'],
    answer: [
      'For a research-and-report system, use a **multi-agent workflow** orchestrated by a state graph [1].',
      '',
      '**Agents**',
      '- **Researcher**: searches the web with a search tool and stores raw findings in the shared state [2].',
      '- **Analyst**: reads the findings and extracts the key facts.',
      '- **Writer**: turns the analysis into the final report.',
      '',
      '**State and memory**: one shared state object carries the question, findings and draft between nodes [1][3].',
      '',
      '```python',
      'from langgraph.graph import StateGraph, START, END',
      '',
      'graph = StateGraph(ReportState)',
      'graph.add_node("researcher", research)',
      'graph.add_node("analyst", analyse)',
      'graph.add_node("writer", write_report)',
      'graph.add_edge(START, "researcher")',
      'graph.add_edge("researcher", "analyst")',
      'graph.add_edge("analyst", "writer")',
      'graph.add_edge("writer", END)',
      'app = graph.compile()',
      '```',
      '',
      '*Demo answer: the backend is offline, so this response is simulated.*',
    ].join('\n'),
    sources: [
      { chunk_id: 'demo-1', framework: 'langgraph', url: 'https://langchain-ai.github.io/langgraph/concepts/low_level/',
        text: 'A StateGraph is parameterised by a user-defined State object. Nodes are functions that receive the state and return updates; edges define which node runs next.' },
      { chunk_id: 'demo-2', framework: 'crewai', url: 'https://docs.crewai.com/concepts/agents',
        text: 'Agents are autonomous units that can perform tasks, make decisions and use tools. Each agent has a role, a goal and a backstory.' },
      { chunk_id: 'demo-3', framework: 'langgraph', url: 'https://langchain-ai.github.io/langgraph/concepts/memory/',
        text: 'Short-term memory is part of the graph state and is persisted with a checkpointer. Long-term memory is stored across threads.' },
    ],
    graph: {
      nodes: [
        { id: 'langgraph', label: 'LangGraph', type: 'Framework', df: 890, seed: true },
        { id: 'multi-agent system', label: 'Multi-Agent System', type: 'Concept', df: 410, seed: true },
        { id: 'memory', label: 'Memory', type: 'Concept', df: 520, seed: true },
        { id: 'stategraph', label: 'StateGraph', type: 'Component', df: 230, seed: false },
        { id: 'checkpointer', label: 'Checkpointer', type: 'Component', df: 120, seed: false },
        { id: 'agent', label: 'Agent', type: 'Component', df: 1500, seed: false },
        { id: 'tool', label: 'Tool', type: 'Component', df: 1200, seed: false },
        { id: 'crewai', label: 'CrewAI', type: 'Framework', df: 600, seed: false },
        { id: 'routing', label: 'Routing', type: 'Technique', df: 90, seed: false },
      ],
      edges: [
        { source: 'langgraph', target: 'stategraph', relation: 'PROVIDES', confidence: 0.92, evidence: 'LangGraph provides the StateGraph class to build workflows.' },
        { source: 'langgraph', target: 'multi-agent system', relation: 'SUPPORTS', confidence: 0.88, evidence: 'LangGraph supports multi-agent systems through subgraphs.' },
        { source: 'stategraph', target: 'agent', relation: 'CONTAINS', confidence: 0.8, evidence: 'Each node of the graph can be an agent.' },
        { source: 'agent', target: 'tool', relation: 'USES', confidence: 0.95, evidence: 'Agents use tools to act on the outside world.' },
        { source: 'agent', target: 'memory', relation: 'HAS', confidence: 0.9, evidence: 'An agent has short-term and long-term memory.' },
        { source: 'memory', target: 'checkpointer', relation: 'USES', confidence: 0.85, evidence: 'Short-term memory is persisted with a checkpointer.' },
        { source: 'multi-agent system', target: 'agent', relation: 'CONTAINS', confidence: 0.9, evidence: 'A multi-agent system is made of several agents.' },
        { source: 'multi-agent system', target: 'routing', relation: 'USES', confidence: 0.7, evidence: 'A supervisor routes work between agents.' },
        { source: 'langgraph', target: 'crewai', relation: 'ALTERNATIVE_TO', confidence: 0.75, evidence: 'CrewAI is an alternative framework for multi-agent workflows.' },
      ],
    },
    review: { ok: true, issues: [] },
  }
}

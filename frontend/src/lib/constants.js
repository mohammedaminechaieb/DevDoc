// frontend/src/lib/constants.js
// Owner: Oussema
// One entry per intent of agents/state.py (features A-F of NLP.pdf section 4).

export const INTENTS = {
  learn:     { letter: 'A', label: 'Learn',     title: 'Learning assistant',       hint: 'Explains Agentic AI concepts with examples' },
  recommend: { letter: 'B', label: 'Recommend', title: 'Framework recommendation', hint: 'Compares frameworks and technologies' },
  design:    { letter: 'C', label: 'Design',    title: 'Architecture designer',    hint: 'Turns an idea into an agentic architecture' },
  code:      { letter: 'D', label: 'Code',      title: 'Code assistant',           hint: 'Code examples, project structure, debugging' },
  explore:   { letter: 'E', label: 'Explore',   title: 'Workflow explorer',        hint: 'Understand how an agentic workflow runs' },
  evaluate:  { letter: 'F', label: 'Evaluate',  title: 'Evaluation assistant',     hint: 'Quality, reliability and hallucinations' },
}

export const EXAMPLES = {
  learn:     'What is the difference between a classic LLM and an AI agent?',
  recommend: 'Compare CrewAI vs AutoGen for multi-agent collaboration.',
  design:    'I want several agents that search the web, analyse the results and write a report. How should I design the architecture?',
  code:      'Give me a code example of a LangGraph StateGraph with two nodes and a conditional edge.',
  explore:   'Walk me through the workflow of a LangGraph agent step by step.',
  evaluate:  'How can I evaluate the reliability of a multi-agent system and limit hallucinations?',
}

export const TOP_K_OPTIONS = [3, 5, 8, 10]
export const MIN_QUESTION = 3
export const MAX_QUESTION = 2000

// Node colours of the graph view: blues first, a few muted accents so types stay distinguishable
const TYPE_PALETTE = ['#0b2545', '#2563eb', '#0e7490', '#64748b', '#4f46e5', '#0f766e', '#7c8db5', '#1e3a8a']
const TYPE_ORDER = ['Framework', 'Concept', 'Component', 'Technology', 'Technique', 'Protocol', 'Tool', 'Agent']

export function typeColor(type) {
  if (!type) return '#94a3b8'
  const i = TYPE_ORDER.indexOf(type)
  if (i >= 0) return TYPE_PALETTE[i]
  let hash = 0
  for (const ch of type) hash = (hash * 31 + ch.charCodeAt(0)) % 997
  return TYPE_PALETTE[hash % TYPE_PALETTE.length]
}

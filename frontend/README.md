# frontend/ - React UI
Owner: Oussema | Branch: feat/frontend
Oussema also owns: api/routes/health.py, agents/evaluation_assistant.py,
tests/eval/, tests/integration/, notebooks/04_evaluation.ipynb

## Features
- Question box (Enter sends, Shift+Enter = new line) sending `{question, top_k, use_graph, history}` to `POST /api/query`
- Options: number of sources (`top_k`) and the knowledge-graph switch (`use_graph`)
- Welcome screen with the six features of NLP.pdf (A-F), each with a ready-to-send example
- Shows, for every answer: the detected mode (intent), the concepts found in the question (`entities`),
  the reviewer verdict (`review`: Verified / Needs checking + the list of issues) and the response time
- Answer rendered as Markdown with copyable code blocks; inline citations `[n]` are buttons that open source n
- **Sources** tab: numbered like the prompt context, framework, link and an expandable excerpt
- **Knowledge graph** tab: interactive graph (react-force-graph-2d) of `graph` = `{nodes, edges}`;
  drag, zoom, click a concept to see its relations, their confidence and the evidence passage
- Keeps the conversation history (last turns) so follow-up questions work
- Clear errors (501 pipeline incomplete, 422, 500, timeout) with a "Try again" button
- Header status polls `GET /health` every 20 s

## Mock (demo) mode
If the backend cannot be reached, the UI switches to demo mode (yellow status, "Demo answer" badge)
and answers with `src/lib/mock.js`, so the UI can be developed and shown independently.
HTTP errors of a running backend (501, 500...) are NOT hidden by the mock: they are displayed.

## Layout
~~~
src/main.jsx, App.jsx        entry point
src/styles.css               design tokens (dark blue + white) and all styles
src/lib/api.js               calls to the backend (health, query, error messages, history)
src/lib/constants.js         intents A-F, examples, graph colours
src/lib/mock.js              demo response
src/pages/Home.jsx           state of the conversation
src/components/              Header, Welcome, SearchBar, Message, AnswerCard, SourcesList,
                             GraphViewer (lazy loaded), Badges (intent / entities / review)
~~~

## Run
~~~
cd frontend
npm install
npm run dev
~~~
App: http://localhost:5173 (proxies `/api` and `/health` to http://localhost:8000)
Production build: `npm run build` (output in `dist/`, git-ignored).

## Contract with the backend
Request `POST /api/query`: `{question (3-2000 chars), top_k (1-20), use_graph, history: [{role, content}]}`.
Response: `{query, intent, entities, answer, sources: [{chunk_id, url, framework, text}], graph, review: {ok, issues}}`.
Graph nodes `{id, label, type, df, seed}`, edges `{source, target, relation, confidence, evidence, chunk_id}`
(format produced by `graph/queries.py::query_subgraph`). Missing fields are tolerated.

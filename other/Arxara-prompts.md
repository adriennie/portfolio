# Prompts for completing this project

## Prompt 1 — Project Scaffold + Backend Core

```bash
You are building a production FastAPI backend for an AI Autonomous Research Assistant.

TECH STACK: Python 3.11, FastAPI, Uvicorn, LangChain v0.3, Claude API (tool_use, model: claude-sonnet-4-20250514), Qdrant (qdrant-client), httpx (async), tenacity, pydantic v2, python-dotenv.

CREATE this exact folder structure:
backend/
├── main.py
├── config.py
├── requirements.txt
├── .env.example
├── models/
│   ├── __init__.py
│   ├── paper.py
│   └── session.py
├── services/
│   ├── __init__.py
│   ├── arxiv.py
│   ├── semantic_scholar.py
│   └── qdrant_service.py
├── agent/
│   ├── __init__.py
│   ├── tools.py
│   ├── orchestrator.py
│   └── prompts.py
├── api/
│   ├── __init__.py
│   └── research.py
└── middleware/
    ├── __init__.py
    └── request_id.py

RULES:
- All HTTP calls use httpx.AsyncClient only — never requests
- All endpoints have response_model and status_code
- All env vars loaded via config.py using pydantic BaseSettings — raise error if missing
- tenacity retry (max 3, exponential backoff) on all external API calls
- mypy strict compatible type hints throughout
- Use asyncio.gather for concurrent arXiv + S2 calls

IMPLEMENT in full:
1. config.py — BaseSettings loading CLAUDE_API_KEY, SEMANTIC_SCHOLAR_API_KEY, QDRANT_URL
2. models/paper.py — Paper and ReviewDraft Pydantic models exactly as specced
3. models/session.py — SessionState with status: Literal["pending","searching","ranking","clustering","extracting","writing","complete","error"], progress: int (0-100), current_step: str
4. services/arxiv.py — async search_arxiv(topic: str, max_results: int) -> List[Paper] using arXiv REST API (https://export.arxiv.org/api/query), parse Atom XML with xml.etree.ElementTree
5. services/semantic_scholar.py — async search_semantic_scholar(topic: str, max_results: int) -> List[Paper] using GET https://api.semanticscholar.org/graph/v1/paper/search
6. services/qdrant_service.py — init_collection(), upsert_papers(papers), get_all_vectors() using qdrant-client
7. middleware/request_id.py — adds X-Request-ID header to every response
8. main.py — FastAPI app with CORS (localhost:5173), request_id middleware, router mounted at /api
9. requirements.txt — pin all versions exactly

Do not scaffold placeholders. Write complete working code for every file.
```

## Prompt 2 — LangChain Agent + Claude tool_use Orchestrator

```bash
Continue building the AI Research Assistant backend. The scaffold from Prompt 1 exists. Now implement the full LangChain agent.

FILES TO IMPLEMENT IN FULL:

agent/prompts.py — Define these prompt templates as Python string constants:
- QUERY_EXPANSION_PROMPT: takes {topic}, returns 3 search keyword variants
- RELEVANCE_SCORING_PROMPT: takes {topic}, {title}, {abstract}, returns integer 1-10
- KEY_FINDINGS_PROMPT: takes {abstract}, returns JSON {"findings": "bullets", "novelty": "high|medium|low"}
- CLUSTER_THEME_PROMPT: takes {paper_titles_and_findings}, returns theme name string
- REVIEW_SYNTHESIS_PROMPT: takes {topic}, {clusters_json}, returns full Markdown review with sections: ## Introduction, ## Summary of Included Papers (markdown table), ## Key Findings by Theme, ## Research Gaps, ## Conclusion. Academic style, inline citations [Author, Year].

agent/tools.py — Implement these as standalone async functions (not LangChain tools yet):
- async deduplicate_papers(papers: List[Paper]) -> List[Paper]: deduplicate by id field using dict
- async score_papers(papers: List[Paper], topic: str, client: anthropic.AsyncAnthropic) -> List[Paper]: batch 5 papers per Claude call using RELEVANCE_SCORING_PROMPT, set paper.relevance_score
- async extract_findings(paper: Paper, client: anthropic.AsyncAnthropic) -> Paper: single Claude call using KEY_FINDINGS_PROMPT, set paper.key_findings, truncate abstract to 2000 chars
- async cluster_papers(papers: List[Paper], qdrant_svc) -> Dict[str, List[Paper]]: embed abstracts via Claude (use anthropic embeddings or fallback to sentence-transformers all-MiniLM-L6-v2 dim=384 if Claude embeddings unavailable), store in Qdrant, run sklearn HDBSCAN(min_cluster_size=2), return dict of {theme_name: [papers]}

agent/orchestrator.py — Implement async run_research_pipeline(session_id, topic, max_papers, session_store, claude_client, qdrant_svc) that:
1. Updates session status at each step
2. Calls asyncio.gather(search_arxiv, search_semantic_scholar) concurrently
3. Calls deduplicate_papers
4. Calls score_papers (batched)
5. Filters top max_papers by relevance_score
6. Calls extract_findings concurrently with asyncio.gather (all papers at once)
7. Calls cluster_papers
8. Makes final Claude call with REVIEW_SYNTHESIS_PROMPT
9. Returns completed ReviewDraft
10. Wraps entire pipeline in try/except; sets session status="error" on any failure

RULES:
- claude_client = anthropic.AsyncAnthropic(api_key=config.CLAUDE_API_KEY)
- All Claude calls use model="claude-sonnet-4-20250514", max_tokens=1000 (2000 for review synthesis)
- Abstract truncation at 2000 chars before every Claude call — enforce in every function
- Use functools.lru_cache on extract_findings keyed by paper.id
- No blocking calls in async functions
```

## Prompt 3 — FastAPI Endpoints + SSE Progress Streaming

```bash
Continue the AI Research Assistant. Scaffold + agent exist. Now implement the API layer and real-time streaming.

IMPLEMENT api/research.py in full with these 4 endpoints:

1. POST /api/research/start
   - Body: ResearchRequest(topic: str = Field(min_length=3, max_length=200), max_papers: int = Field(default=10, ge=5, le=20))
   - Creates a new SessionState, stores in in-memory dict SESSION_STORE: Dict[str, SessionState]
   - Launches orchestrator as asyncio.create_task (non-blocking)
   - Returns: SessionResponse(session_id: str)
   - Rate limit: 5 requests/minute per IP using slowapi

2. GET /api/research/stream/{session_id}
   - Returns: StreamingResponse with media_type="text/event-stream"
   - Polls SESSION_STORE every 0.5s and yields SSE events: data: {status, progress, current_step}\n\n
   - Closes stream when status in ["complete", "error"]
   - SSE format exactly: "data: {json}\n\n"

3. GET /api/research/result/{session_id}
   - Returns full ReviewDraft if status=="complete"
   - Returns 404 if session not found
   - Returns 202 with {status, progress} if still processing

4. POST /api/research/regenerate
   - Body: RegenerateRequest(session_id: str, max_papers: int, recency_year: Optional[int])
   - Resets session, re-runs pipeline with new params
   - Returns new SessionResponse

ALSO implement in main.py:
- slowapi Limiter with key_func=get_remote_address
- @app.exception_handler(RateLimitExceeded) returns 429 JSON
- Lifespan context manager (not deprecated on_event) that initialises Qdrant collection on startup

SESSION_STORE must be a module-level dict in api/research.py. The orchestrator receives a reference to it and updates SessionState in place.

All responses must be JSON. No HTML error pages.
```

## Prompt 4 — React Frontend (Complete)

```bash
Build the complete React 18 frontend for the AI Research Assistant.

TECH STACK: React 18, Vite, TypeScript, TailwindCSS v3, shadcn/ui, Zustand, axios, react-markdown, remark-gfm, EventSource (native browser API for SSE).

CREATE this structure:
frontend/
├── index.html
├── vite.config.ts          # proxy /api → http://localhost:8000
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── store/
    │   └── researchStore.ts
    ├── api/
    │   └── client.ts
    ├── components/
    │   ├── InputPanel.tsx
    │   ├── OutputPanel.tsx
    │   ├── AgentProgress.tsx
    │   ├── PaperList.tsx
    │   └── ExportButtons.tsx
    └── types/
        └── index.ts

IMPLEMENT IN FULL:

types/index.ts — Paper, ReviewDraft, SessionState, ResearchRequest interfaces matching backend Pydantic models exactly.

store/researchStore.ts — Zustand store with:
- topic: string, maxPapers: number, sessionId: string | null
- status: string, progress: number, currentStep: string
- result: ReviewDraft | null, papers: Paper[]
- actions: setTopic, setMaxPapers, startResearch, reset
- startResearch action: POST /api/research/start → get session_id → open EventSource to /api/research/stream/{id} → update progress/status on each SSE event → on complete, GET /api/research/result/{id} → set result

api/client.ts — axios instance with baseURL from vite proxy, typed functions: startResearch(req), getResult(id).

App.tsx — Two-column layout (40/60 split on ≥1200px, stacked on tablet). No card wrapper, pure TailwindCSS. Import InputPanel left, OutputPanel right.

InputPanel.tsx — Topic textarea (min 3 chars validation), shadcn Slider for maxPapers (5-20), Start button (disables during processing), AgentProgress below button.

AgentProgress.tsx — shadcn Progress bar, current step text, animated spinner when active. Hidden when status is idle.

PaperList.tsx — Collapsible list (shadcn Collapsible) showing selected papers with title + relevance score badge. Only shows when papers exist.

OutputPanel.tsx — Skeleton loader while processing. react-markdown with remark-gfm when result exists. Placeholder text when idle. ExportButtons at bottom when result exists.

ExportButtons.tsx — Three buttons: Copy (copies full_markdown to clipboard, shows toast), Download .md (triggers file download), Download .docx (POST to /api/research/export if implemented, else skip docx for now).

RULES:
- No class components
- TailwindCSS only — no inline styles
- max-w-screen-2xl mx-auto px-8 on root container
- All components fully typed with TypeScript
- Mobile (<768px): show "Best experienced on desktop" banner, hide main layout
- EventSource must close on component unmount or status complete/error
```

## Prompt 5 — Docker, Tests, Polish & README Verification

```bash
Finalize the AI Research Assistant. All code exists. Now wire everything together, add tests, and production polish.

1. CREATE docker-compose.yml:
   - Service: qdrant (image: qdrant/qdrant:latest, port 6333:6333, volume qdrant_storage:/qdrant/storage)
   - Service: backend (build: ./backend, port 8000:8000, env_file: .env, depends_on: qdrant, command: uvicorn main:app --host 0.0.0.0 --port 8000)
   - Service: frontend (build: ./frontend, port 5173:5173, depends_on: backend, command: npm run dev -- --host)
   - Named volume: qdrant_storage
   - Network: research-net (bridge)

2. CREATE backend/Dockerfile:
   FROM python:3.11-slim, WORKDIR /app, COPY requirements.txt, RUN pip install --no-cache-dir -r requirements.txt, COPY . ., CMD uvicorn main:app --host 0.0.0.0 --port 8000

3. CREATE frontend/Dockerfile:
   FROM node:18-alpine, WORKDIR /app, COPY package*.json, RUN npm ci, COPY . ., EXPOSE 5173, CMD npm run dev -- --host

4. CREATE backend/tests/ with these test files in full:

tests/test_services.py:
- test_search_arxiv_returns_list: mock httpx, assert returns List[Paper], len ≤ max_results
- test_search_s2_returns_list: mock httpx, same pattern
- test_deduplicate_removes_same_id: create 3 papers with 2 duplicate ids, assert result has 2 unique

tests/test_agent.py:
- test_score_papers_sets_relevance: mock anthropic client returning "8", assert paper.relevance_score == 8.0
- test_extract_findings_truncates_abstract: mock anthropic, assert abstract sent to Claude is ≤ 2000 chars
- test_orchestrator_sets_complete_status: mock all services, run pipeline, assert session status=="complete"

tests/test_api.py:
- test_start_research_returns_session_id: TestClient POST /api/research/start, assert 202, assert "session_id" in response
- test_result_returns_404_unknown: GET /api/research/result/bad-id, assert 404
- test_result_returns_202_while_processing: start session, immediately GET result, assert 202

Use pytest, pytest-asyncio, pytest-httpx, pytest-mock. All external calls mocked. No live API calls.
Add pytest.ini with asyncio_mode = auto.

5. CREATE .github/workflows/ci.yml:
   - Trigger: push to main, PR to main
   - Job: test (ubuntu-latest, python 3.11)
   - Steps: checkout, pip install -r requirements.txt pytest pytest-asyncio pytest-httpx pytest-mock, pytest tests/ --cov=. --cov-report=term-missing, fail if coverage < 80%

6. VERIFY and fix any import errors across all files. Run: cd backend && python -m mypy . --strict and resolve all type errors. Run: cd backend && python -m pytest tests/ -v and ensure all tests pass.

7. UPDATE vite.config.ts proxy to handle SSE correctly:
   server: { proxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true, ws: true } } }

Final check: the app must run end-to-end with just:
   cp .env.example .env  # add CLAUDE_API_KEY
   docker-compose up
   # open http://localhost:5173
```

*Usage note:* Each prompt is self-contained enough to paste directly into Cursor's composer (Cmd+I). Use @workspace in Cursor before Prompts 2–5 so it reads the existing files. If a file gets truncated mid-generation, follow up with: "Continue from where you stopped in [filename]."

# Project 8: Fully Advanced AI — Autonomous Multi-Agent Research Orchestrator

    Build a multi-agent system where a Planner agent decomposes a research question into subtasks, dispatches them to specialized sub-agents (web search agent, PDF reader agent, data analyst agent, citation formatter agent), and a Synthesizer agent merges all outputs into a structured report. Each agent runs asynchronously, has memory via vector store, and the system self-corrects if a sub-agent returns low-confidence output. Format: WebApp (React or Streamlit frontend + FastAPI orchestration backend).

    Covers: Async execution at full depth (asyncio task groups, concurrent sub-agent calls), OOP paradigms at architecture level (abstract BaseAgent class, concrete subclasses, dependency injection), pydantic for inter-agent message schemas, structured logging across distributed agents, virtual environment and dependency resolution (complex multi-library stack), unit testing philosophy (each agent independently testable with mock inputs), process/resource management (controlling token budgets per agent to avoid cost explosion).

    Swiss value: This is production-grade agentic AI — exactly what USI Lugano, EPFL spinoffs, and Zurich AI labs prototype. It signals senior-level systems thinking while you are still in MSc, which is extremely rare and memorable to Swiss hiring committees.

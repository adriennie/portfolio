# Project 7: AI + Cybersecurity — Adversarial Prompt Injection Detection System

    Build a security layer for LLM-powered applications. A FastAPI service sits in front of any AI endpoint, classifies incoming prompts using a fine-tuned classifier + LLM-as-judge pattern, flags prompt injection / jailbreak attempts, logs them with severity levels, and blocks or sanitizes before forwarding to the real model. Includes a Streamlit dashboard showing attack attempt analytics. Format: WebApp + API service.

    Covers: OOP deeply (abstract threat classifier base class, multiple detector subclasses), async execution (concurrent threat scoring while request is in flight), pydantic for strict input schemas, structured logging for audit trails, try/except/finally for graceful failure under attack, process/memory management concepts (handling burst attack traffic).

    Swiss value: AI security is a direct regulatory requirement under the EU AI Act, which Switzerland is aligning to. Firms like Kudelski Security, ABB, and Swiss cantonal banks are actively hiring for this intersection. This differentiates you sharply from pure ML candidates.

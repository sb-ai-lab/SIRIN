---
title: SIRIN
emoji: 🔎
colorFrom: purple
colorTo: pink
sdk: docker
app_port: 8501
pinned: false
tags:
  - hallucination-detection
  - answerability
  - longmemeval
  - demo
short_description: Hallucination inspection — replay + live API judges
---

# SIRIN — hallucination inspection, live

Interactive demo for **SIRIN: A Unified Toolkit for Detecting Contextual
Hallucinations in Retrieval-Augmented and Memory-Grounded LLM Systems**.

Paste a context–question–answer triple (or pick a curated case from PsiloQA,
RAGTruth, or LongMemEval) and see where the answer leaves the evidence:
span-level highlighting, response-level verdicts, claim cards, answerability
checks, and side-by-side detector comparison.

**How detection runs here.** This Space has no GPU. The landing cards show
verified recorded results from the paper's Qwen3.5-4B campaign (labelled
"Recorded result · verified — detection is not live"). Live detection uses
API judges: paste your own OpenAI / OpenRouter / Anthropic key in the sidebar
— it stays in your browser session only, never stored, logged, or exported.
The default judge model is a free OpenRouter route, so a free OpenRouter key
is enough to try span-level judging (each span run makes 3 requests; free
keys allow ~50/day). No user data is stored.

Full toolkit: https://github.com/sb-ai-lab/SIRIN

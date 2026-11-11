# Handshake Submission Copy

## What real task does the application solve?

AI Quality Lab reduces repetitive manual work when evaluating AI-generated responses against defined rubrics and checking for potential privacy risks. It turns a prompt, candidate response, optional reference, and weighted rubric into a saved, evidence-backed first-pass review.

## How does the application work?

The React client validates and submits an evaluation to FastAPI with an idempotency key and private browser ownership session. The backend saves it to PostgreSQL, analyzes response structure, scans potential PII patterns, applies deterministic and clearly labeled heuristic rubric checks, optionally calls a configured model provider, calculates a weighted report, and persists the result. Every read is scoped to the owning session.

## What does the live diagram display?

The React Flow diagram displays eight real backend stages. Its status, timestamps, safe output summaries, retries, errors, and durations come from ordered events saved by the server and streamed over SSE. Durations use a monotonic clock and are never hardcoded. Refreshing reconstructs the graph from the database.

## How are failures handled?

Invalid requests return actionable field errors without clearing the form. Duplicate keys return the original run. Optional provider calls use strict timeouts, bounded exponential-backoff retries, schema validation, and a visible deterministic fallback. Potential PII blocks external AI by default. Transactions roll back on database failure, submissions remain saved where persistence is available, and browser reconnection resumes from the last stored sequence.

## How does replay work?

Replay loads the original event records and reveals them in their stored order. Reviewers can play, pause, restart, or change visualization speed. Stored timestamps and execution durations never change.

## Technology

React, TypeScript, Vite, React Flow, FastAPI, Pydantic, SQLAlchemy, PostgreSQL, and Server-Sent Events. The project includes automated tests, a production build, a Replit deployment configuration, and an exact publishing checklist.

## Accuracy note

The app never presents heuristics as proof of factual correctness and never fabricates model results when a provider is unavailable.

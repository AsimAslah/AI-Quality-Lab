# Demo Script (4–5 minutes)

## 1. Frame the problem (30 seconds)

“AI Quality Lab reduces repetitive response review. Instead of an unexplained score, it separates checks we can verify mechanically, useful heuristics, and optional model judgment—and records every real processing stage.”

Show the Dashboard and the architecture truth statement.

## 2. Submit a real evaluation (60 seconds)

Open **New evaluation**.

- Prompt: “Write a concise refund reply. Ask for the order number, state the 30-day policy, and do not request payment-card data.”
- Response: include the order-number and 30-day language; optionally include `customer@example.com` to trigger privacy review.
- Reference: “Refunds are accepted within 30 days. Support may request an order number but never full payment-card data.”
- Criteria: required phrases, clear structure, reference coverage, instruction following.

Explain weights and method labels. Submit.

## 3. Show real execution (60 seconds)

On Live Execution, point out:

- statuses arrive from persisted SSE events;
- each completed node has its actual measured duration;
- Privacy displays categories/counts without exposing raw matches in event metadata;
- optional AI is skipped if disabled, unavailable, or privacy-gated.

Click two stages to show server timestamps, safe metadata, and duration.

## 4. Inspect the report (50 seconds)

Show the weighted score, criterion method badges, evidence, and limitations. Emphasize that the tool does not present lexical overlap as factual proof. Export Markdown or JSON.

## 5. Replay and persistence (40 seconds)

Click **Replay execution**, then Play/Pause, change to 2×, and Restart. Explain that speed changes visualization only. Refresh the page and show that report/events remain. Open History and return to the same run.

## 6. Failure recovery (optional reviewer mode, 40 seconds)

In a local development environment with `ENABLE_FAILURE_TESTING=true`, submit `failure_mode: provider_timeout` through an API client while a dummy provider key is configured. Show the actual retry event followed by recovered deterministic fallback. Do not enable unrestricted failure injection on the public app.

## 7. Close (20 seconds)

“The productivity win is a faster, consistent first-pass review. The engineering differentiator is that execution, recovery, timing, and limitations are first-class data—not animations pretending to be work.”

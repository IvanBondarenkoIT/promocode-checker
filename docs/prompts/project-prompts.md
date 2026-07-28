# Project Prompts

## Architecture prompt

Design the `promocode-checker` system with:

- FastAPI backend
- PostgreSQL for checker state
- cashier PWA with absolute autofocus
- admin and viewer roles
- ERP reconciliation through proxy/direct adapters
- Telegram alerts for changes and failures
- Railway demo and Windows Server Docker production

## Review prompt

For each completed stage:

- review the implementation
- summarize what was completed
- list what might be missing
- list open questions before the next stage
- confirm which tests were run and what they proved

## Anti-fraud prompt

Evaluate whether:

- manual promo closure is backed by ERP sale evidence
- suspicious timing gaps exist
- admin overrides are fully audited
- Telegram alerts are deduplicated and actionable

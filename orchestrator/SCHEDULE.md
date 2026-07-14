# Scheduling the AI Operations Manager agency cycle

Registration is a tool action (the `schedule` skill / `CronCreate`), not
code — do this once Phases 0-6 have been manually verified per each
phase's steps in the plan (see PREREQUISITES.md and the phase verification
notes).

**Prompt to schedule:** the contents of `ai_ops_agency_prompt.md` (same
pattern as the existing `recurring_agent_prompt.md`).

**Suggested interval:** every 15-30 minutes. Faster doesn't help — cold
email replies don't arrive that quickly, and Gmail/GHL rate limits make
tighter polling counterproductive. Start closer to 30 minutes for the first
week to keep send volume low while confirming deliverability is healthy,
then tighten if needed.

**Before registering the schedule:**
1. Confirm every Phase 0 prerequisite in `PREREQUISITES.md` is filled in.
2. Run `python orchestrator/run_pipeline.py` manually once and confirm it
   reports `RUNNING` (not an error) and syncs at least one lead correctly.
3. Run one full manual cycle by hand, following `ai_ops_agency_prompt.md`
   step by step yourself, with `DRY_RUN=1` set in `config/.env` — confirm a
   pitch email arrives correctly formatted in your own inbox before ever
   setting `DRY_RUN=0`.
4. Only after a real end-to-end test (one real demo generated, one real
   pitch sent to a test address you control, one real Stripe test-mode
   checkout completed, one Telegram notification received) should you
   register the recurring schedule and switch Stripe to live mode.

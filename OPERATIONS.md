# Manual paper-state approval and activation checklist

Status: NOT ACTIVATED. No scheduled trading or paper-state writes.

## 1. Protect the approval environment
In GitHub repository Settings > Environments, create `paper-state-approval`.
Enable Required reviewers and select an authorized reviewer. Disable self-review
bypass where available. Ensure branch restrictions permit only the intended
development branch. Do not rely on an environment name alone as an approval gate:
unconfigured environments do not guarantee reviewer approval.

## 2. Workflow availability
The manual-only workflow is `.github/workflows/paper-commit.yml`.
GitHub's workflow_dispatch generally requires the workflow to exist on the
default branch. It is currently only on the development branch; DO NOT merge
the draft PR or move the workflow to main without a separate review.

## 3. Security review before first state write
- Review workflow permissions (`contents: write` only for the commit job).
- Confirm required reviewer enforcement in the environment.
- Confirm concurrency group `stc04-rb-paper-state` and `cancel-in-progress: false`.
- Confirm the GitHub state backend uses `paper-state/state.json` with expected SHA.
- Confirm all tests, live data validation and read-only preview pass.
- Confirm no exchange order endpoints or API keys are present.
- Confirm `paper-state/state.json` starts with 10000 USDT and no trades.
- On the first approved manual run, inspect the run log and verify exactly one
  state commit. Re-run on the same daily candle and verify no second commit.
- Review the complete strategy, costs, and daily valuation assumptions before
  any unattended scheduling.

## 4. Fail-closed behavior
If candles are stale, incomplete, missing, or out of order; GitHub SHA changes;
or API connectivity fails, the run must fail without persisting a new state.
No automatic schedule has been enabled.

## 5. Current readiness and next gate
- The GitHub connector can publish source changes but cannot configure environment
  protection or manually dispatch workflows.
- The write workflow remains manual-only and is not present on the default branch.
- The current write workflow references `paper-state-approval`; merely naming
  an environment is NOT equivalent to requiring a reviewer.
- Never enable a daily schedule before verifying first commit, a duplicate-day
  no-op, and a missed-day failure with a real GitHub Actions run.
- This simulator rejects gaps in persisted daily state rather than silently
  skipping a day. Backfill/reconciliation must be designed before unattended use.
- The quote endpoint is a live reference quote without an exchange timestamp;
  execution is illustrative and should not be mistaken for a historical fill.

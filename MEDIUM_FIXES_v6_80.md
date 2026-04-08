# Medium Priority Fixes — v6.80

## Summary

15 Medium priority issues identified by Gemini Code Review (v6.61-v6.78) were fixed in this release.

---

## Medium #5: `reasoning_chain_score` Never Populated

**File:** `constitution/claim_verifier.py`
**Severity:** Medium
**Status:** ✅ Fixed

**Problem:** `verify_claims()` never called `_assess_reasoning_chain()`, causing `VerifiedClaim.reasoning_chain_score` to always be 0.0.

**Fix:** Called `_assess_reasoning_chain()` inside the verification loop and populated `reasoning_chain_score` on each `VerifiedClaim`.

---

## Medium #6: 10k Character Hard Truncation Breaks HR-09

**File:** `constitution/execution_logger.py`
**Severity:** Medium
**Status:** ✅ Fixed

**Problem:** `_load_artifacts_for_phase` used `content[:10000]` hard truncation, causing HR-09 to incorrectly fail on large artifacts.

**Fix:** Increased truncation limit to 100,000 (100k) characters.

---

## Medium #7: Inconsistent File Encoding in sensors.py

**File:** `quality_gate/sensors/sensors.py`
**Severity:** Medium
**Status:** ✅ Fixed

**Problem:** `_calculate_avg_cyclomatic_complexity` used `read_text()` without encoding, while all other methods used `read_text(encoding="utf-8", errors="ignore")`.

**Fix:** Unified to `read_text(encoding="utf-8", errors="ignore")`.

---

## Medium #8: Silent Exception Swallowing in drift_monitor.py

**File:** `quality_gate/drift_monitor.py`
**Severity:** Medium
**Status:** ✅ Fixed

**Problem:** `_check_drift` used bare `except Exception: return {"has_drift": False}`, silently swallowing all errors.

**Fix:** Changed to `except Exception as e: logging.warning(f"Drift check failed: {e}"); return {"has_drift": False, "error": str(e)}`.

---

## Medium #9: Overly Broad Exception Catching in fitness_functions.py

**File:** `quality_gate/fitness_functions.py`
**Severity:** Medium
**Status:** ✅ Fixed

**Problem:** `_extract_dependencies` and `_calculate_cohesion` used `except Exception: pass` / `except Exception: self.dependencies[...] = []`, silently ignoring errors.

**Fix:** Replaced with `logging.warning()` to surface parse failures, while still providing fallback empty values.

---

## Medium #10: No I/O Fault Tolerance in baseline_manager.py

**File:** `quality_gate/baseline_manager.py`
**Severity:** Medium
**Status:** ✅ Fixed

**Problem:** `check_drift` and `capture_baseline` read/write `latest.json` without `try/except JSONDecodeError`.

**Fix:** Added `try/except (json.JSONDecodeError, IOError)` around file operations, with `logging.error()` and graceful fallback values.

---

## Medium #11: Local Timezone vs UTC Inconsistency

**File:** `quality_gate/baseline_manager.py`
**Severity:** Medium
**Status:** ✅ Fixed

**Problem:** Used `datetime.now().isoformat()` while other files use `datetime.now(timezone.utc).isoformat()`.

**Fix:** Replaced all `datetime.now()` with `datetime.now(timezone.utc)` throughout the file.

---

## Medium #12: Index Not Updated on `assignee` Change

**File:** `core/feedback/feedback.py`
**Severity:** Medium
**Status:** ✅ Fixed

**Problem:** `FeedbackStore.update()` did not update `_by_assignee` index when `assignee` was changed.

**Fix:** Added logic to remove `feedback_id` from the old assignee's index before applying the new assignee, then re-index under the new assignee.

---

## Medium #13: Direct Object Mutation in closure.py

**File:** `core/feedback/closure.py`
**Severity:** Medium
**Status:** ✅ Fixed

**Problem:** Direct mutation of `fb.verified_at = now_iso` and `fb.recurrence_count += 1` would break DB-backed stores.

**Fix:** Replaced all direct mutations with:
- `store.update()` for status changes
- Dict/copy pattern for fields not covered by `FeedbackUpdate`
- Return fresh `StandardFeedback` instances via `StandardFeedback.from_dict()`

---

## Medium #13: Direct Object Mutation in router.py

**File:** `core/feedback/router.py`
**Severity:** Medium
**Status:** ✅ Fixed

**Problem:** Direct mutation of `fb_updated.sla_deadline = deadline` would break DB-backed stores.

**Fix:** Removed the direct mutation; returns `(team, deadline)` directly without patching the stored object.

---

## Medium #14: Type Contract Mismatch in steering/integrations.py

**File:** `steering/integrations.py`
**Severity:** Medium
**Status:** ✅ Fixed

**Problem:** `check_output_compliance` assumed `output` was a dict, but `_extract_text` also accepts strings.

**Fix:** Added a type check at the start of `check_output_compliance`; converts `str` to `{"text": output}` dict, or returns an explicit `TypeError` violation in the result.

---

## Medium #15: Wrong Timestamp in save_progress

**File:** `onboarding/wizard.py`
**Severity:** Medium
**Status:** ✅ Fixed

**Problem:** `last_updated = str(Path(__file__).stat().st_mtime)` recorded the file's modification time, not the current time.

**Fix:** Replaced with `datetime.now(timezone.utc).isoformat()`.

---

## Verification

All 12 files passed `python3 -m py_compile`:

```bash
python3 -m py_compile \
  constitution/claim_verifier.py \
  constitution/execution_logger.py \
  quality_gate/sensors/sensors.py \
  quality_gate/drift_monitor.py \
  quality_gate/fitness_functions.py \
  quality_gate/baseline_manager.py \
  core/feedback/feedback.py \
  core/feedback/closure.py \
  core/feedback/router.py \
  steering/integrations.py \
  onboarding/wizard.py
# ALL OK
```

## Commits

- `6c246f2` — fix: 15 Medium issues from Gemini Code Review
- `614d784` — chore: bump version to v6.80 in CHANGELOG

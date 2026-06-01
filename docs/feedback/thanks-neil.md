# Thanks Neil Feedback

Status: draft feedback log for PR-based follow-up.

Rule for follow-up PRs:

- Tag each PR with the contributor name in the title or prefix.
- Use a short, explicit label such as `thanks-neil:` for changes tied to this feedback.

## Feedback from latest review

### 1. Search autocomplete is too loose

Observed on mobile search:

- Typing `water` is surfacing matches from inside other words instead of behaving like a direct, word-aware autocomplete.

Expected behavior:

- Keep the autocomplete inside the search box.
- Prefer the most likely full match for the typed string.
- Avoid noisy dropdown-style suggestions for this control.
- Make the search feel precise and frictionless.

### 2. MP card vote count saturates too early

Observed on MP profile cards:

- Vote totals cap at `100` even when the MP has more than 100 recorded votes available.

Expected behavior:

- The card should not flatten the data at 100 if the underlying record contains more votes.
- Preserve the real count or state clearly that the card is showing a subset of the available record.

## Submission note

This feedback is best handled as a small follow-up PR so the fix can be reviewed and attributed clearly to the contributor who raised it.

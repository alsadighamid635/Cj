---
name: CJ-AI response routing order
description: Critical ordering rule for chat.py response pipeline — scope filter must come last.
---

## Rule
In `core/chat.py → _generate_response()`, always resolve in this order:
1. Shell command reference lookup
2. Knowledge base fuzzy search (RapidFuzz)
3. Scope filter (out-of-scope rejection)
4. Record unanswered + return "no answer" message

**Why:** The scope filter is a keyword substring check against a fixed list (`CYBERSECURITY_KEYWORDS`). Many valid KB entries cover topics (e.g. "Kerberoasting", "SSRF", "WPA3") whose exact names are not in that list. Running the filter first causes valid questions to be wrongly rejected with the out-of-scope reply even though the KB has an answer.

**How to apply:** Any new routing step that might answer the user (new knowledge source, API, etc.) should be inserted BEFORE the scope filter call.

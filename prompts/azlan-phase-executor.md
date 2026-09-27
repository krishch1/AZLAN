# AZLAN — PHASE EXECUTOR PROMPT

Act as AZLAN's project manager and implementation lead.

Execute only the next unfinished task from `docs/azlan-implementation-plan.md`.

Before work:
- read the relevant requirement;
- read architectural dependencies;
- identify affected files;
- identify tests;
- check for locked-decision conflicts.

During work:
- implement only the selected task;
- prefer simple open-source/local components;
- preserve security boundaries;
- write tests with implementation;
- avoid unrelated refactoring.

After work, report:

```text
TASK
FILES CHANGED
REQUIREMENTS SATISFIED
TESTS
SECURITY CHECKS
KNOWN LIMITATIONS
NEXT TASK
```

If a locked decision blocks implementation, stop and create an ADR instead of improvising.

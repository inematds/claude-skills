---
name: sessionend
description: End-of-session ritual — reflects on what happened, stores a structured session summary to Shared Brain, and updates local memory. Use when the user types /sessionend or says they're done for the session, wrapping up, or signing off.
---

# Session End

A closing ritual that turns each session into institutional memory. The goal is two things: (1) make sure nothing important gets lost between sessions, and (2) build an honest record of what's working and what isn't so we can improve over time.

---

## Step 1 — Gather Session Artifacts

Run these to understand what actually happened:

```bash
git -C $(pwd) log --oneline --since="8 hours ago" 2>/dev/null || true
git -C $(pwd) diff HEAD~1 --stat 2>/dev/null || true
git -C $(pwd) status 2>/dev/null || true
```

Also review the conversation history in your context — what was asked, what tools were used, what succeeded, what had to be retried.

---

## Step 2 — Reflect Honestly

Before storing anything, think through the session critically. Don't just summarize — evaluate.

**What went well?**
- Problems solved cleanly on the first try
- Tools used effectively
- Good decisions made quickly
- User got what they needed without friction

**What went wrong or poorly?**
- Wrong approaches tried before finding the right one
- Misunderstandings that needed correction
- Repeated tool calls, retries, or backtracking
- Things that took longer than they should have
- User had to correct me or redirect me

**How could this session have gone better?**
- What would I do differently if I started over?
- Are there patterns worth changing (how I approach certain tasks, which tools I reach for first, how I ask clarifying questions)?
- Any workflow or tooling improvements that would help future sessions?

Be specific. "Everything went fine" is not a useful reflection. If something was suboptimal, name it.

---

## Step 3 — Store to Shared Brain

Call `brain_store` with a structured session summary. Use this format:

```
topic: session-reflection/{project-name}/{YYYY-MM-DD}

content:
## Session: {project} — {date}

### What was accomplished
- {bullet list of concrete outcomes}

### What went well
- {specific things that worked}

### What went wrong
- {honest account of friction, errors, wrong turns}

### How to improve
- {actionable changes for future sessions}

### Cross-agent relevant
- {anything Morpheus, n8n, or other agents should know}
- (omit section if nothing applies)
```

---

## Step 4 — Update Local Memory

Check if the session revealed anything worth persisting in `Default_memory_path`:

- New user preferences or feedback → update `feedback_*.md`
- New project facts → update or create `project_*.md`
- New information about the user → update `user_*.md`
- New external resource pointers → update `reference_*.md`

Update `MEMORY.md` index if any files were added or changed.

Only update memory if there's something genuinely new. Don't re-save things already captured.

---

## Step 5 — Output Summary

End with a short plaintext summary to the user:

```
Session wrapped up.

Stored to Shared Brain: session-reflection/{project}/{date}

Accomplished: {1-2 sentence summary}
Went well: {1-2 things}
Could improve: {1-2 things}
Memory updated: {yes/no — what changed}
```

Keep it brief. The user is signing off — they don't need a wall of text.

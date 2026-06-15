---
name: vibe-coding
description: Troubleshoots frontend layout, CSS, and DOM issues by prioritizing live browser visual feedback before hardcoding. Use when the user wants to test CSS/HTML changes, fix cut-off elements, or adjust layouts visually.
---

# Vibe Coding

> 🏆 **Special Thanks & Acknowledgement**
> A massive thank you to **@kem-tossoun-1511** for taking the time to thoroughly test this skill, providing incredibly detailed feedback offline, and helping overhaul the Git workflow and terminology to align with software engineering best practices!

> ⚠️ **Platform Disclaimer (Claude Code / Other Agents)**
> *This skill was originally designed and tested in Google Antigravity.*
> There are specific tools referenced in this document that may not exist in Claude Code or other agents, which can lead to tool hallucinations. Examples include:
> - `notify_user` with `BlockedOnUser=true` (designed to force a hard stop for user input)
> - `browser_subagent` (designed to spin up a visible browser session)
> If you are using this skill in Claude Skills 2.0 or another environment, please bear this in mind. It is highly recommended to run an evaluation first and substitute these instructions with your agent's equivalent native tools for web inspection and user confirmation.

## Changelog
* **v1.1.0 (Current)**: 
  * Refactored Git flow to **Branch-First** (creates a secure sandbox local branch immediately before work begins).
  * Removed dangerous "hardcode" terminology, replacing it with "persist to source".
  * Simplified browser iteration by removing the over-engineered `/tmp` injection log logic.
  * Added platform tool disclaimers.

> **CRITICAL SYSTEM DIRECTIVE:**
> **UNDER NO CIRCUMSTANCES are you to edit ANY local repository files (like `.css`, `.scss`, `.jsx`, `.html`) immediately upon reading the user's request.**
> **You MUST complete the "Live Troubleshooting" step and gain explicit visual approval from the user BEFORE making any permanent edits to the source code. Your first action should be opening the target URL, NOT editing a file.**

> [!TIP] **Performance Recommendation**
> This skill involves heavy use of browser subagents, screenshots, and iterative live testing. **For significantly faster results, switch your agent mode from "Planning" to "Fast" before starting.** At the very beginning of the workflow, notify the user:
> *"⚡ **Heads up:** Vibe Coding works best in **Fast** mode. If your agent is set to **Planning**, consider switching to **Fast** for a much quicker experience."*

> [!WARNING] **Workspace Confirmation**
> Before doing ANY work, you MUST confirm the active workspace with the user. Detect the current working directory / active workspace and notify the user:
> *"📂 **Repo check:** I'm currently working in `[DETECTED WORKSPACE PATH]`. Is this the correct repository for this vibe session, or should we switch?"*
> **HARD STOP**: Use the `notify_user` tool with `BlockedOnUser=true` to present this confirmation. **DO NOT proceed** with any git commands, browser sessions, or file operations until the user explicitly confirms the workspace is correct.

## When to use this skill
- The user reports a visual bug, hidden element, or layout issue.
- The user wants to experiment with CSS or DOM changes live.
- The user explicitly asks to "vibe code", "live test", or "use the developer browser".

## Workflow
- [ ] **Confirm Workspace**:
  - Detect the current active workspace path.
  - Notify the user of the detected workspace and ask for explicit confirmation (see **Workspace Confirmation** alert above).
  - If the user says the workspace is wrong, **stop immediately** and instruct them to reopen the correct project before re-triggering the workflow.
- [ ] **Safety Check & Sandbox Branch**: 
  - Verify the current `git status` of the repository.
  - If there are uncommitted changes, pause and ask the user: *"I see uncommitted work. Do you want me to commit this locally as a backup before we begin?"*
  - Once the workspace is clean (or backup is approved/skipped), ask the user for a short description of the task.
  - **IMMEDIATELY** create and switch to a new local branch: `git checkout -b vibe/[short-description]`. This creates a safe local sandbox for editing BEFORE you start analyzing or opening the browser.
- [ ] **Establish Target Environment & Browser Subagent (VISIBLE)**:
  - Identify the target URL provided by the user. This could be a local dev server (e.g., `http://localhost:3000`) OR an actual hosted staging/production URL (e.g., `https://example.com/page`).
  - If the target is local, start the local development server (e.g., `npm run dev`, `yarn start`) using the `run_command` tool in the background. If the target is a hosted URL, skip the dev server step.
  - Dispatch a `browser_subagent` to open the target URL.
  - **CRITICAL**: You must instruct the `browser_subagent` to run the browser visibly on the user's screen (e.g., disable headless mode) so the user can watch the automation happen live.
  - Use the subagent to actively inspect the DOM (saving the user from having to copy/paste HTML) and take screenshots to confirm the bug.
- [ ] **Live Troubleshooting & Validation Loop**:
  - **Do NOT edit the repository files yet.**
  - Use the subagent to inject JavaScript or manipulate styles in its live browser session to test possible fixes.
  - Take screenshots of your proposed fixes in the subagent's browser and show them to the user.
  - Alternatively, generate vanilla JavaScript snippets for the user to inject into their own browser's Developer Tools Console.
  - **SESSION RECOVERY**: If the browser is refreshed (accidentally or otherwise) and the live injections are lost, simply re-inspect the DOM and re-apply the CSS/JS. Do not use complex scratch files or injection logs.
  - **HARD STOP #1 — VISUAL APPROVAL**: Once you have suggested/injected a fix, you MUST pause execution. Use the `notify_user` tool with `BlockedOnUser=true` to ask the user: "How does this look? Do you want to iterate further on the design, or are we ready to move to the codebase strategy?"
  - **DO NOT proceed** to strategizing or persisting until the user explicitly says "Yes, let's persist this to source." If they say "No" or give feedback, iterate on the live CSS/JS again.
  - **GATE RULE**: User approval here ONLY grants permission to move to the **Strategy** step. It does NOT grant permission to apply code. These are separate gates.
- [ ] **Strategize Codebase Edits** *(STRATEGY ONLY — NO CODE CHANGES)*:
  - Once the user explicitly approves the visual fix on the screen, **stop editing the live browser**.
  - Evaluate the exact DOM adjustments or CSS properties that successfully solved the issue.
  - Search the repository (e.g., using `grep_search`) to locate the source definitions of those elements.
  - Formulate an efficient, best-practice strategy for the repository (e.g., Should this go in a global `_overrides.scss` file? Should it update a nested React component? Is it a Tailwind utility class?).
  - **HARD STOP #2 — STRATEGY APPROVAL**: Use the `notify_user` tool with `BlockedOnUser=true` to present the implementation strategy and *why* this approach is the most robust. Ask the user for explicit approval to proceed with editing the codebase.
  - **DO NOT proceed** to applying code until the user explicitly approves the strategy. Do NOT ask for the remote repository destination at this stage — that comes later.
  - ⛔ **ANTI-MERGE RULE**: You are STRICTLY FORBIDDEN from combining the Strategy and Apply steps into "one go." You may NOT say things like "I'll outline the strategy and apply it in one go" or "Since you approved, I'll go ahead and apply the changes." Each step requires its own separate, explicit user approval. Presenting a strategy and applying code in the same response is a VIOLATION of this workflow. If you catch yourself about to combine them — STOP.
- [ ] **Persist to Source Code** *(ONLY after strategy is explicitly approved)*:
  - Translate the temporary browser-side injection into clean, permanent source code changes based on the approved strategy.
  - Clean up any temporary utility classes, console logs, or hacky styles used during live testing.
  - ⛔ **NO TERMINAL COMMANDS YET**: You are STRICTLY FORBIDDEN from running ANY terminal commands (`run_command`) during this step. Do NOT run compilation scripts (like `npm`, `grunt`, `npx`). Do NOT run ANY `git` commands (no `git diff`, no `git add`). You must ONLY edit the code files using your file editing tools and save them.
  - ⛔ **NO REVERTS**: If a compiler or linter is running in the background and throws errors, DO NOT panic and revert your changes (e.g. `git checkout -- file`). Leave the files alone. The user will handle compilation.
  - **HARD STOP #3 — CODE REVIEW**: After saving the file changes, you MUST pause immediately. Use the `notify_user` tool with `BlockedOnUser=true` to tell the user: "I've applied the source code changes to your local branch. Please review the Diff in your VS Code Source Control panel and check it in your browser before we push."
  - **DO NOT** self-verify using a browser subagent and **DO NOT** execute any terminal commands. The USER decides if the code is good by checking it locally — not you. Since it is on a dedicated local branch, if the code needs more work, you can keep iterating here safely without affecting the main codebase.
  - ⛔ **ANTI-STEAMROLL RULE**: You may NOT combine applying code with verifying and pushing. Applying code and then running `git commit` or saying "everything looks good, ready to push" in the same response is a VIOLATION. Stop after editing the files. Wait for the user.
- [ ] **Push Live** *(ONLY after user confirms the applied changes are correct)*:
  - ⛔ **NO GIT COMMANDS UNTIL APPROVED**: You are strictly forbidden from running ANY git commands (e.g., `git stash`, `git commit`) BEFORE you have received explicit user approval at Hard Stop #4.
  - **TARGET REPO SETUP**: Ask the user for the target destination remote name (e.g., `origin`) where this branch should be pushed.
  - **HARD STOP #4 — PUSH APPROVAL**: Use the `notify_user` tool with `BlockedOnUser=true` to present the following:
    1. "Ready to commit and push live?"
    2. "Please provide the target repository URL or remote name (e.g. `origin`) where this branch should be pushed."
  - **DO NOT run any git commands** until the user has provided the repository URL/name.
  - ⛔ **ONE BRANCH PER FIX**: Every push MUST be on its own **new, dedicated branch** (which you created at the start). Never push to `main` or `master` directly.
  - ⚠️ **POWERSHELL COMPATIBILITY**: The user's shell is **PowerShell** (Windows). The `&&` operator is a bash/Unix convention and is NOT supported in Windows. **NEVER chain git commands with `&&`**. Instead, once approved, run each git command as a **separate `run_command` call**, one at a time:
    1. `git add .`
    2. `git commit -m "Fix: [short description]"`
    3. `git push [USER_PROVIDED_REPO] vibe/[branch-name]`
- [ ] **Session Close** *(mandatory — no exceptions)*:
  - After a successful push, the vibe coding session is **COMPLETE**. Notify the user:
  - *"✅ **Vibe session complete!** Your fix has been pushed to `vibe/[branch-name]`. To avoid context bleed between tasks, please start a **fresh new chat** for your next vibe session. See you there! 🎯"*
  - ⛔ **DO NOT** accept another vibe coding task in the same chat. If the user asks to fix something else, remind them: *"For best results, let's start a fresh chat so we have a clean slate. This prevents branch conflicts and context issues from the previous fix."*
  - **Scope Limitation**: If the user asks for new architecture (e.g., adding a database schema) during a vibe session, gently remind them that Vibe Coding is for frontend layout and visual issues, and recommend a standard `plan` or `task` strategy.

## Instructions

### Live Testing Constraints
- **Feedback Dependence**: The live testing phase MUST rely on the user visually confirming the edits in their dev browser. Make a change, sync with the user, and repeat.
- **Aspect Ratios**: When dealing with video iframes or nested modals, remember that intrinsic ratio hacks (`padding-bottom`) constrain height based on width. Shrink the `max-width` of the padding container to effectively shrink the vertical footprint.

### Validation Loop
- **Plan**: Identify the wrapper or element causing the visual overflow/bug.
- **Validate**: Apply the CSS/DOM fix to the code and ask the user "How does that look on your end?". If it doesn't work, revert and try a different approach.
- **Execute**: Once visually approved by the user, finalize the fix cleanly.

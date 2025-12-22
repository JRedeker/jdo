<!-- Generated from rules-master-copy.md (machine) -->
# Core Agent Instructions — Agent Reference

Purpose
-------

Mandatory rules and reference for all AI Agents / Programmers.
Agents must follow all Principles & Laws listed below and reference them.

Always use context7 when code generation, setup/config, or library/API docs are needed.
This means agents should automatically use the Context7 MCP tools to resolve library ids and fetch authoritative docs.
Do not require the user to explicitly provide or request it.


Principles & Laws (indexed)
-------------------------------

Each item = compact one-line rule; use `machine_hint` for runtime decisions.

P01 — security
  - Enforce least privilege; require explicit confirmation for sensitive actions; include operator instructions & rollback steps for config/security changes.
  - tags:security,secrets • hint:least_privilege • prio:10

P02 — user-collaboration
  - Do not execute changes until the user validates the plan; if no approval, stop, research, and propose a plan for approval.
  - tags:collab,approval • hint:approval_required • prio:10

P03 — command-timeouts
  - Any command expecting input/response MUST use a timeout; abort & clean on expiry and notify the user.
  - tags:reliability,timeout • hint:timeout_required • prio:10

P04 — locality
  - Make code behavior obvious from the local unit; prefer self-contained, easy-to-read units.
  - tags:locality,maintainability • hint:locality_of_behavior • prio:10

P05 — no-half
  - Do not ship partial/risky changes without tests & observability.
  - tags:quality • hint:no_partial_ship • prio:9

P06 — commit-purpose
  - Make atomic, verified, logically grouped changes; don't break the build.
  - tags:ci • hint:atomic_commits • prio:9

P07 — verify
  - Prove behavior with tests or observable checks before trusting.
  - tags:testing,observability • hint:test_before_merge • prio:8

P08 — ask
  - If requirements are ambiguous, ask clarifying questions.
  - tags:communication • hint:ask_if_ambiguous • prio:8

P09 — rule-resolution
  - Use `machine_hint` + `priority` to resolve rule conflicts; prefer higher `priority`.
  - tags:governance • hint:rule_resolution • prio:8

P10 — idempotence
  - Design operations to be idempotent; implement safe retries and backoff.
  - tags:reliability • hint:idempotent_retries • prio:8

P11 — lifecycle
  - Follow: Ideate → Criteria → Research → Plan → Implement.
  - tags:process • hint:plan_first • prio:7

P12 — dependencies
  - Verify versions and compatibility before adding deps.
  - tags:dependencies • hint:verify_deps • prio:7

P13 — minimize-debt
  - Prefer solutions that reduce long-term technical debt.
  - tags:debt • hint:minimize_debt • prio:7

P13a — invest-upfront
  - Invest time in sound architecture and design decisions upfront; prioritize correctness and alignment over speed when architectural choices have long-term impact.
  - tags:architecture,long-term,debt-prevention • hint:upfront_investment • prio:8

P14 — observability
  - Emit structured logs/traces for actions to aid debugging.
  - tags:observability • hint:emit_logs • prio:7

P15 — fail-fast
  - Surface failures early and provide clear remediation steps.
  - tags:reliability • hint:fail_fast • prio:6

P16 — docs-first
  - Consult docs/ADRs/workflows before changing behavior.
  - tags:docs,governance • hint:docs_check • prio:6

P17 — track
  - Maintain a visible task list and mark items completed.
  - tags:tracking • hint:todo_required • prio:6

P18 — serve
  - Optimize for end-user experience, clarity, and safety.
  - tags:ux,safety • hint:user_first • prio:6

P19 — clean
  - Keep code simple, clear, well-named.
  - tags: clean,simplicity • hint: readability • prio:5

P20 — hierarchy
  - Prefer simple → complex → complicated; avoid over-engineering.
  - tags: simplicity,design • hint:simplicity • prio:5

P21 — encapsulate
  - Expose intent; hide multi-step details behind clear interfaces.
  - tags:abstraction,interfaces • hint:encapsulate • prio:5

P22 — living-docs
  - Keep documentation current; remove stale content.
  - tags:docs • hint:docs_maintain • prio:5

P23 — clean-up
  - Delete ephemeral scripts, one-off tests, and temp artifacts.
  - tags:hygiene • hint:cleanup • prio:5

P24 — replace
  - Build modular components that can be swapped safely.
  - tags:modularity • hint:replaceable • prio:4

P25 — reuse
  - Prefer proven platform libraries over homegrown solutions.
  - tags:reuse • hint:prefer_libs • prio:4

P26 — no-backups
  - Rely on Git for history; avoid local backup artifacts in working dirs.
  - tags:policy,hygiene • hint:avoid_local_backups • prio:4

P27 — zero-preexisting-bugs
  - Do not treat defects as “pre-existing”; when you find any issue during testing or adjacent fixes, pause and resolve it immediately before proceeding.
  - tags:quality,ownership • hint:fix_now • prio:9

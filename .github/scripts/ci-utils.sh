#!/usr/bin/env bash
# CI utility functions using gum for beautiful output
# Source this file: source .github/scripts/ci-utils.sh

set -eo pipefail

# Colors (ANSI 256)
_BLUE=212 _GREEN=82 _RED=196 _ORANGE=208 _YELLOW=220 _PURPLE=141 _CYAN=75 _GRAY=240

# Core display functions (internal)
_header() { gum style --border double --border-foreground "$_BLUE" --padding "1 2" "$@"; }
_success() { gum style --border double --border-foreground "$_GREEN" --padding "1 2" "$@"; }
_error() { gum style --border double --border-foreground "$_RED" --padding "1 2" "$@"; }
_warn() { gum style --border double --border-foreground "$_ORANGE" --padding "1 2" "$@"; }
_critical() { gum style --border thick --border-foreground "$_RED" --padding "1 2" "$@"; }
_high() { gum style --border thick --border-foreground "$_ORANGE" --padding "1 2" "$@"; }
_medium() { gum style --border normal --border-foreground "$_CYAN" --padding "1 2" "$@"; }
_low() { gum style --border normal --border-foreground "$_YELLOW" --padding "1 2" "$@"; }
_section() { local c="$1"; shift; gum style --border double --border-foreground "$c" --padding "1 2" "$@"; }

# =============================================================================
# CI CHECK FUNCTIONS - Just call these, output is automatic
# =============================================================================

ci_lint() {
  _header "🔍 LINT"
  if ! uv run ruff format --check src/ tests/; then
    _error "❌ FORMAT FAILED" "" "Run: uv run ruff format src/ tests/"
    return 1
  fi
  if ! uv run ruff check src/ tests/; then
    _error "❌ LINT FAILED" "" "Run: uv run ruff check --fix src/ tests/"
    return 1
  fi
  _success "✅ LINT PASSED"
}

ci_typecheck() {
  _header "🔬 TYPE CHECK"
  if ! uvx pyrefly check; then
    _error "❌ TYPE ERROR" "" "Run: uvx pyrefly check src/"
    return 1
  fi
  _success "✅ TYPES PASSED"
}

ci_complexity() {
  _header "📊 COMPLEXITY" "" "CCN ≤ 10 | NLOC ≤ 50 | Params ≤ 6"
  if ! uv run lizard src/ -C 10 -L 50 -a 6 -w; then
    _warn "⚠️ COMPLEXITY WARNING" "" "Some functions exceed thresholds"
    return 1
  fi
  _success "✅ COMPLEXITY PASSED"
}

ci_test() {
  _header "🧪 TESTS"
  if ! uv run pytest --tb=short -q; then
    _error "❌ TESTS FAILED" "" "Run: uv run pytest -v"
    return 1
  fi
  _success "✅ TESTS PASSED"
}

ci_review() {
  local pr_number="$1" pr_title="$2" pr_author="$3" head_ref="$4" base_ref="$5"

  local changed file_count additions deletions stats
  changed=$(git diff --name-only origin/${base_ref}...HEAD | grep -E '\.(py|md|yml|yaml|toml)$' || true)
  file_count=$(echo "$changed" | grep -c . || echo "0")
  stats=$(git diff --stat origin/${base_ref}...HEAD | tail -1)
  additions=$(echo "$stats" | grep -oE '[0-9]+ insertion' | grep -oE '[0-9]+' || echo "0")
  deletions=$(echo "$stats" | grep -oE '[0-9]+ deletion' | grep -oE '[0-9]+' || echo "0")

  _section 99 "🤖 AI CODE REVIEW" "" \
    "PR #${pr_number}: ${pr_title}" \
    "Branch: ${head_ref} → ${base_ref}" \
    "Author: ${pr_author}" "" \
    "Files: ${file_count} | +${additions} -${deletions}"

  echo ""
  if [ -n "$changed" ]; then
    echo "$changed" | while read -r file; do echo "  • $file"; done
  fi

  _critical "🚨 CRITICAL (P01-P04) — Blocks merge" "" \
    "☐ No hardcoded secrets/credentials" \
    "☐ Least privilege enforced" \
    "☐ Commands have timeouts" \
    "☐ Behavior obvious from local context"

  _high "⚠️ HIGH (P05-P06) — Should fix" "" \
    "☐ No partial changes without tests" \
    "☐ Atomic, logically grouped commits"

  _medium "📋 MEDIUM (P07-P14)" "" \
    "☐ Tests for new behavior" \
    "☐ Dependencies verified" \
    "☐ Reduces technical debt" \
    "☐ Structured logs/traces"

  _low "💡 STANDARD (P15-P26)" "" \
    "☐ Fails fast with clear errors" \
    "☐ Simple, clear, well-named" \
    "☐ Docs current"

  _high "🐍 PROJECT RULES" "" \
    "☐ No # noqa or # type: ignore" \
    "☐ All functions typed" \
    "☐ ClassVar for mutable class attrs" \
    "☐ No bare except:" \
    "☐ Exception msgs in variables"

  _section 141 "📝 REPORT FORMAT" "" \
    "### [SEVERITY] P## — file:line" \
    "**Issue:** Description" \
    "**Fix:** Suggestion" "" \
    "🚨 BLOCKING | ⚠️ MAJOR | 📋 MINOR | 💡 SUGGEST" "" \
    "Verdict: ✅ APPROVE | ❌ REQUEST_CHANGES | 💬 COMMENT"

  _section 99 "📄 DIFF"
  git diff origin/${base_ref}...HEAD -- '*.py' '*.md' '*.yml' '*.yaml' '*.toml' | head -c 50000
  _section 99 "📄 END"
}

# =============================================================================
# INSTALL HELPER
# =============================================================================

ci_install_gum() {
  if command -v gum &> /dev/null; then return 0; fi
  sudo mkdir -p /etc/apt/keyrings
  curl -fsSL https://repo.charm.sh/apt/gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/charm.gpg
  echo "deb [signed-by=/etc/apt/keyrings/charm.gpg] https://repo.charm.sh/apt/ * *" | sudo tee /etc/apt/sources.list.d/charm.list
  sudo apt update && sudo apt install -y gum
}

# AI Analysis, Free Providers and Company Profile: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Editable company profile in the app, structured AI country analysis and comparison insight generated with a free provider (Gemini or Groq), and a redesigned PDF that combines new charts with the AI sections.

**Architecture:**
- New backend modules: `app/ai/` (provider adapters over the OpenAI-compatible chat API), `app/analysis/` (prompts, structured content, guard, storage, routes; replaces `app/explanation/`) and `app/profile/store.py` + `routes.py` (profile overrides in SQLite).
- `deps.get_profile` returns the *effective* profile, so scoring, prompts and the PDF all follow edits automatically.
- Frontend: a new `features/company` and `features/analysis`, replacing `features/explanation`.
- Same vertical-slice, TDD and PR workflow as the first plan.

**Tech Stack:** unchanged (FastAPI, httpx2, SQLite, fpdf2, matplotlib; React, TanStack Query, Recharts, Vitest).

**Spec:** `docs/specs/2026-11-01-ai-analysis-and-company-profile-design.md`. Read it first; it builds on `docs/specs/2026-10-25-cage-market-accessibility-design.md`.

## Global Constraints

- Providers: **only Gemini and Groq**, called through their OpenAI-compatible chat endpoints with httpx2, no provider SDK.
  - Gemini: `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions`, default model `gemini-3.8-flash`.
  - Groq: `https://api.groq.com/openai/v1/chat/completions`, default model `openai/gpt-oss-120b`.
  - Auth: `Authorization: Bearer <key>`.
- Settings: `GEMINI_API_KEY`, `GEMINI_MODEL`, `GROQ_API_KEY`, `GROQ_MODEL` replace `LLM_PROVIDER`, `LLM_API_KEY` and `LLM_MODEL`. A provider is available iff its key is set.
- Time budget: **30 s timeout per AI call, at most two calls per request** (one retry, whatever the reason).
- Error messages are exactly the spec §5 table; the 429 message names the provider and, if another provider is available, suggests it.
- Every text field of AI content passes the numbers guard. The prompt allows digits only for numbers in DATA, with timeframes in words.
- Exporting the PDF and loading any page **never call the AI**.
- Profile edits live in SQLite, never in files or git. Editable fields:
  - `name`: 1–120 chars;
  - `description`: ≤ 4,000 chars;
  - `supported_languages` ⊆ `en, es, pt, fr, de, it`, non-empty;
  - `channels` ⊆ `sms, email, whatsapp`, non-empty.
- One saved analysis per subject. Comparison subject = sorted codes of the selected countries **that have data**; at least 2.
- Ranking order always comes from the real scores; AI ranking text is matched by `iso3`.
- Exact UI and PDF copy from spec §6–7, including:
  - "AI analysis not generated yet";
  - "Written before the latest data or company change.";
  - "Some numbers could not be verified; review before use.";
  - "AI analysis written by {Label} ({model}) on {YYYY-MM-DD}. Numbers checked against the data."
- Same workflow as the first plan: one branch per slice, `test(scope)` then `feat(scope)` commits, PR per slice merged with a merge commit after green CI, README and docs updated in the slice, and no test edited just to pass.

## Review Focus

1. **The free quota runs out mid-use (429):** the user sees the spec's quota message naming the other provider, and an already saved analysis stays visible. → Tasks 2.1 and 2.4.
2. **The model wraps its JSON in markdown fences** (```` ```json … ``` ````), which free models often do: it must parse, not count as unreadable. → Task 2.2.
3. **A long description with accents, quotes and newlines:** saved exactly, sent intact, and long AI text flows across PDF pages without overlapping. → Tasks 1.1 and 4.2.
4. **Editing the profile after analyses exist:** analyses are kept but marked outdated in the app and the PDF. → Tasks 2.3 and 4.2.
5. **Changing the comparison selection:** an insight is found again for the same countries in any order, but not for a different set. → Task 3.1.

---

## How every slice runs

Same as the first plan's "How every slice runs" section (branch from `main`, tasks in order, README/docs, PR, CI green, merge commit, delete branch, check "Done when").

---

## Slice 1 · `feat/company-profile`

**Done when:** on the Company page, adding Spanish and saving makes Colombia's C1 show 100 on the scorecard right away; Reset brings back the example profile.

### Task 1.1: Profile overrides, effective profile and API

**Files:**
- Create: `backend/app/profile/store.py`, `backend/app/profile/routes.py`
- Modify: `backend/app/deps.py` (`get_profile`), `backend/app/main.py`
- Test: `backend/tests/profile/test_store.py`, `backend/tests/profile/test_routes.py`

**Interfaces:**
- Produces:
  - `LANGUAGE_OPTIONS = ("en", "es", "pt", "fr", "de", "it")` and `CHANNEL_OPTIONS = ("sms", "email", "whatsapp")`.
  - pydantic `ProfileEdits{name: str, description: str, supported_languages: list[str], channels: list[str]}`. Validators: name stripped, 1–120 chars; description ≤ 4,000; lists non-empty, de-duplicated, within the options.
  - `ProfileStore(db_path)`: table `company_profile` with a single row (`id = 1`), lists stored as JSON. Methods: `get() -> ProfileEdits | None`, `save(edits: ProfileEdits) -> None`, `clear() -> None`.
  - `effective_profile(file_profile: CompanyProfile, edits: ProfileEdits | None) -> CompanyProfile` (`dataclasses.replace`; home fields always from the file).
  - `deps.get_profile` now returns `effective_profile(load_profile(config_dir), ProfileStore(db_path).get())`. `deps.get_profile_store()`.
  - Routes (session required):
    - `GET /api/profile` → `ProfileOut{name, description, supported_languages, channels, home_country, home_timezone, source: "saved"|"file", options: {languages, channels}}`;
    - `PUT /api/profile` (body `ProfileEdits`) → `ProfileOut`, 422 on validation;
    - `DELETE /api/profile` → `ProfileOut` from the file.

- [ ] **Step 1: Write the failing tests.**
  - Store:
    - `test_save_then_get_round_trips_unicode_and_newlines` (description `"Restaurantes en Bogotá – \"premium\"\nSegunda línea"` comes back identical) **(Review Focus 3)**;
    - `test_clear_removes_edits`;
    - `test_effective_profile_keeps_home_fields_from_file`;
    - `test_edits_validation` (parametrized: empty name, 121-char name, 4,001-char description, `[]` languages, `"xx"` language, `"fax"` channel → `ValidationError`; `["es","es"]` → `["es"]`).
  - Routes:
    - `test_get_profile_from_file_by_default` (`source == "file"`, options listed);
    - `test_put_saves_and_returns_saved_source`;
    - `test_put_invalid_returns_422_with_field`;
    - `test_saving_spanish_changes_colombia_c1_immediately` (seed COL evidence, PUT with `supported_languages=["en","es"]`, then `GET /api/countries/COL/scorecard` → C1 score 100);
    - `test_delete_resets_to_file`;
    - `test_profile_requires_session`.
- [ ] **Step 2:** `uv run pytest tests/profile -v` → FAIL (imports). Commit `test(profile): …`.
- [ ] **Step 3:** Implement the store, `effective_profile`, the deps change and the routes. The profile store shares the database file with the evidence store.
- [ ] **Step 4:** `uv run pytest -q && uv run ruff check .` → all pass.
- [ ] **Step 5:** Commit: `feat(profile): editable company profile stored in the database`.

### Task 1.2: Company page

**Files:**
- Create: `frontend/src/features/company/api.ts`, `CompanyPage.tsx`, `company.test.tsx`; shadcn `textarea`
- Modify: `frontend/src/App.tsx` (lazy route `/company`), `frontend/src/features/auth/AppShell.tsx` (nav link "Company"), `frontend/src/lib/types.ts` (`Profile`, `ProfileEdits`)

**Interfaces:**
- Consumes: Task 1.1 routes.
- Produces: `getProfile()`, `saveProfile(edits)` and `resetProfile()`. Saving or resetting invalidates `['profile']` and every `['scorecard', …]`, `['comparison', …]` and `['analysis', …]` query.

- [ ] **Step 1: Write the failing tests** (mock `./api`).
  - `shows the profile values and the read-only home country`.
  - `saving sends the edited fields and shows "Saved"` (type a new name, tick Spanish, click "Save" → `saveProfile` called with the name, `["en","es"]` and the channels).
  - `validation error from the server is shown next to the form` (reject `ApiError(422, …)` → message visible).
  - `reset asks for confirmation and restores the default profile`.
  - `at least one language and one channel must stay ticked` (Save disabled when none).
- [ ] **Step 2:** `npx vitest run src/features/company` → FAIL. Commit `test(company-ui): …`.
- [ ] **Step 3:** Implement the form:
  - labelled Name input and Description textarea, with a character counter `n/4000`;
  - checkbox groups from `options`;
  - home country and time zone as text, with the spec's note;
  - Save and Reset buttons (`window.confirm` for reset).
- [ ] **Step 4:** `npx vitest run && npm run lint && npm run build` → pass.
- [ ] **Step 5:** Commit: `feat(company-ui): company page to edit the profile`. Then a README section "Company profile" (`docs: …`).

---

## Slice 2 · `feat/ai-analysis`

**Done when:** with a free Gemini or Groq key in `backend/.env`, choosing the provider and clicking Generate on Colombia's scorecard shows the five sections and "written by …". Changing the company profile marks it outdated.

### Task 2.1: Settings and provider adapters

**Files:**
- Create: `backend/app/ai/__init__.py`, `backend/app/ai/providers.py`, `backend/app/ai/routes.py`
- Modify: `backend/app/settings.py`, `backend/app/deps.py`, `backend/app/main.py`, `backend/.env.example`, `deploy/.env.example`, `backend/tests/conftest.py` (new Settings fields)
- Delete: `backend/app/explanation/model.py` and `deps.get_explanation_model` (their role moves here)
- Modify: `backend/app/explanation/routes.py`: the old `POST …/explanation` no longer takes a model and always answers 503 `"AI is not configured"`, so the module keeps working until Task 2.3 deletes it (the slice merges as a whole)
- Test: `backend/tests/ai/test_providers.py`, `backend/tests/ai/test_routes.py`, `backend/tests/test_settings.py`

**Interfaces:**
- Produces:
  - `Settings` loses the `llm_*` fields and gains `gemini_api_key: str | None = None`, `gemini_model: str = "gemini-3.8-flash"`, `groq_api_key: str | None = None` and `groq_model: str = "openai/gpt-oss-120b"` (defaults, last in the dataclass).
  - `ProviderId = Literal["gemini", "groq"]`, `PROVIDER_LABELS = {"gemini": "Gemini", "groq": "Groq"}`, `PROVIDER_URLS` (the two URLs above).
  - `ProviderInfo{id, label, model}` and `available_providers(settings) -> list[ProviderInfo]` (Gemini first).
  - `class TextModel(Protocol): provider: ProviderId; model: str; def complete_json(self, prompt: str) -> str`.
  - `AIProviderError(status_code: int, detail: str)`.
  - `OpenAICompatibleModel(provider: ProviderId, model: str, api_key: str, client: httpx2.Client, alternative: ProviderId | None = None)`:
    - `complete_json` POSTs `{"model", "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}, "temperature": 0.3}` with a 30 s timeout;
    - returns `choices[0].message.content`;
    - maps errors per the spec table: 429 → `AIProviderError(429, "The free quota for Gemini is used up for now. Try again later or use Groq.")`, or `"… Try again later."` when there is no alternative; 401/403 → 502 `"The Gemini API key was rejected"`; timeout, network error or 5xx → 502 `"The AI service failed. Try again."`.
  - `deps.get_ai_models(settings) -> dict[ProviderId, TextModel]` (tests override it with fakes).
  - Route `GET /api/ai/providers` → `list[ProviderInfo]` (session required).

- [ ] **Step 1: Write the failing tests** (`httpx2.MockTransport`).
  - `test_available_providers_depend_on_keys` (none / gemini only / both).
  - `test_request_shape` (parametrized per provider: URL, `Authorization: Bearer k`, model, `response_format`).
  - `test_returns_message_content`.
  - `test_429_names_provider_and_suggests_alternative` and `test_429_without_alternative` **(Review Focus 1)**.
  - `test_401_maps_to_key_rejected`.
  - `test_timeout_maps_to_service_failed` (transport raises `httpx2.ReadTimeout`).
  - `test_500_maps_to_service_failed`.
  - `test_providers_route_lists_configured_models`.
  - `test_load_settings_reads_ai_keys_and_default_models`.
- [ ] **Step 2:** FAIL → commit `test(ai): …`.
- [ ] **Step 3:** Implement. Update both `.env.example` files: remove the `LLM_*` lines, add the four new variables with a comment on where to get free keys (Google AI Studio, Groq console).
- [ ] **Step 4:** Full backend suite → pass. Old explanation route tests that used a fake model are deleted here; their replacements arrive in 2.3.
- [ ] **Step 5:** Commit: `feat(ai): Gemini and Groq providers over the OpenAI-compatible API`.

### Task 2.2: Structured content, prompts and guarded generation

**Files:**
- Create: `backend/app/analysis/__init__.py`, `schema.py`, `prompt.py`, `generate.py`
- Move: `backend/app/explanation/guard.py` → `backend/app/analysis/guard.py` (`git mv`, imports updated); `backend/app/explanation/prompt.py` → its `data_block` becomes `country_data_block` in `analysis/prompt.py`
- Test: `backend/tests/analysis/test_schema.py`, `test_prompt.py`, `test_generate.py`, `test_guard.py` (moved)

**Interfaces:**
- Produces:
  - pydantic `CountryAnalysisContent{executive_summary: str, dimensions: DimensionTexts{Cultural, Administrative, Geographic, Economic: str}, barriers: list[str], opportunities: list[str], recommendation: str}`. Strings are non-empty after strip; lists are non-empty and **trimmed to the first 3**.
  - `ComparisonInsightContent{summary: str, ranking: list[RankingText{iso3: str, explanation: str}], key_differences: list[str]}`, with `key_differences` trimmed to 4.
  - `parse_content(raw: str, cls: type[T]) -> T | None`: strips a surrounding markdown code fence, then `json.loads` + `model_validate`; returns `None` on any failure.
  - `text_fields(content: BaseModel) -> list[str]`: every string inside the content.
  - `country_data_block(scorecard) -> str` (today's `data_block`, unchanged output) and `country_prompt(scorecard, profile) -> str`. The prompt includes the JSON shape, the word targets, `[ID]` citations, "Use digits only for numbers that appear in DATA; write timeframes and quantities in words", the company description and DATA.
  - `AnalysisUnreadable(Exception)`.
  - `generate_structured(model: TextModel, prompt: str, allowed: set[float], cls: type[T]) -> tuple[T, bool]` (content, flagged). At most two calls:

```
first = parse(call(prompt))
if first is None:
    second = parse(call(prompt + MALFORMED_NOTE))
    if second is None: raise AnalysisUnreadable
    return second, has_unsupported(second)
if not has_unsupported(first): return first, False
second = parse(call(prompt + numbers_note(unsupported)))
if second is None: return first, True          # keep the readable answer, flagged
return second, has_unsupported(second)
```

- [ ] **Step 1: Write the failing tests** (`FakeModel(replies)`, which has `provider` and `model` and records prompts).
  - Schema:
    - `test_lists_are_trimmed_to_three`;
    - `test_missing_dimension_key_is_invalid`;
    - `test_empty_list_is_invalid`;
    - `test_parse_strips_markdown_fence` (```` ```json\n{…}\n``` ```` parses) **(Review Focus 2)**;
    - `test_parse_returns_none_for_non_json`.
  - Prompt:
    - `test_country_prompt_contains_data_block_description_and_digit_rule`;
    - `test_country_data_block_unchanged_for_colombia` (A3 score 46).
  - Generate:
    - `test_clean_first_answer_one_call`;
    - `test_malformed_then_valid_two_calls`;
    - `test_malformed_twice_raises_unreadable`;
    - `test_unsupported_numbers_retry_clean_not_flagged` (2nd prompt lists the number);
    - `test_unsupported_numbers_twice_flagged`;
    - `test_unsupported_then_malformed_keeps_first_flagged`;
    - `test_guard_checks_every_field` (an invented "20%" only inside `barriers[1]` is caught).
- [ ] **Step 2:** FAIL → commit `test(analysis): …`.
- [ ] **Step 3:** Implement. `has_unsupported` = any `find_unsupported_numbers` over `text_fields`.
- [ ] **Step 4:** Full suite → pass.
- [ ] **Step 5:** Commit: `feat(analysis): structured AI content with guarded generation`.

### Task 2.3: Analysis storage, outdated detection and country analysis API

**Files:**
- Create: `backend/app/analysis/store.py`, `service.py`, `routes.py`
- Modify: `backend/app/deps.py` (`get_analysis_store`), `backend/app/main.py`, `backend/app/reports/routes.py` (temporarily pass no analyses; Task 4.2 wires them)
- Delete: `backend/app/explanation/` (cache, service, routes) and `backend/tests/explanation/`
- Test: `backend/tests/analysis/test_store.py`, `test_service.py`, `test_routes.py`

**Interfaces:**
- Produces:
  - `StoredAnalysis{kind: Literal["country", "comparison"], subject: str, cache_key: str, provider: ProviderId, model: str, content: dict, flagged: bool, created_at: str}`.
  - `AnalysisStore(db_path)`: table `analyses`, PK `(kind, subject)`; `DROP TABLE IF EXISTS explanations` on init. Methods: `get(kind, subject) -> StoredAnalysis | None` and `put(StoredAnalysis) -> None` (replaces).
  - `analysis_key(payload_json: str, profile: CompanyProfile) -> str` (sha256 of payload + `profile_hash`).
  - Response model `CountryAnalysis{iso3, provider, provider_label, model, created_at, flagged, outdated, content: CountryAnalysisContent}`.
  - `generate_country_analysis(scorecard, profile, model: TextModel, store) -> CountryAnalysis` (always generates and replaces) and `get_country_analysis(scorecard, profile, store) -> CountryAnalysis | None` (`outdated` = stored key ≠ current key).
  - Routes:
    - `GET /api/countries/{iso3}/analysis` → `CountryAnalysis` or 404 `"No AI analysis yet"`;
    - `POST /api/countries/{iso3}/analysis`, body `{provider}`:
      - no providers available → 503 `"AI is not configured"`;
      - provider not available → 400 `"This AI is not configured"`;
      - `AIProviderError` → its status and detail;
      - `AnalysisUnreadable` → 502 `"The AI returned an unreadable answer. Try again."`;
      - unknown country 404; no data 409.
  - `load_scorecard` moves from `explanation/routes.py` to `analysis/routes.py` (the reports routes import it from there).

- [ ] **Step 1: Write the failing tests.**
  - Store: `test_put_replaces_previous_subject`; `test_old_explanations_table_is_dropped`.
  - Service:
    - `test_generate_saves_provider_model_and_content`;
    - `test_regenerating_with_other_provider_replaces`;
    - `test_outdated_after_data_change`;
    - `test_outdated_after_profile_change` (analysis kept, `outdated=True`) **(Review Focus 4)**;
    - `test_not_outdated_when_nothing_changed`.
  - Routes (override `get_ai_models` with a fake):
    - `test_post_then_get`;
    - `test_get_without_analysis_404`;
    - `test_unknown_provider_400`;
    - `test_no_providers_503`;
    - `test_quota_error_passes_429_and_message`;
    - `test_unreadable_502`;
    - `test_analysis_requires_session`.
- [ ] **Step 2:** FAIL → commit `test(analysis): …`.
- [ ] **Step 3:** Implement and delete the old explanation module and tests.
- [ ] **Step 4:** Full suite → pass (157 minus removed plus new).
- [ ] **Step 5:** Commit: `feat(analysis): store country analyses and expose the analysis API`.

### Task 2.4: AI analysis panel

**Files:**
- Create: `frontend/src/features/analysis/api.ts`, `ProviderSelect.tsx`, `AnalysisPanel.tsx`, `analysis.test.tsx`
- Modify: `frontend/src/features/scorecard/ScorecardPage.tsx` (use `AnalysisPanel`), `scorecard.test.tsx` (mock the new api), `frontend/src/lib/types.ts`
- Delete: `frontend/src/features/explanation/`

**Interfaces:**
- Produces:
  - `getProviders()`;
  - `getCountryAnalysis(iso3) -> CountryAnalysis | null` (404 → null);
  - `generateCountryAnalysis(iso3, provider)`;
  - `ProviderSelect({providers, value, onChange})`, a labelled native select "AI provider", reused in Task 3.2;
  - `AnalysisPanel({iso3})`.

- [ ] **Step 1: Write the failing tests.**
  - `no providers shows "AI is not configured" and no Generate button`.
  - `shows saved analysis sections and attribution` ("Executive summary", the four dimension headings, "Barriers", "Opportunities", "Recommendation", and "Written by Gemini (gemini-3.8-flash) on 2026-11-01").
  - `generate uses the chosen provider` (select Groq → `generateCountryAnalysis('COL', 'groq')`).
  - `flagged shows the review warning`.
  - `outdated shows the badge` ("Written before the latest data or company change. Generate again to update.").
  - `quota error keeps the saved analysis visible and shows the message` **(Review Focus 1)**.
  - `unreadable answer shows the error and re-enables Generate`.
- [ ] **Step 2:** FAIL → commit `test(analysis-ui): …`.
- [ ] **Step 3:** Implement. The provider menu defaults to the last choice (`localStorage`, guarded by try/catch).
- [ ] **Step 4:** `npx vitest run && npm run lint && npm run build` → pass.
- [ ] **Step 5:** Commit: `feat(analysis-ui): AI analysis panel with provider choice`.
- [ ] **Step 6:**
  - Manual check with a real free key: Generate for Colombia with each configured provider, then read the text.
  - Update the README (features, free keys) and `docs/deploy.md` (env vars). Mark the AI parts of the 2026-10-25 spec as superseded by the new spec (one line at its top).
  - Commit `docs: …`.

---

## Slice 3 · `feat/comparison-insight`

**Done when:** on `/compare` with Colombia, Mexico, Spain and Chile, Generate shows a summary, the countries in real ranking order with the AI's explanation each, and key differences.

### Task 3.1: Comparison insight backend

**Files:**
- Modify: `backend/app/analysis/prompt.py`, `service.py`, `routes.py`
- Test: `backend/tests/analysis/test_comparison.py`

**Interfaces:**
- Produces:
  - `comparison_subject(codes: list[str]) -> str` (sorted, comma-joined).
  - `comparison_data_block(scorecards: list[Scorecard]) -> str`: per country, accessibility, dimensions and indicator scores (rounded), plus `rank` and `points_behind_leader`, overall and per dimension.
  - `comparison_prompt(scorecards, profile) -> str`.
  - `RankedExplanation{iso3, name, accessibility: float | None, rank: int, explanation: str}` and `order_ranking(scorecards, entries: list[RankingText]) -> list[RankedExplanation]`:
    - order by accessibility descending, `None` last;
    - explanation matched by `iso3`, otherwise `"No explanation provided"`;
    - duplicate or unknown entries ignored.
  - `ComparisonInsight{countries: list[str], provider, provider_label, model, created_at, flagged, outdated, summary, ranking: list[RankedExplanation], key_differences: list[str]}`.
  - `generate_comparison_insight(scorecards, profile, model, store)` and `get_comparison_insight(scorecards, profile, store)`.
  - Routes:
    - `POST /api/comparison/insight`, body `{iso3: list[str], provider}`: unknown codes 404; countries without data dropped; fewer than 2 left → 422 `"Select at least two countries with data"`; provider errors as in 2.3;
    - `GET /api/comparison/insight?iso3=…` → the insight for the filtered set, or 404.

- [ ] **Step 1: Write the failing tests.**
  - `test_data_block_contains_ranks_and_gaps` (leader `points_behind_leader == 0`; values match the scorecards).
  - `test_order_ranking_uses_real_scores_and_fills_missing` (AI lists MEX first, Chile is the real leader, one country is missing → its explanation is `"No explanation provided"`).
  - `test_countries_without_data_are_dropped_from_subject`.
  - `test_fewer_than_two_with_data_returns_422`.
  - `test_same_set_any_order_finds_insight` and `test_different_set_returns_404` **(Review Focus 5)**.
  - `test_outdated_after_profile_change`.
- [ ] **Step 2:** FAIL → commit `test(analysis): …`.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Full suite → pass.
- [ ] **Step 5:** Commit: `feat(analysis): comparison insight`.

### Task 3.2: Comparison insight panel

**Files:**
- Create: `frontend/src/features/analysis/ComparisonInsightPanel.tsx`
- Modify: `frontend/src/features/analysis/api.ts`, `frontend/src/features/comparison/ComparisonPage.tsx`, `analysis.test.tsx`

- [ ] **Step 1: Write the failing tests.**
  - `fewer than two countries with data shows the hint and no Generate button`.
  - `shows summary, ranking in order with percentages and key differences`.
  - `generate sends the selected codes and provider`.
  - `flagged and outdated states` (same copy as 2.4).
- [ ] **Step 2:** FAIL → commit `test(analysis-ui): …`.
- [ ] **Step 3:** Implement using `ProviderSelect`.
- [ ] **Step 4:** Checks pass.
- [ ] **Step 5:** Commit: `feat(analysis-ui): comparison insight panel`. README line (`docs: …`).

---

## Slice 4 · `feat/report-redesign`

**Done when:** a PDF for COL, MEX, ESP and CHL has a comparison page (ranking, heat map, top-3 radar, AI insight) and, for each country, the mockup layout with AI sections, attribution and new charts.

### Task 4.1: New report charts

**Files:**
- Modify: `backend/app/reports/charts.py`
- Test: `backend/tests/reports/test_charts.py`

**Interfaces:**
- Produces:
  - `SCORE_BANDS`: below 40 `#f4a29b` (barrier), 40–69 `#f6d58a`, 70 and above `#8fd1a6`, missing `#d9d9d9`; text is always printed on the cell.
  - `band_color(score: float | None) -> str`.
  - `indicator_heatmap_png(indicators: list[IndicatorResult]) -> bytes`: a 4×3 grid with rows C, A, G, E; each cell shows "ID" and the score, or "n/a".
  - `dimension_bars_png(dimensions: list[Dimension], best: dict[str, tuple[str, float]] | None) -> bytes`: horizontal bars with the score printed, plus "best: Chile 88" when `best` is given.
  - `comparison_heatmap_png(scorecards: list[Scorecard]) -> bytes`: countries × dimensions, scores printed.

- [ ] **Step 1: Write the failing tests.**
  - `test_band_color_boundaries` (39.9 → barrier, 40 → amber, 70 → green, None → grey).
  - `test_charts_return_png` (each function's output starts with `\x89PNG`, for Colombia's data and for a scorecard with missing indicators).
- [ ] **Step 2:** FAIL → commit `test(reports): …`.
- [ ] **Step 3:** Implement. matplotlib Agg; palette per the existing `SERIES_COLORS`.
- [ ] **Step 4:** Suite → pass.
- [ ] **Step 5:** Commit: `feat(reports): heat maps and dimension bars`.

### Task 4.2: Report layout with AI sections

**Files:**
- Modify: `backend/app/reports/pdf.py`, `backend/app/reports/routes.py`
- Test: `backend/tests/reports/test_pdf.py`, `backend/tests/reports/test_routes.py`

**Interfaces:**
- Consumes: Tasks 2.3 and 3.1 (`get_country_analysis`, `get_comparison_insight`, `PROVIDER_LABELS`) and 4.1.
- Produces:
  - `build_report(scorecards, analyses: dict[str, CountryAnalysis | None], insight: ComparisonInsight | None, profile, generated_at) -> bytes`.
  - Country page in the spec §6 order:
    - header `"Market accessibility: {pct}% · rank {r} of {n}"` (no rank part in a one-country report);
    - radar, executive summary, dimension bars (with `best` only for several countries), heat map, AI sections, attribution, indicator table.
  - Comparison page: ranking chart + table, comparison heat map, top-3 radar, and the insight with the real-order ranking.
  - The route loads analyses and the insight from the store (the insight only for 2+ countries with data). It never calls the AI.

- [ ] **Step 1: Write the failing tests** (update the existing PDF tests to the new signature).
  - `test_country_page_has_ai_sections_and_attribution` ("Executive summary", "Barriers", "Recommendation", and "AI analysis written by Groq (openai/gpt-oss-120b) on 2026-11-01. Numbers checked against the data.").
  - `test_missing_analysis_says_not_generated` ("AI analysis not generated yet").
  - `test_flagged_and_outdated_notes`.
  - `test_rank_shown_only_for_several_countries` ("rank 4 of 4" present for 4 countries; "rank" absent for one).
  - `test_comparison_page_includes_insight_in_real_order`.
  - `test_long_ai_text_flows_across_pages` (each section ~1,500 characters with accents: no exception, more pages than without, all text extractable) **(Review Focus 3)**.
  - `test_pdf_route_never_calls_ai` (kept: fake models that fail if called).
- [ ] **Step 2:** FAIL → commit `test(reports): …`.
- [ ] **Step 3:** Implement. AI boxes use a light blue fill (`#eef4fc`) with the existing heading style.
- [ ] **Step 4:** Suite → pass. Generate a real 4-country PDF from local data and inspect the pages visually.
- [ ] **Step 5:** Commit: `feat(reports): AI-written country and comparison pages`.

### Task 4.3: Export note

**Files:**
- Modify: `frontend/src/features/report/ExportPdfButton.tsx`, `report.test.tsx`, `frontend/src/features/scorecard/ScorecardPage.tsx`, `frontend/src/features/comparison/ComparisonPage.tsx`

**Interfaces:**
- Produces: `ExportPdfButton({iso3: string[], missingAnalyses: number})`. The note reads `"{missing} of {total} countries have no AI analysis yet"`, or `"This country has no AI analysis yet"` for one country. The pages compute `missingAnalyses` with `useQueries` over `getCountryAnalysis`; outdated counts as present.

- [ ] **Step 1: Write the failing tests.**
  - `shows note when analyses are missing` ("2 of 4 countries have no AI analysis yet").
  - `no note when all have analyses`.
  - `single-country wording`.
- [ ] **Step 2:** FAIL → commit `test(report-ui): …`.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Checks pass.
- [ ] **Step 5:** Commit: `feat(report-ui): note countries without AI analysis before export`. README "PDF report" section updated (`docs: …`).

---

## After the last slice

Final whole-branch review (most capable model), fix pass, then merge per slice. Update `docs/plans/polishing-backlog.md`: remove "LLM provider adapter (Task 5.3)", which this plan replaces.

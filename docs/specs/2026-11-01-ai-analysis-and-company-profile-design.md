# AI Analysis, Free AI Providers and Editable Company Profile: Design

- **Status:** draft for review · 2026-11-01
- **Builds on:** `docs/specs/2026-10-25-cage-market-accessibility-design.md` (the original spec). Everything not mentioned here stays as it is.
- **Public repo rule still applies:** no real company data or API keys in git.

## 1. Why

The tool already calculates and shows the CAGE scores clearly. What the thesis author and the company need now:

1. **A report that explains, not just shows.** The PDF should read like a short market-entry brief: why each dimension scored as it did, the main barriers and opportunities, and what to do next. The AI writes those explanations; the charts and tables show the numbers.
2. **Free AI.** The team will not pay for an AI provider. Gemini and Groq both have free API tiers.
3. **An easy way to change the company.** Editing the company description (and the settings that affect the scores) from the app, so the description can be updated or the tool tried with another company.

**Success:** a manager can open the PDF for Colombia and, in a few minutes, understand why the country scores 52%, what blocks entry, and the recommended next step. Every number in the AI text must match the data, and the report must read well whichever free AI wrote it.

## 2. Goals

1. **Company page** in the app to edit the company's name, description, languages and channels.
2. **Choice of AI provider: Gemini or Groq**, picked when generating. Only providers with an API key configured are offered.
3. **AI country analysis** with fixed sections (executive summary, why each CAGE dimension scored as it did, barriers, opportunities, recommendation and next steps), replacing today's short explanation.
4. **AI comparison insight** for the comparison page and the multi-country report: why the countries rank as they do.
5. **Redesigned PDF report** with new charts and the AI sections, following the approved mockup (section 6).

## 3. Non-goals and anti-goals

**Non-goals (not built now):**
- ChatGPT (OpenAI) and Claude (Anthropic): paid, so out of scope. The provider code must make adding one later a small change, but no adapter is written.
- Several saved companies; side-by-side answers from different AIs.
- Editing the home country or home time zone in the app.
- API keys typed into the app.
- The PDF calling the AI.

**Anti-goals (would be a failure even if it "works"):**
- AI text containing numbers that are not in the data, without being flagged.
- A real company's details or an API key ending up in the public repo.
- Exporting a PDF or opening a page triggering AI calls (surprise quota use).
- A free-quota limit showing up as a generic crash instead of a clear message.

## 4. Company profile

### Behaviour
- New page **Company** (top menu, next to Scorecard and Compare) with a form:
  - **Name**: required, at most 120 characters.
  - **Description**: free text the AI reads as background, at most 4,000 characters.
  - **Languages the company sells and gives support in**: checkboxes for English, Spanish, Portuguese, French, German and Italian (ISO codes `en, es, pt, fr, de, it`). At least one.
  - **Channels**: checkboxes for SMS, Email and WhatsApp (`sms, email, whatsapp`). At least one.
  - **Home country and home time zone**: shown read-only, with a note: *"Changing the home country needs new reference data; edit `backend/config/company.yaml` and run `collect`."*
  - **Save** and **Reset to the default profile** buttons.
- **Saving takes effect immediately.** Languages feed C1 and channels feed C2, and both are calculated when a scorecard is requested, so no data collection is needed.
- **Reset** deletes the saved edits and goes back to the file profile (`company.yaml`/`.md`, or the committed example).

### Storage
- Edits are stored in SQLite (the existing database, which lives on the Docker volume in production), never in files. A single saved profile overrides `name`, `description`, `supported_languages` and `channels` of the file profile. `home_country` and `home_timezone` always come from the file.
- The effective profile is used everywhere that uses the profile today: scoring, AI prompts, PDF.

### API
| Method | Path | Behaviour |
|---|---|---|
| GET | `/api/profile` | Effective profile + `editable` fields + `source: "saved" \| "file"` |
| PUT | `/api/profile` | Validate and save the editable fields → 200 with the effective profile; 422 with field errors |
| DELETE | `/api/profile` | Remove saved edits → 200 with the file profile |

All three require the login session.

## 5. AI providers and analyses

### Providers
- Two providers: **Gemini** (`gemini-3.8-flash` by default) and **Groq** (`openai/gpt-oss-120b` by default). Both are free-tier models that are current and stable or production as of 2026-11-01.
- Both are called through their **OpenAI-compatible chat-completions endpoints** with plain HTTP (httpx2), with no provider SDK:
  - Gemini: `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions`
  - Groq: `https://api.groq.com/openai/v1/chat/completions`
  - Both use `Authorization: Bearer <key>`.
- **Settings** (environment variables) replace `LLM_PROVIDER`, `LLM_API_KEY` and `LLM_MODEL`: `GEMINI_API_KEY`, `GEMINI_MODEL`, `GROQ_API_KEY` and `GROQ_MODEL`. A provider is *available* when its key is set.
- `GET /api/ai/providers` returns the available providers: `[{id: "gemini"|"groq", label, model}]`, which may be empty.
- **Error mapping** (shown to the user as-is):

| Situation | HTTP | Message |
|---|---|---|
| Provider not configured / unknown | 400 | "This AI is not configured" |
| No provider configured at all | 503 | "AI is not configured" |
| Provider answers 429 (free quota/rate limit) | 429 | "The free quota for Gemini is used up for now. Try again later or use Groq." (provider name and alternative filled in) |
| Provider answers 401/403 | 502 | "The Gemini API key was rejected" |
| Timeout, network error, other 5xx | 502 | "The AI service failed. Try again." |
| Answer is not valid structured JSON twice | 502 | "The AI returned an unreadable answer. Try again." |

### Time budget (my call)
- Generation is a **synchronous POST**. Each AI call has a **30 s timeout**, and a request makes **at most two AI calls**: the first answer plus **one retry, whatever the reason** (malformed JSON, missing keys, or unsupported numbers). The worst case therefore stays near 60 s, well under the Cloudflare tunnel's ~100 s limit and nginx's 120 s.
- If the retry still has unsupported numbers, the answer is saved flagged. If it is still malformed, the request returns the 502.

### Country analysis
- `POST /api/countries/{iso3}/analysis` with body `{"provider": "gemini"|"groq"}`.
- The model is asked for **JSON only** (`response_format: {"type": "json_object"}` where supported, plus the instruction) with this shape. The builder chooses the exact prompt wording; the word ranges are targets, not hard validation:
  - `executive_summary`: 60–100 words.
  - `dimensions`: an object with keys `Cultural`, `Administrative`, `Geographic` and `Economic`, 40–80 words each.
  - `barriers`: 2–3 short items.
  - `opportunities`: 2–3 short items.
  - `recommendation`: 50–100 words, ending with concrete next steps.
- The prompt keeps today's grounding: a DATA block of rounded scores, formatted raw values and years, plus the company description, and the rule to use only numbers from DATA and cite indicator IDs like `[A1]`.
- **Numbers guard** (existing) runs over **all text fields**. Unsupported numbers use the single retry (time budget above); if they persist, the analysis is saved with `flagged: true`.
- **Structure rules (my call):**
  - Missing or misspelled required keys count as a malformed answer, which uses the retry and then returns the 502.
  - Lists: 1–3 items are accepted. Extra items are cut to the first 3. An empty list counts as malformed.
- **Numbers the AI might work out itself (my call):** the prompt tells the model to use digits only for numbers in DATA, and to write timeframes and quantities in words (e.g. "a short pilot", "within the first months"). Any other digit is flagged by the guard, as intended.
- `GET /api/countries/{iso3}/analysis` returns the latest saved analysis for the country, or 404 if there is none. It carries `provider`, `model`, `created_at`, `flagged` and **`outdated`**, which is true when the scorecard data or the effective profile changed since it was written.
- **One analysis per country:** generating again, with either provider, replaces the previous one.

### Comparison insight
- `POST /api/comparison/insight` with body `{"iso3": ["COL","MEX",...], "provider": ...}`.
  - **Subject (my call):** countries without data are dropped. The insight is stored under the remaining set, which must contain at least two countries; otherwise the request returns 422 "Select at least two countries with data". The GET and the PDF look up the same filtered set. The comparison PDF already exports only countries with data, so the insight shown on the page is the one the PDF finds.
- JSON shape:
  - `summary`: 80–130 words on what separates the countries.
  - `ranking`: one entry per country in rank order, `{iso3, explanation}`, one or two sentences each.
  - `key_differences`: 2–4 items.
- DATA block: the compared countries' accessibility %, dimension scores and indicator scores, plus **precomputed rank positions and point gaps to the leader** (overall and per dimension), so the AI can write "ranks 2nd" or "trails Chile by 5 points" without inventing numbers. The same numbers guard, retry, flagged and outdated rules apply.
- **Ranking order is ours, not the AI's (my call).** The rank order shown in the app and the PDF always comes from the real scores; countries without an accessibility % go last. The AI's per-country explanations are matched to countries by `iso3`. A country the AI left out shows "No explanation provided". Duplicate or unknown entries are ignored.
- `GET /api/comparison/insight?iso3=...` returns the latest insight for **that exact set of countries** (order ignored), or 404.

### Storage
- One SQLite table for both kinds, replacing the `explanations` table, which holds development data only and can be dropped. One row per subject (country code, or the sorted country set), storing provider, model, the structured content, the guard result, the creation time and the cache key used to compute `outdated`.

## 6. The PDF report (approved mockup)

Built from **saved analyses only**. Exporting never calls the AI.

**Country page (one per country):**
1. **Header:** country name, market accessibility %, and **rank among the countries in this report** (omitted for a one-country report).
2. **Radar** of the four dimensions.
3. **AI executive summary** (highlighted box).
4. **Dimension bars:** each dimension's score. In a multi-country report, each bar is annotated with the best compared country for that dimension (e.g. "best: Chile 88"). In a one-country report, the bars appear without the annotation.
5. **Indicator heat map:** 12 cells (C1…E3) with their scores printed in them, coloured from red (barrier) through amber to green (strength); missing indicators are grey.
6. **AI sections:** why each dimension scored this way; main barriers and opportunities; recommendation and next steps.
7. **Attribution line:** *"AI analysis written by Gemini (gemini-3.8-flash) on 2026-11-01. Numbers checked against the data."* If flagged, *"Some numbers could not be verified; review before use."* If outdated, *"Written before the latest data or company change."*
8. The full indicator table with raw values, sources and years, as today.
9. A country without a saved analysis gets *"AI analysis not generated yet"* in place of the AI boxes.

**Comparison page (multi-country reports, before the country pages):** ranking bar chart, a **heat map of countries × dimensions** (scores printed), the radar overlay of the top 3, and the **AI comparison insight** if one is saved for exactly these countries.

The cover and methodology pages stay. Unicode must render as today (DejaVu Sans).

## 7. App changes

- **Scorecard page:** the "Explain" panel becomes **"AI analysis"**:
  - a provider menu (available providers only; if none, the message "AI is not configured");
  - a **Generate** button;
  - the rendered sections;
  - "written by … on …";
  - the flagged warning, and an **outdated** badge that invites regenerating.
- **Comparison page:** a **"Comparison insight"** panel with the same provider menu and Generate button, and the rendered summary, ranking explanations and key differences.
- **Export PDF:** next to the button, a note when some of the selected countries have no saved analysis (e.g. *"2 of 4 countries have no AI analysis yet"*). It never blocks the export.
- **Company page** as in section 4.

## 8. Testing expectations

Same rules as the original spec: test first, no network in tests, a fake model for AI logic, and nothing that only asserts mocks. Key behaviours to pin:
- profile save, validation errors, reset, and C1/C2 changing immediately after a save;
- provider list depending on configured keys;
- the request each adapter sends (URL, auth header, model, JSON response format), checked with a mock transport, and each error mapping (429, 401, timeout);
- JSON parsing with one retry, then a clear error;
- the numbers guard across all fields;
- `outdated` after a data or profile change;
- one analysis per subject;
- comparison insight requiring two or more countries with data;
- PDF text containing the AI sections, the attribution, the "not generated yet" text and the comparison insight;
- the UI flows: provider menu, generate, flagged, outdated, the Company form, and the export note.

## 9. Left to the builder

Exact prompt wording; chart styling within the existing palette (the heat map must print numbers, so colour is never the only signal); file and module layout; whether the two providers share one adapter class; how the profile override table is shaped; and how PDF content flows when an AI section is long.

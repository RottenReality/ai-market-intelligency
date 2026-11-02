# Polishing backlog

Items collected while building and using the tool. Before working on them, turn the chosen
items into a polishing plan (`docs/plans/<date>-polishing-plan.md`) with the team.

## Data freshness

- **Monthly automatic refresh on the VPS.** Add a cron job that runs
  `docker compose -f deploy/docker-compose.yml run --rm api python -m app.cli collect --all`
  once a month, so World Bank indicators (A3, G2, E1, E2, E3) and time zones (G1) update on their own.
  Log the output next to the backup log. *Done when:* the cron line is in `docs/deploy.md` and a
  test run on the server stores new values.
- **Yearly manual update (each November).** EF EPI and DataReportal publish new editions around
  November. Update `english_band`, `whatsapp_pct` and `social_media_pct` in
  `backend/data/manual_inputs.csv`, re-check tax treaties (PwC) and trade agreements (USTR), then
  run `collect`. *Done when:* the steps are in `docs/methodology.md` and a reminder exists
  (calendar or a scheduled GitHub issue).
- **Verify the WhatsApp figures (C2).** Colombia is verified (92.1%, Digital 2026: Colombia,
  slide 85 "Self-declared platform use", GWI Q2 2025). Mexico, Spain and Chile still come from an
  article citing the DataReportal/GWI report: confirm them on the same slide of each country's
  Digital 2026 report and update the source links.

## Methodology

- **Review the C2 rule.** `100 − WhatsApp %` gives about 8 for every compared country (≈92%
  WhatsApp use), which lowers every Cultural score without separating the countries. Decide with
  the thesis author whether to keep it, soften it or replace it (e.g. email reach).
- **Real company profile.** Create the gitignored `backend/config/company.yaml` / `.md`; if the
  company works in Spanish, C1 becomes 100 for Spanish-speaking countries.

## Product

- **Named tunnel with a domain** for a stable public address (see `docs/deploy.md`).
- **README screenshots and a demo GIF.**
- **Time-zone sampling note (minor).** G1 samples once a day; fine for current countries, revisit
  for a country with unusual daylight-saving rules.

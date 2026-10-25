# Methodology

This page explains, without code, how the tool turns public data into a **Market Accessibility %** for a country. It is written for the thesis and for business readers.

## 1. The idea: CAGE distance

Pankaj Ghemawat (2001, *"Distance Still Matters"*, Harvard Business Review) showed that companies overestimate foreign markets when they look only at size and growth, because they ignore the **distance** between countries. He groups distance into four dimensions:

| Dimension | Meaning | For a remote service company |
|---|---|---|
| **Cultural** | Language, values, communication habits | Can the company sell and support clients in their language? Do people use the same channels? |
| **Administrative** | Taxes, trade agreements, institutions | How much do taxes and regulation add to the cost of selling from abroad? |
| **Geographic** | Physical distance, time zones, communication links | Can the home team work in the same hours? Can customers be reached online? |
| **Economic** | Income, stability | Can local clients afford a service priced in the home currency? |

Ghemawat also says each industry is sensitive to different distances. For a **remote digital service**, kilometres hardly matter, so the Geographic dimension uses **working-hours overlap** and **digital reach** instead of physical distance.

All distances are measured **from the company's home country** (in the pilot, the United States), which is set in the company profile.

## 2. The 12 indicators

Each indicator gets a score from **0 (very hard) to 100 (very accessible)**.

| ID | Indicator | Rule | Source |
|---|---|---|---|
| C1 | Language barrier | 100 if the company already works in a local language. Otherwise the population's English level: Very high 100 · High 75 · Moderate 50 · Low 25 · Very low 0 | Company profile; EF English Proficiency Index |
| C2 | Channel fit | 100 if the company's product uses WhatsApp. Otherwise `100 − % of internet users on WhatsApp` (the more WhatsApp dominates, the less SMS/email reach) | DataReportal |
| C3 | Cultural distance | `100 − 25 × Kogut–Singh index` (0 distance → 100; 4 or more → 0) | Hofstede 6-D scores |
| A1 | Tax treaty with home country | Yes 100 / No 0 | PwC Worldwide Tax Summaries |
| A2 | Trade agreement with home country | Yes 100 / No 0 | USTR (or the home country's trade office) |
| A3 | Regulatory quality | World Bank estimate (−2.5 to +2.5) rescaled to 0–100 | World Bank, Worldwide Governance Indicators |
| G1 | Working-hours overlap | `(8 − largest hour difference during the year) / 8 × 100` | Computed from official time zones |
| G2 | Internet users | % of population | World Bank |
| G3 | Social media users | % of population | DataReportal |
| E1 | Income per person vs home | `country income ÷ home income × 100` (purchasing power parity, max 100) | World Bank |
| E2 | Market size | 100 if the urban population is at least 10 million, else 0 | World Bank |
| E3 | Inflation | `100 − 5 × annual inflation %` (0% → 100, 20% or more → 0) | World Bank |

### Cultural distance (C3) in detail

The **Kogut–Singh index** (Kogut & Singh, 1988) combines Hofstede's six culture dimensions: power distance, individualism, masculinity, uncertainty avoidance, long-term orientation and indulgence. For each dimension it squares the difference between the country and the home country and divides it by that dimension's variance across all countries in the dataset. The index is the average of those terms. Dimensions without data for either country are skipped.

## 3. From indicators to the final percentage

1. **Dimension %** = the average of that dimension's available indicator scores. The tool always shows how many of the 3 indicators had data (e.g. "1/3 indicators").
2. **Market Accessibility %** = the average of the four dimensions, each weighted equally (25%).
3. **Missing data is never counted as 0.** A missing indicator is shown as "n/a" and left out of its dimension's average. If a whole dimension has no data, the tool does not compute the Accessibility % and says which dimension is missing.

Every number shown links to its source and year, so any result can be checked.

## 4. Where the data comes from and how to refresh it

| Data | How it is collected |
|---|---|
| World Bank indicators (A3, G2, E1, E2, E3) | Automatically, through the World Bank API |
| Time-zone overlap (G1) and cultural distance (C3) | Calculated by the tool |
| Manual values (C1 English level, C2 WhatsApp %, G3 social media %, A1 tax treaty, A2 trade agreement) | Typed into `backend/data/manual_inputs.csv` |

**Editing `manual_inputs.csv`:** one row per country and value, with columns `iso3, metric, value, year, source_name, source_url`. Valid metrics and values:

- `english_band`: `very_high`, `high`, `moderate`, `low` or `very_low`
- `whatsapp_pct`, `social_media_pct`: a number from 0 to 100
- `tax_treaty_with_home`, `trade_agreement_with_home`: `yes` or `no`

The file can be edited in Excel. A Spanish-locale export (`;` separators and decimal commas) is accepted. If a row is wrong, the collection step reports the line number and what is expected.

**Refresh the data** after editing the CSV, after adding a country, or after changing the company profile:

```bash
cd backend
uv run --env-file .env python -m app.cli collect --all
```

## 5. Hofstede data terms

The Hofstede scores come from <https://geerthofstede.com/research-and-vsm/dimension-data-matrix/> (*Cultures and Organizations*, 3rd ed., 2010). The page states: *"Researchers can use them without asking for permission. Those who are considering commercial use should contact us."* Using the tool for the thesis is research use. **A company using it commercially should contact Hofstede first.**

## 6. Limitations

- Public data can be one or two years old. Each value shows its year.
- Equal weights are a simplification. The tool shows each dimension separately, so readers can weigh them differently.
- Some indicators depend on manually collected values and on the company profile.
- The CAGE model measures **accessibility**, not profitability: a market can be accessible and still be too small or too competitive.

## References

- Ghemawat, P. (2001). Distance still matters: The hard reality of global expansion. *Harvard Business Review*, 79(8), 137–147.
- Hofstede, G., Hofstede, G. J., & Minkov, M. (2010). *Cultures and Organizations: Software of the Mind* (3rd ed.). McGraw-Hill.
- Kogut, B., & Singh, H. (1988). The effect of national culture on the choice of entry mode. *Journal of International Business Studies*, 19(3), 411–432.
- Kaufmann, D., Kraay, A., & Mastruzzi, M. (2010). The Worldwide Governance Indicators: Methodology and analytical issues. World Bank Policy Research Working Paper 5430.

# OM Field Validation Design

## Overview

Validate financial metrics extracted from Offering Memorandums against real market data. For each numeric field, GPT-4o researches the local market via web search (Tavily), compares the OM value to what it finds, and produces a per-field validation with status, explanation, and cited sources.

## Pipeline

The auto-pipeline gains a fourth step:

```
Upload OM → Extract Data → Generate Benchmarks → Validate OM → Export
```

Validation runs automatically after benchmarks complete. Users can also re-validate manually.

## Data Model

New `field_validations` table:

| Column | Type | Description |
|--------|------|-------------|
| id | UUID PK | |
| deal_id | UUID FK → deals | |
| field_key | string | Matches extracted_fields.field_key |
| om_value | float | The value from the OM |
| market_value | float | Market reference value from research |
| status | enum | within_range, above_market, below_market, suspicious, insufficient_data |
| explanation | text | LLM-generated explanation with inline citations |
| sources | JSON | Array of {url, title, snippet} |
| confidence | float | 0-1 confidence in the assessment |
| created_at | datetime | |

Upsert key: `(deal_id, field_key)`. Regenerating validation replaces previous results.

## Field Selection

Only numeric fields (`value_number IS NOT NULL`) are sent for validation. The LLM decides which are financial metrics worth validating vs. descriptive metadata to skip (e.g., square_feet, year_built).

Target fields include: rent_psf_yr, vacancy_rate, cap_rate, opex_ratio, noi, purchase_price, price_psf, expense_psf, tax_psf, insurance_psf, management_fee_pct, occupancy_rate.

## Backend Architecture

### New endpoint

`POST /v1/deals/{deal_id}/validate` — triggers validation, returns list of FieldValidation results.

### ValidationService.validate_fields(deal_id)

1. Fetch deal (location, property_type, square_feet)
2. Fetch extracted fields (filter: value_number IS NOT NULL)
3. Fetch assumptions/benchmarks (for additional context)
4. Call `LLMProvider.validate_om_fields(deal, fields, benchmarks)`
5. Persist FieldValidation entities (upsert by deal_id + field_key)
6. Return validations

### LLM Integration

**Model:** GPT-4o with tool use

**Tool:** `web_search(query: string)` backed by Tavily Search API

**Prompt structure:**
- System: "You are a CRE analyst validating an Offering Memorandum. For each financial metric, research the local market using the web_search tool, compare the OM value to market data, and assess whether the OM figure is reasonable."
- Context: deal metadata (property_type, address, city, state, square_feet) + all numeric extracted fields + AI benchmark assumptions
- Instructions: For each field, provide status (within_range/above_market/below_market/suspicious/insufficient_data), a market_value reference point, an explanation citing sources, and confidence score.
- Response format: JSON with `validations` array

**Tavily configuration:**
- Search depth: "advanced" for better results
- Include answer: false (we want raw results, not Tavily's summary)
- Max results per query: 5

**Temperature:** 0.2 (lower than benchmarks for more deterministic validation)

## Frontend

### New "Validation" tab

Positioned between Assumptions and Export tabs. Shows a table:

| Column | Content |
|--------|---------|
| Field | Human-readable field name |
| OM Value | The extracted value with unit |
| Market Range | Market reference value or range |
| Status | Color-coded badge (green/yellow/red) |
| Explanation | LLM reasoning with inline source references |

Status badge colors:
- Green: `within_range`
- Yellow: `insufficient_data`
- Red: `above_market`, `below_market`, `suspicious`

Source URLs rendered as clickable links below the explanation or in a footnotes section.

### Progress bar update

5 stages: Upload OM → Extract Data → Set Assumptions → Validate OM → Export

New active step label: "Validating OM..."

### useDeal hook changes

Add `validations` state fetched from `GET /v1/deals/{deal_id}/validations`.

## Dependencies

- **Tavily Python SDK** (`tavily-python`): Web search API for market research
- **New env var:** `DEALDESK_TAVILY_API_KEY` for Tavily API access

## Cost & Latency

- Tavily: ~$0.01 per search, expect 5-10 searches per validation run = ~$0.05-0.10
- GPT-4o: longer prompt with tool use, expect ~$0.05-0.15 per validation run
- Total per validation: ~$0.10-0.25
- Latency: 15-45 seconds (multiple sequential web searches + LLM reasoning)

# DataForSEO Integration Notes

## Endpoints used (Standard / task-queue mode)

| Purpose | Method | Path |
|---|---|---|
| Submit Search Volume task | POST | `/v3/keywords_data/google_ads/search_volume/task_post` |
| Retrieve Search Volume result | GET | `/v3/keywords_data/google_ads/search_volume/task_get/{id}` |
| Submit Google Trends task | POST | `/v3/keywords_data/google_trends/explore/task_post` |
| Retrieve Google Trends result | GET | `/v3/keywords_data/google_trends/explore/task_get/{id}` |

Authentication is HTTP Basic Auth using the DataForSEO login/password from `.env` (`DATAFORSEO_LOGIN` / `DATAFORSEO_PASSWORD`).

**Verified against the live API during Phase 1 testing:** the base URL, both `task_post` paths, HTTP Basic Auth header handling, and the top-level JSON envelope (`version`, `status_code`, `status_message`, `tasks`) all matched what's implemented in `api/dataforseo_client.py` — confirmed by real `401` responses when running with placeholder credentials (see below). What's **not yet verified** against a live successful run (no real credentials were available while building this) is called out in [Open verification items](#open-verification-items).

### Search Volume task_post payload

```json
[
  {
    "location_code": 2840,
    "language_code": "en",
    "keywords": ["ceramic coffee mug", "macrame wall hanging"]
  }
]
```

### Search Volume task_get result item (per keyword)

```json
{
  "keyword": "ceramic coffee mug",
  "search_volume": 8100,
  "cpc": 0.85,
  "competition": "MEDIUM",
  "competition_index": 45,
  "monthly_searches": [
    { "year": 2025, "month": 1, "search_volume": 7200 }
  ]
}
```

Parsed by `api/search_volume.py::_parse_search_volume_item` into a `SearchVolumeResult`.

### Google Trends task_post payload

```json
[
  {
    "location_code": 2840,
    "language_code": "en",
    "keywords": ["ceramic coffee mug", "coffee mug", "handmade mug", "mug gift"],
    "time_range": "past_5_years"
  }
]
```

At most `GOOGLE_TRENDS_MAX_KEYWORDS_PER_TASK` (5) keywords per task; more keywords are automatically split into multiple tasks.

### Google Trends task_get result shape

```json
{
  "keywords": ["ceramic coffee mug"],
  "items": [
    {
      "type": "google_trends_graph",
      "data": [
        { "date_from": "2025-01-01", "date_to": "2025-01-31", "values": [48] }
      ]
    }
  ]
}
```

Parsed by `api/google_trends.py::_parse_trends_result_items`, which locates the `google_trends_graph` item and builds one `TrendPoint` per keyword per data point.

## Open verification items

These were built against DataForSEO's documented behavior; confirm against a real account before relying on them in production:

1. **"Task still pending" status codes.** `settings.TASK_PENDING_STATUS_CODES = {40601, 40602}` is used by `DataForSeoClient.poll_task_until_ready` to distinguish "keep polling" from "hard failure." This could only be confirmed with a real, successfully-submitted task — placeholder credentials only produced immediate `401`s, which exercised the failure path but not the polling path. Verify the exact codes on first live run and adjust `settings.py` if needed.
2. **Trends "type" field name.** `_TRENDS_GRAPH_ITEM_TYPE = "google_trends_graph"` in `api/google_trends.py` — confirm this is the exact `type` value DataForSEO returns for the time-series item (as opposed to `google_trends_map`, `google_trends_topics_list`, etc., which are ignored).
3. **Search Volume keyword limit.** DataForSEO's documented cap is up to 1,000 keywords per Search Volume task. Phase 1 sends one task for the whole workbook; Phase 2 (unlimited rows) should chunk beyond that limit the same way Google Trends already does.

## Why DataForSEO (not an alternative)

Per project instructions, DataForSEO was kept as the sole provider — no alternative was substituted. For reference, the tradeoff considered *within* DataForSEO itself:

| | Live mode | Standard (task-queue) mode — **chosen** |
|---|---|---|
| Call pattern | Synchronous, single request/response | Async: `task_post` then poll `task_get` |
| Cost | Higher per call | Lower per call |
| Complexity | Simpler (no polling) | Requires poll-until-ready loop, pending-vs-failed status handling |
| Fit for this project | Simpler but costlier at scale | Matches the retry/error-handling requirements already needed for Phase 2's unlimited-row goal |

Standard mode was selected per explicit direction during planning, accepting the added polling complexity in exchange for lower per-call cost as the workbook grows in Phase 2.

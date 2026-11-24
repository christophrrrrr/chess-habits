# Monitoring

Both services write one JSON line per request to stdout, for example:

```json
{"ts": "2026-11-12T00:38:10+00:00", "level": "INFO", "service": "games", "logger": "request",
 "msg": "request", "method": "POST", "path": "/players/1/imports", "status": 200, "duration_ms": 586.9}
```

Container Apps forwards stdout to the Log Analytics workspace `<prefix>-logs`
(table `ContainerAppConsoleLogs_CL`, the line is in `Log_s`). Request bodies are never logged.

## Base query

Save as function `ChessHabitsRequests` (Log Analytics → Logs → Save → Save as function):

```kusto
ContainerAppConsoleLogs_CL
| where ContainerAppName_s endswith "-games" or ContainerAppName_s endswith "-insights"
| extend log = parse_json(Log_s)
| where tostring(log.logger) == "request"
| project TimeGenerated,
          service = tostring(log.service),
          method = tostring(log.method),
          path = tostring(log.path),
          status = toint(log.status),
          duration_ms = todouble(log.duration_ms)
```

## Dashboard (Azure Workbook)

The dashboard is code: [infra/workbook.bicep](../infra/workbook.bicep), deployed by
[infra/main.bicep](../infra/main.bicep) together with everything else. Open it in the portal:
resource group → **Workbooks** → **`<prefix> monitoring`**.

It runs the queries below on the `<prefix>-logs` workspace, per service:

| Panel | Query |
|---|---|
| Requests per minute | [Requests per service](#requests-per-service) (1 min buckets) |
| Error rate (5xx share) | [Error rate](#error-rate-5xx-share) |
| Response time p50 / p95 | [Response time](#response-time-p50--p95) |
| SLO and error budget (fixed 7 days) | [SLO](#slo) |

A time range picker at the top (default: last 24 hours) applies to the three charts. The
Workbook inlines the base query with `let`, so it works without saving the
`ChessHabitsRequests` function by hand.

Screenshots of the deployed Workbook on 23 Nov 2026 (last 3 days, the first day after the first
deployment):

![Requests per minute, per service](screenshots/monitoring-requests.png)
![Error rate (5xx share), per service](screenshots/monitoring-errors.png)
![Response time p50 / p95](screenshots/monitoring-latency.png)
![SLO and error budget](screenshots/monitoring-slo.png)

## Dashboard queries

The same queries for the Logs page. They need the `ChessHabitsRequests` function above.

### Requests per service

15 min buckets here; the Workbook uses 1 min buckets.

```kusto
ChessHabitsRequests
| summarize requests = count() by service, bin(TimeGenerated, 15m)
| render timechart
```

### Error rate (5xx share)

```kusto
ChessHabitsRequests
| summarize error_rate = 100.0 * countif(status >= 500) / count() by service, bin(TimeGenerated, 1h)
| render timechart
```

### Response time (p50 / p95)

```kusto
ChessHabitsRequests
| where path != "/health"
| summarize p50 = percentile(duration_ms, 50), p95 = percentile(duration_ms, 95)
    by service, bin(TimeGenerated, 1h)
| render timechart
```

## SLO

**Availability: 99% of API requests (excluding `/health`) succeed (status < 500) over a rolling
7 days.** `503` answers caused by chess.com being unreachable count as failures; they are rare and
we want to see them.

```kusto
ChessHabitsRequests
| where TimeGenerated > ago(7d) and path != "/health"
| summarize total = count(), good = countif(status < 500)
| extend availability_pct = round(100.0 * good / total, 2), slo_pct = 99.0
| extend error_budget_left_pct = round(100.0 - (100.0 - availability_pct) / (100.0 - slo_pct) * 100.0, 1)
```

Cold starts after scale-to-zero (and Azure SQL resuming from auto-pause) make the first request
after idle slow, so latency is tracked on the dashboard but not used as the SLO.

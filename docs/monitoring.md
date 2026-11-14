# Monitoring

Both services write one JSON line per request to stdout, for example:

```json
{"ts": "2026-11-12T00:38:10+00:00", "level": "INFO", "service": "games", "logger": "request",
 "msg": "request", "method": "POST", "path": "/players/1/imports", "status": 200, "duration_ms": 586.9}
```

Container Apps forwards stdout to the Log Analytics workspace `<prefix>-logs`
(table `ContainerAppConsoleLogs_CL`, the line is in `Log_s`). Request bodies are never logged.

## Base query

Save as function `KiebitzRequests` (Log Analytics → Logs → Save → Save as function):

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

## Dashboard queries

Pin each to an Azure dashboard or a Workbook.

**Requests per service (15 min buckets)**
```kusto
KiebitzRequests
| summarize requests = count() by service, bin(TimeGenerated, 15m)
| render timechart
```

**Error rate (5xx share)**
```kusto
KiebitzRequests
| summarize error_rate = 100.0 * countif(status >= 500) / count() by service, bin(TimeGenerated, 1h)
| render timechart
```

**Response time (p50 / p95)**
```kusto
KiebitzRequests
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
KiebitzRequests
| where TimeGenerated > ago(7d) and path != "/health"
| summarize total = count(), good = countif(status < 500)
| extend availability_pct = round(100.0 * good / total, 2), slo_pct = 99.0
| extend error_budget_left_pct = round(100.0 - (100.0 - availability_pct) / (100.0 - slo_pct) * 100.0, 1)
```

Cold starts after scale-to-zero (and Azure SQL resuming from auto-pause) make the first request
after idle slow, so latency is tracked on the dashboard but not used as the SLO.

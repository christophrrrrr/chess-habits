// Monitoring dashboard: an Azure Workbook on the existing Log Analytics workspace.
//
// Panels, per service: requests per minute, error rate (5xx share) and p50/p95 response
// time. The queries are the ones in
// docs/monitoring.md. The base query is inlined with `let`, so the Workbook does not depend
// on a function saved by hand in the portal.
//
// Deployed as a module from main.bicep; no new Azure service, the Workbook lives in the
// group's resource group and reads the workspace that Container Apps already writes to.

@description('Name prefix, e.g. sdd-3a-g3. Used in the Workbook\'s display name.')
param prefix string

param location string

@description('Resource ID of the Log Analytics workspace the Container Apps log to.')
param workspaceId string

// Workbook resource names must be GUIDs; the stable seed keeps redeploys updating the same one.
var workbookName = guid(resourceGroup().id, prefix, 'chess-habits-monitoring')
var displayName = '${prefix} monitoring'

// Base query from docs/monitoring.md (the `ChessHabitsRequests` function), one row per request.
var base = '''
let ChessHabitsRequests = ContainerAppConsoleLogs_CL
| where ContainerAppName_s endswith "-games" or ContainerAppName_s endswith "-insights"
| extend log = parse_json(Log_s)
| where tostring(log.logger) == "request"
| project TimeGenerated,
          service = tostring(log.service),
          method = tostring(log.method),
          path = tostring(log.path),
          status = toint(log.status),
          duration_ms = todouble(log.duration_ms);
'''

var requestsQuery = '${base}${'''ChessHabitsRequests
| summarize requests = count() by service, bin(TimeGenerated, 1m)
| render timechart
'''}'

var errorRateQuery = '${base}${'''ChessHabitsRequests
| summarize error_rate = 100.0 * countif(status >= 500) / count() by service, bin(TimeGenerated, 1h)
| render timechart
'''}'

var latencyQuery = '${base}${'''ChessHabitsRequests
| where path != "/health"
| summarize p50 = percentile(duration_ms, 50), p95 = percentile(duration_ms, 95)
    by service, bin(TimeGenerated, 1h)
| render timechart
'''}'

var workspaceType = 'microsoft.operationalinsights/workspaces'

// A chart panel that follows the time range picker at the top of the Workbook.
func chart(name string, title string, query string, workspaceType string) object => {
  type: 3
  name: name
  content: {
    version: 'KqlItem/1.0'
    title: title
    query: query
    size: 0
    queryType: 0
    resourceType: workspaceType
    timeContextFromParameter: 'TimeRange'
    visualization: 'timechart'
  }
}

var workbook = {
  version: 'Notebook/1.0'
  items: [
    {
      type: 1
      name: 'title'
      content: {
        json: '## Chess Habits monitoring\nRequest logs of the games and insights services (one JSON line per request, see `docs/monitoring.md`). Cold starts after scale-to-zero make the first request after idle slow.'
      }
    }
    {
      type: 9
      name: 'parameters'
      content: {
        version: 'KqlParameterItem/1.0'
        parameters: [
          {
            id: 'b6f3c1d2-7a4e-4c1b-9f2a-5d8e0c3a1b70'
            version: 'KqlParameterItem/1.0'
            name: 'TimeRange'
            label: 'Time range'
            type: 4
            isRequired: true
            value: { durationMs: 86400000 }
            typeSettings: {
              selectableValues: [
                { durationMs: 3600000 }
                { durationMs: 14400000 }
                { durationMs: 86400000 }
                { durationMs: 259200000 }
                { durationMs: 604800000 }
              ]
              allowCustom: true
            }
          }
        ]
        style: 'pills'
        queryType: 0
        resourceType: workspaceType
      }
    }
    chart('requests', 'Requests per minute, per service', requestsQuery, workspaceType)
    chart('error-rate', 'Error rate (5xx share, %), per service', errorRateQuery, workspaceType)
    chart('latency', 'Response time p50 / p95 (ms, without /health), per service', latencyQuery, workspaceType)
  ]
  fallbackResourceIds: [workspaceId]
  '$schema': 'https://github.com/Microsoft/Application-Insights-Workbooks/blob/master/schema/workbook.json'
}

resource dashboard 'Microsoft.Insights/workbooks@2023-06-01' = {
  name: workbookName
  location: location
  kind: 'shared'
  properties: {
    displayName: displayName
    category: 'workbook'
    sourceId: workspaceId
    serializedData: string(workbook)
  }
}

output workbookName string = dashboard.name
output workbookDisplayName string = displayName

// Kiebitz infrastructure, deployed into the group's EXISTING resource group (never creates one).
//
// Creates exactly what the assignment allows:
//   - 2 Container Apps (games, insights): Consumption, scale to zero, max 1 replica
//   - 1 logical SQL server with 2 serverless databases (auto-pause), one per service
//   - 1 Static Web App for the UI
//   - plus what these need to exist: the Container Apps environment and its Log Analytics
//     workspace (where request logs, dashboard queries and the SLO query run).
//
// Deploy: .github/workflows/infra.yml (manual) or infra/deploy.sh.

@description('Name prefix, e.g. sdd-3a-g3. Every resource name starts with it.')
param prefix string

param location string = resourceGroup().location

@description('Static Web Apps is only offered in some regions.')
param staticWebAppLocation string = 'westeurope'

@description('SQL administrator login (stored only as a GitHub variable).')
param sqlAdminLogin string

@secure()
@description('SQL administrator password (GitHub secret).')
param sqlAdminPassword string

@description('Full image references, e.g. ghcr.io/christophrrrrr/kiebitz-games:<sha>.')
param gamesImage string
param insightsImage string

@description('GHCR credentials if the images are private; leave empty for public images.')
param registryUsername string = ''
@secure()
param registryPassword string = ''

var registryServer = 'ghcr.io'
var useRegistryAuth = !empty(registryUsername)

// ---- Monitoring ------------------------------------------------------------------------

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${prefix}-logs'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${prefix}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
    workloadProfiles: [
      { name: 'Consumption', workloadProfileType: 'Consumption' }
    ]
  }
}

// ---- Databases -------------------------------------------------------------------------

resource sql 'Microsoft.Sql/servers@2023-08-01' = {
  name: '${prefix}-sql'
  location: location
  properties: {
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
  }
}

// Lets Azure services (the Container Apps) reach the server. No client IP rules.
resource sqlAllowAzure 'Microsoft.Sql/servers/firewallRules@2023-08-01' = {
  parent: sql
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

var serverlessDb = {
  sku: { name: 'GP_S_Gen5', tier: 'GeneralPurpose', family: 'Gen5', capacity: 1 }
  properties: {
    autoPauseDelay: 60 // minutes
    minCapacity: json('0.5')
    maxSizeBytes: 2147483648 // 2 GB
    zoneRedundant: false
    requestedBackupStorageRedundancy: 'Local'
  }
}

resource gamesDb 'Microsoft.Sql/servers/databases@2023-08-01' = {
  parent: sql
  name: '${prefix}-games-db'
  location: location
  sku: serverlessDb.sku
  properties: serverlessDb.properties
}

resource insightsDb 'Microsoft.Sql/servers/databases@2023-08-01' = {
  parent: sql
  name: '${prefix}-insights-db'
  location: location
  sku: serverlessDb.sku
  properties: serverlessDb.properties
}

// ---- UI --------------------------------------------------------------------------------

resource ui 'Microsoft.Web/staticSites@2023-12-01' = {
  name: '${prefix}-ui'
  location: staticWebAppLocation
  sku: { name: 'Free', tier: 'Free' }
  properties: {}
}

var uiOrigin = 'https://${ui.properties.defaultHostname}'

// ---- Services --------------------------------------------------------------------------

func dbUrl(server string, db string, user string, password string) string =>
  'mssql+pymssql://${uriComponent(user)}:${uriComponent(password)}@${server}:1433/${db}'

var registries = useRegistryAuth
  ? [
      {
        server: registryServer
        username: registryUsername
        passwordSecretRef: 'registry-password'
      }
    ]
  : []

var registrySecrets = useRegistryAuth ? [{ name: 'registry-password', value: registryPassword }] : []

var commonScale = {
  minReplicas: 0
  maxReplicas: 1
  rules: [
    {
      name: 'http'
      http: { metadata: { concurrentRequests: '20' } }
    }
  ]
}

var probes = [
  {
    type: 'Liveness'
    httpGet: { path: '/health', port: 8000 }
    initialDelaySeconds: 5
    periodSeconds: 30
  }
  {
    // Startup covers Azure SQL resume from auto-pause plus migrations (up to ~2 min).
    type: 'Startup'
    httpGet: { path: '/health', port: 8000 }
    initialDelaySeconds: 3
    periodSeconds: 5
    failureThreshold: 30
  }
]

resource gamesApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${prefix}-games'
  location: location
  properties: {
    environmentId: env.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
      registries: registries
      secrets: concat(
        [
          {
            name: 'database-url'
            value: dbUrl(sql.properties.fullyQualifiedDomainName, gamesDb.name, sqlAdminLogin, sqlAdminPassword)
          }
        ],
        registrySecrets
      )
    }
    template: {
      containers: [
        {
          name: 'games'
          image: gamesImage
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'DATABASE_URL', secretRef: 'database-url' }
            { name: 'CORS_ORIGINS', value: uiOrigin }
          ]
          probes: probes
        }
      ]
      scale: commonScale
    }
  }
}

resource insightsApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${prefix}-insights'
  location: location
  properties: {
    environmentId: env.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
      registries: registries
      secrets: concat(
        [
          {
            name: 'database-url'
            value: dbUrl(sql.properties.fullyQualifiedDomainName, insightsDb.name, sqlAdminLogin, sqlAdminPassword)
          }
        ],
        registrySecrets
      )
    }
    template: {
      containers: [
        {
          name: 'insights'
          image: insightsImage
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'DATABASE_URL', secretRef: 'database-url' }
            { name: 'CORS_ORIGINS', value: uiOrigin }
            { name: 'GAMES_SERVICE_URL', value: 'https://${gamesApp.properties.configuration.ingress.fqdn}' }
          ]
          probes: probes
        }
      ]
      scale: commonScale
    }
  }
}

output gamesUrl string = 'https://${gamesApp.properties.configuration.ingress.fqdn}'
output insightsUrl string = 'https://${insightsApp.properties.configuration.ingress.fqdn}'
output uiUrl string = uiOrigin
output logAnalyticsWorkspaceId string = logs.properties.customerId

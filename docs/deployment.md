# Deployment (Azure)

Everything in Azure is created by [infra/main.bicep](../infra/main.bicep) and updated only by
GitHub Actions. Nothing is changed by hand in the portal after setup.

| Resource | Name | Notes |
|---|---|---|
| Container App | `<prefix>-games` | Consumption, scale 0–1, port 8000, `/health` probes |
| Container App | `<prefix>-insights` | same; calls `<prefix>-games` over HTTPS |
| SQL server | `<prefix>-sql` | TLS 1.2+, only Azure services allowed through the firewall |
| SQL database | `<prefix>-games-db` | serverless GP_S_Gen5_1, auto-pause after 60 min, 2 GB |
| SQL database | `<prefix>-insights-db` | same |
| Static Web App | `<prefix>-ui` | Free tier |
| Container Apps environment | `<prefix>-env` | required by the apps |
| Log Analytics workspace | `<prefix>-logs` | request logs, dashboard queries, SLO query |

`<prefix>` is the group prefix from the professor, e.g. `sdd-3a-g3`. Images live in GitHub
Container Registry: `ghcr.io/christophrrrrr/chess-habits-games` and `...-insights`.

## Where it runs

The group project runs in IE's subscription **Azure Simple IE Instituto de Empresa, S.L.**,
which lives in its own directory (tenant), not in anyone's Azure for Students. Our resource
group is `rg-sdd-3a-g3`; we never create resource groups. GitHub Actions signs in as the
group's managed identity `sdd-3a-g3-github` through OpenID Connect (federated credential),
so there is **no client secret** to store.

### Look at it yourself

1. Accept the email from *Microsoft Invitations on behalf of IE Instituto de Empresa, S.L.*
   (check Junk).
2. Portal: switch directory in Settings → Directories + subscriptions (or use the link from the
   professor's message).
3. Terminal (add `--use-device-code` if the browser sign-in fails):

   ```sh
   az login --tenant <IE tenant ID>
   az account set --subscription "Azure Simple IE Instituto de Empresa, S.L."
   az group show --name rg-sdd-3a-g3 -o table
   ```

## One-time setup (when the managed identity is ready)

1. **Repository variables** (Settings → Secrets and variables → Actions → Variables). These
   are identifiers, not secrets:

   | Variable | Value |
   |---|---|
   | `AZURE_CLIENT_ID` | client ID of the managed identity `sdd-3a-g3-github` |
   | `AZURE_TENANT_ID` | the IE directory (tenant) ID |
   | `AZURE_SUBSCRIPTION_ID` | ID of *Azure Simple IE Instituto de Empresa, S.L.* |
   | `AZURE_RESOURCE_GROUP` | `rg-sdd-3a-g3` |
   | `AZURE_PREFIX` | `sdd-3a-g3` |
   | `SQL_ADMIN_LOGIN` | `chesshabitsadmin` |
   | `AZURE_ENABLED` | `true` (set last, after step 4) |

   The client ID: `az identity show -g rg-sdd-3a-g3 -n sdd-3a-g3-github --query clientId -o tsv`
   (or ask the professor).

2. **Repository secrets** (same page → Secrets). Paste values only there, never in chat, code or issues:

   | Secret | Value |
   |---|---|
   | `SQL_ADMIN_PASSWORD` | a new strong password (16+ characters) |
   | `GHCR_PULL_TOKEN` | only if the GHCR images stay private: a classic PAT with `read:packages` |

   Alternative to `GHCR_PULL_TOKEN`: make both packages public (GitHub → Packages → package
   settings → Change visibility). They contain no secrets.

3. **Create an environment** called `production` (Settings → Environments). Every Azure job
   runs in it, so the OIDC token's subject is
   `repo:christophrrrrr/chess-habits:environment:production`. The managed identity's federated
   credential must match exactly that subject; confirm it with the professor.

4. **First run**: merge to `main` (or run *Deploy* manually) so the images are pushed, then run
   the *Infrastructure* workflow (Actions → Infrastructure → Run workflow). Its summary shows
   the live URLs.

5. Set `AZURE_ENABLED=true`. From now on every merge to `main` deploys automatically.

## What a deploy does ([deploy.yml](../.github/workflows/deploy.yml))

1. CI (lint, format, tests with the 70% coverage gate, audits, image builds, compose smoke test).
2. Push both images tagged with the commit SHA (and `latest`).
3. `az containerapp update` both apps to the SHA tag. Migrations run on container startup.
4. Wait until each app's latest revision is ready **and** `/health` answers 200; fail after 5 minutes.
5. Build the UI with the live service URLs and upload it to Static Web Apps.
6. Smoke test: UI page, `GET /players`, `GET /analyses` on the live URLs.

## Rollback

Re-run the *Deploy* workflow for an earlier commit (Actions → Deploy → choose the run → Re-run),
or run *Infrastructure* with `image_tag` set to an earlier commit SHA.

## Known limitations (to revisit)

- Both services use the SQL admin login. Next step: one contained database user per service
  with rights only on its own database.
- The firewall rule `AllowAzureServices` allows any Azure service; with the allowed services
  only, VNet integration is not available.

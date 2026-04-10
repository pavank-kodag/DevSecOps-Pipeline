# DevSecOps CI/CD Pipeline with Automated Security Gates



A production-grade DevSecOps CI/CD pipeline where security is enforced at every stage through automated gates. Code with known vulnerabilities never reaches Azure Container Registry.

---

## Pipeline Architecture

```
git push to main
        |
        v
+-----------------------------------------------+
|  Stage 1   Tests              pytest          |
+-----------------------------------------------+
        |
        v  [Gate 1 - fails on any test failure]
+-----------------------------------------------+
|  Stage 2   SAST               Bandit + CodeQL |
+-----------------------------------------------+
        |
        v  [Gate 2 - fails on HIGH severity]
+-----------------------------------------------+
|  Stage 3   SCA + Secrets      Snyk + Gitleaks |
+-----------------------------------------------+
        |
        v  [Gate 3 - fails on HIGH CVE or any secret]
+-----------------------------------------------+
|  Stage 4   Container Scan     Trivy            |
+-----------------------------------------------+
        |
        v  [Gate 4 - fails on CRITICAL CVE]
+-----------------------------------------------+
|  Stage 5   Build + Push       Docker + ACR     |
+-----------------------------------------------+
        |
        v
Azure Container Registry
(image tagged :sha + :latest)
```

Each stage has a hard dependency on the previous one via `needs:`. A failure at any gate blocks all downstream stages. Code is stopped at the source.

---

## Security Stages

| Stage | Tool | Catches | Blocks On |
|-------|------|---------|-----------|
| Tests | pytest | Broken functionality | Any test failure |
| SAST | Bandit | Python security patterns: injection, unsafe calls, hardcoded credentials | HIGH severity |
| SAST | CodeQL | Deep data flow vulnerabilities across function boundaries | Any finding |
| SCA | Snyk | Known CVEs in Python dependencies | HIGH severity |
| Secrets | Gitleaks | Committed API keys, tokens, passwords including git history | Any finding |
| Container | Trivy | OS and library CVEs in the built Docker image | CRITICAL CVEs |

---

## Security Gate Demo

When vulnerable code is pushed:

```
Stage 1   Tests              passed in 18s
Stage 2   SAST               FAILED: HIGH severity - command injection detected

Stage 3   SCA + Secrets      skipped
Stage 4   Container Scan     skipped
Stage 5   Build + Push       skipped

Code was blocked. Image never reached ACR.
```

---


## Key Design Decisions

The full reasoning behind every tool and architectural choice is in [DECISIONS.md](./DECISIONS.md).

Summary:

- **Gate chain over parallel jobs** so failures stop the pipeline at the earliest possible point
- **Bandit and CodeQL together** because they operate at different depths and catch different vulnerability classes
- **Snyk over pip-audit** for real-time CVE database coverage and fix guidance
- **Gitleaks scans git history** not just the current commit, catching credentials deleted but never truly removed
- **Non-root Docker user** to limit blast radius if the application is compromised
- **Commit SHA image tagging** for full traceability from running container back to exact commit

---

## Tech Stack

| Tool | Category | Purpose |
|------|----------|---------|
| GitHub Actions | CI/CD | Pipeline orchestration |
| pytest | Testing | Automated test execution |
| Bandit | SAST | Python security pattern scanning |
| CodeQL | SAST | Semantic data flow analysis |
| Snyk | SCA | Dependency vulnerability scanning |
| Gitleaks | Secrets | Git history secret detection |
| Trivy | Container | Image vulnerability scanning |
| Docker | Containerization | Non-root slim image |
| Azure Container Registry | Registry | Private image storage |

---

## Run Locally

```bash
git clone https://github.com/pavank-kodag/DevSecOps-Pipeline.git
cd DevSecOps-Pipeline

# Install dependencies
pip install -r app/requirements.txt

# Run tests
pytest app/tests/ -v

# Run security scan locally
pip install bandit
bandit -r app/

# Build and run Docker image
docker build -t devsecops-app .
docker run -p 5000:5000 devsecops-app

# Verify
curl localhost:5000/health
```

---

## Setup

### GitHub Secrets Required

Go to Settings > Secrets and variables > Actions and add the following:

| Secret | Value |
|--------|-------|
| `ACR_LOGIN_SERVER` | yourregistry.azurecr.io |
| `ACR_USERNAME` | ACR admin username from Azure Portal |
| `ACR_PASSWORD` | ACR admin password from Azure Portal |
| `SNYK_TOKEN` | API token from snyk.io account settings |

### Azure Infrastructure

```bash
# Resource group
az group create --name devsecops-rg --location eastus

# Container Registry
az acr create \
  --name yourregistry \
  --resource-group devsecops-rg \
  --sku Basic \
  --admin-enabled true
```

---

## Project Structure

```
DevSecOps-Pipeline/
├── .github/
│   └── workflows/
│       └── pipeline.yml      # 5-stage CI/CD pipeline definition
├── app/
│   ├── app.py                # Flask application
│   ├── requirements.txt      # Python dependencies
│   └── tests/
│       └── test_app.py       # pytest test suite
├── Dockerfile                # Non-root, python:3.11-slim base
├── DECISIONS.md              # Architecture decision records
└── README.md
```

---

## License

MIT

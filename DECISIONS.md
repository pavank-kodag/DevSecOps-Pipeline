# Architecture Decision Records

Every significant technical choice in this project is documented here with context and reasoning. These reflect production thinking about tradeoffs, not tutorial defaults.

---

## ADR 1: Gate Chain Architecture

**Decision:** Each pipeline stage depends on the previous one using `needs:`. Failure at any stage blocks all downstream stages.

**Reasoning:** Running all security stages in parallel produces reports but does not prevent deployment. A HIGH severity code vulnerability found in Stage 2 should stop the image from being built and pushed in Stage 5. The purpose of security scanning in a pipeline is enforcement, not observation.

**Tradeoff:** Sequential execution takes longer than parallel. This is an acceptable cost because the security guarantee is the point.

---

## ADR 2: Bandit and CodeQL Together

**Decision:** Run both Bandit and CodeQL for static analysis rather than either alone.

**Reasoning:** These tools operate at fundamentally different depths.

Bandit performs fast pattern matching against known dangerous constructs specific to Python: `subprocess` with `shell=True`, `eval()`, use of weak cryptography, hardcoded credentials. It runs in seconds and catches common mistakes immediately.

CodeQL performs semantic, data flow analysis. It traces how untrusted input moves through the application across multiple function calls and identifies vulnerabilities that pattern matching cannot detect. A SQL injection that passes through five functions before reaching the database call is invisible to Bandit and visible to CodeQL.

Using only one leaves a gap. Using both is standard at enterprise security teams.

---

## ADR 3: Snyk for Dependency Scanning

**Decision:** Use Snyk over pip-audit or Safety.

**Reasoning:** Snyk queries multiple vulnerability databases simultaneously including NVD, GitHub Advisory, and its own proprietary database. Its output includes the exact remediation path, not just the finding. It updates in near real-time including zero-day disclosures.

pip-audit covers only the OSV database. Safety requires a paid license for current data. Snyk is free for open-source projects and provides broader coverage and actionable output.

---

## ADR 4: Gitleaks Scans Entire Git History

**Decision:** Use Gitleaks rather than a pre-commit hook or current-state scan only.

**Reasoning:** Secrets committed to git history remain accessible even after deletion. A developer who commits an API key and immediately removes it in the next commit has not removed it from the repository. Anyone with repository access can retrieve it from history using `git log`.

Gitleaks scans the complete commit history on every pipeline run. This catches credentials from weeks or months ago that were assumed to be gone. This is a common vector for real breaches.

---

## ADR 5: Trivy with Two Separate Runs

**Decision:** Run Trivy twice in Stage 4: once with `exit-code: 1` on CRITICAL to block the pipeline, and once in SARIF format to upload a full report as an artifact.

**Reasoning:** These serve different purposes.

The first run is enforcement. It fails the pipeline if CRITICAL CVEs are present, preventing the image from being pushed.

The second run is visibility. It produces a complete vulnerability report including non-critical findings that the team should be aware of and plan to address. Uploading this as an artifact means it is available for review without blocking the pipeline on lower-severity issues.

Combining both in a single run would force a choice between blocking too aggressively or losing the full report.

---

## ADR 6: Non-Root User in Docker Container

**Decision:** Create and switch to a non-root `appuser` before running the application.

**Reasoning:** Docker runs processes as root inside containers by default. If an attacker exploits a vulnerability in the application and achieves code execution, they gain root privileges inside the container. Root inside a container can attempt privilege escalation, modify system files, and use known container escape techniques.

A non-root user limits the blast radius. The attacker gets only `appuser` permissions: no package installation, no system file modification, no escalation paths that require root.

This costs nothing and is a standard production security practice.

---

## ADR 7: python:3.11-slim Base Image

**Decision:** Use `python:3.11-slim` rather than the full `python:3.11` image.

**Reasoning:** The full Python image ships with compilers, build tools, documentation, and package managers. None of these are needed at runtime. Every additional package is a potential vulnerability surface that Trivy will scan and flag.

`python:3.11-slim` contains only the Python runtime. Image size drops from approximately 900MB to 45MB. Smaller image means fewer packages, fewer CVE findings, faster Trivy scans, and faster pulls in production.

This directly reduces the noise in Stage 4 container scanning results.

---

## ADR 8: Commit SHA Image Tagging

**Decision:** Tag every image with the git commit SHA in addition to `:latest`.

**Reasoning:** Using only `:latest` breaks traceability. When a production incident occurs, the first question is: what code is running? With `:latest` only, there is no way to answer that from the image tag alone.

Tagging with `${{ github.sha }}` means every image is permanently linked to the exact commit, pull request, author, and timestamp that produced it. `docker inspect` on any running container returns the SHA, and from there the full audit trail is available in GitHub.

Both tags are pushed: `:latest` for convenience, `:sha` for accountability.

---

## ADR 9: GitHub Actions over Jenkins

**Decision:** Use GitHub Actions rather than Jenkins or any other CI system.

**Reasoning:** Jenkins requires provisioning and maintaining a separate server, managing a plugin ecosystem, and handling security updates for the CI infrastructure itself. This is operational overhead that adds no value to the security pipeline.

GitHub Actions is serverless, native to where the code lives, and free for public repositories. Every workflow run executes in a fresh isolated VM with no state from previous runs. There are no plugin compatibility issues and no server to maintain.

For a project already hosted on GitHub, introducing a separate CI system creates an unnecessary tool gap.

---

## ADR 10: Security Scanning Before Build

**Decision:** Run all security scanning stages before building the Docker image.

**Reasoning:** Build time is the most expensive part of the pipeline. Running source code and dependency scans before building means that a HIGH severity finding discovered in Stage 2 terminates the pipeline before any compute is spent on Stage 5.

Cheapest checks run first. Most expensive runs last. A vulnerability found at source costs seconds. A vulnerability found after a multi-minute build and push wastes time and leaves an insecure image in the registry requiring cleanup.

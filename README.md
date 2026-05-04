# SwiftDeploy

SwiftDeploy is a declarative Infrastructure as Code (IaC) CLI tool designed to programmatically generate, deploy, and manage a containerized stack from a single source of truth (`manifest.yaml`).

## Architecture
- **API Service:** A lightweight Python/Flask application running via Gunicorn. Features a dynamic `/chaos` endpoint and mode-aware headers.
- **Reverse Proxy:** Nginx, configured for custom JSON error handling and ISO8601 access logging.
- **CLI Engine:** A Python-based automation tool utilizing Jinja2 templating for dynamic configuration generation.

## Setup Instructions
1. Clone the repository.
2. Ensure Docker and Docker Compose are installed and running.
3. Build the base application image:
   ```bash
   docker build -t swift-deploy-1-node:latest . 
   ```
4. Install CLI dependencies:
   ```bash
   pip install pyyaml jinja2 
   ```

## Subcommand Walkthrough

* **`python swiftdeploy init`**
  Parses `manifest.yaml` and injects the variables into Jinja2 templates, generating the `docker-compose.yml` and `nginx.conf` files.

* **`python swiftdeploy validate`**
  Executes pre-flight checks:
  1. Verifies manifest syntax and required fields.
  2. Confirms the target Docker image exists locally.
  3. Checks if the host port is available.
  4. Spawns an isolated Docker container to test the generated `nginx.conf` syntax.

* **`python swiftdeploy deploy`**
  Generates configurations, executes a detached Docker Compose deployment, and polls the API `/healthz` endpoint until the stack reports healthy.

* **`python swiftdeploy promote [canary|stable]`**
  Updates the manifest in-place, regenerates configs, and performs a zero-downtime rolling restart of *only* the API service container to switch environments.

* **`python swiftdeploy teardown [--clean]`**
  Destroys all running containers, networks, and volumes. The optional `--clean` flag deletes the generated configuration files.
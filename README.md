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
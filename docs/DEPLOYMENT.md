# Workload Web App - Deployment Guide

This document explains how to deploy the Workload Cost Calculation application using Docker.
The application is split into a **FastAPI backend** and a **Vite + React frontend**, managed together using Docker Compose.

## Prerequisites
- **Docker** and **Docker Compose** installed on your server or local machine.

## Architecture
- **Backend (`workload_backend`)**: A Python container running FastAPI via Uvicorn on internal port `8001`.
- **Frontend (`workload_frontend`)**: An Nginx container that serves the compiled static React files on port `80` and proxies any requests starting with `/api` to the backend container.

## 🚀 How to Deploy

### 1. Build and Start the Containers
Navigate to the root directory of the project (where `docker-compose.yml` is located) and run:

```bash
docker-compose up -d --build
```
- `-d`: Runs the containers in the background (detached mode).
- `--build`: Forces Docker to build the images based on the latest code.

### 2. Access the Application
Once the containers are running, open your web browser and go to:
- **http://localhost** (or your server's IP address)

The frontend will load, and it will automatically communicate with the backend securely through Nginx.

### 3. Updating Data Files (Excel)
Notice in `docker-compose.yml`, the `data` folder is mounted as a volume to the backend container:
```yaml
    volumes:
      - ./data:/app/data
```
This means you can update the Excel files in the `data/` folder on your host machine, and the backend container will immediately see the new files. You do **not** need to rebuild the Docker image just to update data files!

## Helpful Docker Commands

**View Logs:**
To see what's happening inside the containers (useful for debugging):
```bash
docker-compose logs -f
```

**Stop the Application:**
```bash
docker-compose down
```

**Rebuild after changing code:**
If you modify Python code (`src/` or `main.py`) or React code (`frontend/src/`):
```bash
docker-compose up -d --build
```

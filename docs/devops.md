# DevOps setup: Docker, Jenkins and Kubernetes

This guide reproduces the CI/CD pipeline of the project on a laptop. Everything runs in
containers, so the only requirement is Docker (Docker Desktop on macOS and Windows, or Docker
Engine on Linux). Minikube and kubectl are needed only for the optional Kubernetes step.

## 1. The application image

```bash
docker build -t agrotrust-metrics .
docker run --rm agrotrust-metrics --version
docker run --rm agrotrust-metrics simulate --nodes 3 --days 2 --out /tmp/data
docker run --rm -p 8000:8000 agrotrust-metrics serve     # open http://localhost:8000
```

The `Dockerfile` has two stages. The first builds a wheel from the sources, the second installs
only that wheel into a clean `python:3.12-slim` image and runs as an unprivileged user (uid 10001).
`serve` simulates a 14-node greenhouse, builds the HTML reliability report and serves it on port 8000.

## 2. Start Jenkins

```bash
cd jenkins
docker compose up -d --build
docker compose logs -f jenkins      # wait for "Jenkins is fully up and running", then Ctrl+C
```

Open <http://localhost:8080> and log in as `admin` / `admin` (set `JENKINS_ADMIN_PASSWORD`
before `docker compose up` to choose another password).

What the setup does:

- `jenkins/Dockerfile` extends the official `jenkins/jenkins:lts-jdk21` image with Python, Git,
  the Docker CLI and the plugins from `plugins.txt`.
- `jenkins/casc.yaml` (Configuration as Code) creates the admin user and the pipeline job
  `agrotrust`, which reads the `Jenkinsfile` from the `main` branch of this repository. The setup
  wizard is skipped, so no manual configuration is needed.
- The host Docker socket is mounted into the container, so the pipeline builds images and starts
  the test server on the host Docker engine.

## 3. Run the pipeline

1. Open the job `agrotrust` and press **Build Now** once. The first run also registers the
   parameters and the commit trigger.
2. From then on Jenkins checks GitHub every 2 minutes (`pollSCM`) and builds every new commit on
   `main`. A webhook is not used because GitHub cannot reach a laptop.
3. Stages: Checkout, Set up Python, Lint, Unit tests (JUnit report), Build Docker image,
   Smoke test image, Push to Docker Hub (optional), Deploy to test server.
4. After a green build the new version is running at <http://localhost:8000>.

Screenshots for the report: the stage view of the job, the console log of a build, the
**Test Result** page with 53 tests, `docker image ls agrotrust-metrics` in a terminal, and the
report page on port 8000.

### Optional: push to Docker Hub

1. Create an access token at hub.docker.com (Account settings, Personal access tokens).
2. In Jenkins: Manage Jenkins, Credentials, System, Global credentials, Add credentials:
   kind *Username with password*, ID `dockerhub`, username = Docker Hub login, password = token.
3. Build with parameters: tick `PUSH_IMAGE` and set `DOCKERHUB_REPO` to `<login>/agrotrust-metrics`.

## 4. Optional: deploy to Kubernetes (Minikube)

```bash
brew install minikube kubectl        # macOS; see minikube.sigs.k8s.io for other systems
./deploy/minikube.sh
```

The script starts Minikube, builds the image, loads it into the cluster, applies `k8s/` (a
Deployment with readiness and liveness probes and a NodePort Service) and prints the URL of
the report.

## 5. Stop everything

```bash
docker rm -f agrotrust-test
cd jenkins && docker compose down          # add -v to delete the Jenkins data volume
minikube stop
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `permission denied ... docker.sock` in the build log | Start Jenkins with the provided compose file (it runs as root inside the container). |
| Port 8080 or 8000 already in use | Change the left side of `ports` in `jenkins/docker-compose.yml`, or stop the other program. |
| The job does not start on a new commit | Run **Build Now** once; polling starts after the first build. |
| `docker: not found` in the pipeline | Rebuild the Jenkins image: `docker compose build --no-cache`. |

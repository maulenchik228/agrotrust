// CI/CD pipeline for agrotrust-metrics.
// Runs on every new commit (the job polls GitHub, see jenkins/casc.yaml):
// lint -> unit tests -> Docker image -> smoke test -> optional push -> deploy to the test server.

pipeline {
    agent any

    parameters {
        booleanParam(name: 'PUSH_IMAGE', defaultValue: false,
                     description: 'Push the image to Docker Hub (needs the dockerhub credential)')
        string(name: 'DOCKERHUB_REPO', defaultValue: 'maulenchik228/agrotrust-metrics',
               description: 'Docker Hub repository for the push stage')
        booleanParam(name: 'DEPLOY_TEST', defaultValue: true,
                     description: 'Deploy the new image to the local test server (port 8000)')
    }

    triggers {
        // GitHub cannot reach a laptop, so Jenkins checks the repository every 2 minutes
        // and starts a build for every new commit on main
        pollSCM('H/2 * * * *')
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        IMAGE = 'agrotrust-metrics'
        TAG = "${env.BUILD_NUMBER}"
        TEST_CONTAINER = 'agrotrust-test'
    }

    stages {
        stage('Checkout') {
            steps {
                // the code is already checked out by Declarative; show which commit is built
                sh 'git log -1 --pretty=format:"%h %an: %s"'
            }
        }

        stage('Set up Python') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --quiet --upgrade pip
                    pip install --quiet -e ".[dev]"
                    python --version
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '. .venv/bin/activate && ruff check . && ruff format --check .'
            }
        }

        stage('Unit tests') {
            steps {
                sh '''
                    . .venv/bin/activate
                    mkdir -p reports
                    pytest --junitxml=reports/junit.xml \
                           --cov=agrotrust_metrics --cov-report=xml:reports/coverage.xml \
                           --cov-report=term
                '''
            }
            post {
                always {
                    junit 'reports/junit.xml'
                }
            }
        }

        stage('Build Docker image') {
            steps {
                sh '''
                    docker build \
                        --label org.opencontainers.image.revision="$(git rev-parse HEAD)" \
                        -t "$IMAGE:$TAG" -t "$IMAGE:latest" .
                    docker image ls "$IMAGE"
                '''
            }
        }

        stage('Smoke test image') {
            steps {
                sh '''
                    docker run --rm "$IMAGE:$TAG" --version
                    docker run --rm "$IMAGE:$TAG" simulate --nodes 3 --days 2 --out /tmp/data
                '''
            }
        }

        stage('Push to Docker Hub') {
            when { expression { params.PUSH_IMAGE } }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub',
                                                  usernameVariable: 'DOCKERHUB_USER',
                                                  passwordVariable: 'DOCKERHUB_TOKEN')]) {
                    sh '''
                        echo "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USER" --password-stdin
                        docker tag "$IMAGE:$TAG" "$DOCKERHUB_REPO:$TAG"
                        docker tag "$IMAGE:$TAG" "$DOCKERHUB_REPO:latest"
                        docker push "$DOCKERHUB_REPO:$TAG"
                        docker push "$DOCKERHUB_REPO:latest"
                    '''
                }
            }
            post {
                always { sh 'docker logout || true' }
            }
        }

        stage('Deploy to test server') {
            when { expression { params.DEPLOY_TEST } }
            steps {
                sh '''
                    docker rm -f "$TEST_CONTAINER" 2>/dev/null || true
                    docker run -d --name "$TEST_CONTAINER" --restart unless-stopped \
                        -p 8000:8000 "$IMAGE:$TAG" serve
                    check='import urllib.request; urllib.request.urlopen("http://127.0.0.1:8000/")'
                    for i in $(seq 1 60); do
                        if docker exec "$TEST_CONTAINER" python -c "$check" 2>/dev/null; then
                            echo "Test server is up: http://localhost:8000 (build $TAG)"
                            exit 0
                        fi
                        sleep 2
                    done
                    docker logs "$TEST_CONTAINER"
                    echo "Test server did not become healthy" >&2
                    exit 1
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true, fingerprint: true
        }
        success {
            echo "Build ${env.BUILD_NUMBER}: image ${env.IMAGE}:${env.TAG} is tested and deployed."
        }
        failure {
            echo 'Pipeline failed. See the stage logs above.'
        }
    }
}

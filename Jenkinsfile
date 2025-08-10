pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'docker.io'
        IMAGE_NAME = 'sre-microservice'
        KUBECONFIG = credentials('kubeconfig-credentials')
        DOCKER_CREDENTIALS = credentials('docker-hub-credentials')
        NAMESPACE = 'sre-microservice'
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        skipStagesAfterUnstable()
    }
    
    stages {
        stage('Preparation') {
            steps {
                script {
                    env.BUILD_DATE = sh(returnStdout: true, script: 'date -u +"%Y-%m-%dT%H:%M:%SZ"').trim()
                    env.GIT_COMMIT = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
                    env.BUILD_VERSION = sh(returnStdout: true, script: 'git describe --tags --always --dirty').trim()
                    env.IMAGE_TAG = "${env.BUILD_VERSION}-${env.BUILD_NUMBER}"
                }
                
                echo "Starting CI/CD Pipeline for SRE Microservice"
                echo "Build Version: ${env.BUILD_VERSION}"
                echo "Image Tag: ${env.IMAGE_TAG}"
                
                // Clean workspace
                cleanWs()
                
                // Checkout code
                checkout scm
            }
        }
        
        stage('Code Quality & Security') {
            parallel {
                stage('Lint & Format Check') {
                    steps {
                        sh '''
                            python -m pip install --upgrade pip
                            pip install flake8 black isort
                            
                            echo "Running code formatting checks..."
                            black --check src/
                            
                            echo "Running import sorting checks..."
                            isort --check-only src/
                            
                            echo "Running linting..."
                            flake8 src/ --max-line-length=88 --ignore=E203,W503
                        '''
                    }
                }
                
                stage('Security Scan - Source Code') {
                    steps {
                        sh '''
                            pip install bandit safety
                            
                            echo "Running security scan on source code..."
                            bandit -r src/ -f json -o bandit-report.json || true
                            
                            echo "Checking for known vulnerabilities in dependencies..."
                            safety check --json --output safety-report.json || true
                        '''
                        
                        archiveArtifacts artifacts: '*-report.json', allowEmptyArchive: true
                    }
                }
            }
        }
        
        stage('Build & Test') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        sh '''
                            pip install -r requirements.txt
                            python -m pytest src/tests/ -v \
                                --cov=src/app \
                                --cov-report=xml:coverage.xml \
                                --cov-report=html:htmlcov \
                                --cov-report=term \
                                --junitxml=test-results.xml
                        '''
                        
                        publishTestResults testResultsPattern: 'test-results.xml'
                        publishHTML([
                            allowMissing: false,
                            alwaysLinkToLastBuild: true,
                            keepAll: true,
                            reportDir: 'htmlcov',
                            reportFiles: 'index.html',
                            reportName: 'Coverage Report'
                        ])
                    }
                }
                
                stage('Build Docker Image') {
                    steps {
                        script {
                            def dockerImage = docker.build("${IMAGE_NAME}:${IMAGE_TAG}", 
                                "--build-arg BUILD_DATE='${env.BUILD_DATE}' " +
                                "--build-arg VERSION='${env.BUILD_VERSION}' " +
                                "--build-arg VCS_REF='${env.GIT_COMMIT}' .")
                            
                            env.DOCKER_IMAGE_ID = dockerImage.id
                        }
                    }
                }
            }
        }
        
        stage('Container Security Scan') {
            steps {
                script {
                    try {
                        sh '''
                            # Install Trivy if not available
                            if ! command -v trivy &> /dev/null; then
                                wget https://github.com/aquasecurity/trivy/releases/latest/download/trivy_Linux-64bit.tar.gz
                                tar zxvf trivy_Linux-64bit.tar.gz
                                sudo mv trivy /usr/local/bin/
                            fi
                            
                            echo "Running container security scan..."
                            trivy image --format json --output trivy-report.json ${IMAGE_NAME}:${IMAGE_TAG}
                            trivy image --severity HIGH,CRITICAL ${IMAGE_NAME}:${IMAGE_TAG}
                        '''
                    } catch (Exception e) {
                        echo "Trivy scan failed: ${e.getMessage()}"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
                
                archiveArtifacts artifacts: 'trivy-report.json', allowEmptyArchive: true
            }
        }
        
        stage('Integration Tests') {
            steps {
                script {
                    try {
                        sh '''
                            echo "Starting container for integration tests..."
                            docker run -d --name test-container -p 8080:8000 ${IMAGE_NAME}:${IMAGE_TAG}
                            
                            # Wait for service to be ready
                            timeout 60 bash -c 'until curl -f http://localhost:8080/health; do sleep 2; done'
                            
                            echo "Running integration tests..."
                            
                            # Test health endpoint
                            curl -f http://localhost:8080/health
                            
                            # Test ready endpoint
                            curl -f http://localhost:8080/ready
                            
                            # Test payload endpoint
                            curl -f -X POST -H "Content-Type: application/json" \
                                -d '{"numbers": [1,2,3,4,5], "text": "Integration test"}' \
                                http://localhost:8080/payload
                            
                            # Test metrics endpoint
                            curl -f http://localhost:8080/metrics
                            
                            echo "Integration tests passed!"
                        '''
                    } catch (Exception e) {
                        echo "Integration tests failed: ${e.getMessage()}"
                        currentBuild.result = 'FAILURE'
                        error("Integration tests failed")
                    } finally {
                        sh 'docker stop test-container && docker rm test-container || true'
                    }
                }
            }
        }
        
        stage('Push to Registry') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                    buildingTag()
                }
            }
            steps {
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", "${DOCKER_CREDENTIALS}") {
                        def image = docker.image("${IMAGE_NAME}:${IMAGE_TAG}")
                        image.push()
                        image.push("latest")
                    }
                }
            }
        }
        
        stage('Deploy to Kubernetes') {
            when {
                branch 'main'
            }
            steps {
                script {
                    try {
                        sh '''
                            echo "Deploying to Kubernetes..."
                            
                            # Update image tag in deployment
                            sed -i "s|image: sre-microservice:latest|image: ${IMAGE_NAME}:${IMAGE_TAG}|g" k8s/deployment.yaml
                            
                            # Apply manifests
                            kubectl apply -f k8s/
                            
                            # Wait for rollout to complete
                            kubectl rollout status deployment/sre-microservice -n ${NAMESPACE} --timeout=300s
                            
                            echo "Deployment successful!"
                        '''
                    } catch (Exception e) {
                        echo "Deployment failed: ${e.getMessage()}"
                        currentBuild.result = 'FAILURE'
                        error("Deployment failed")
                    }
                }
            }
        }
        
        stage('Load Testing') {
            when {
                branch 'main'
            }
            steps {
                script {
                    try {
                        sh '''
                            echo "Getting service URL..."
                            SERVICE_IP=$(kubectl get service sre-microservice-service -n ${NAMESPACE} -o jsonpath='{.spec.clusterIP}')
                            SERVICE_URL="http://${SERVICE_IP}"
                            
                            echo "Running load tests against ${SERVICE_URL}..."
                            chmod +x scripts/load-test.sh
                            ./scripts/load-test.sh ${SERVICE_URL} 100 10
                        '''
                        
                        archiveArtifacts artifacts: 'test-results/**', allowEmptyArchive: true
                        
                        publishHTML([
                            allowMissing: false,
                            alwaysLinkToLastBuild: true,
                            keepAll: true,
                            reportDir: 'test-results',
                            reportFiles: 'load-test-report.txt',
                            reportName: 'Load Test Report'
                        ])
                        
                    } catch (Exception e) {
                        echo "Load testing failed: ${e.getMessage()}"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }
        
        stage('Rollback Simulation') {
            when {
                anyOf {
                    branch 'main'
                    expression { params.SIMULATE_ROLLBACK == true }
                }
            }
            steps {
                script {
                    try {
                        sh '''
                            echo "Simulating rollback scenario..."
                            
                            # Get current deployment
                            CURRENT_IMAGE=$(kubectl get deployment sre-microservice -n ${NAMESPACE} -o jsonpath='{.spec.template.spec.containers[0].image}')
                            echo "Current image: ${CURRENT_IMAGE}"
                            
                            # Simulate a problematic deployment
                            kubectl set image deployment/sre-microservice sre-microservice=nginx:invalid -n ${NAMESPACE}
                            
                            # Wait a bit and check rollout status
                            sleep 10
                            
                            # Check if rollout is failing
                            if ! kubectl rollout status deployment/sre-microservice -n ${NAMESPACE} --timeout=60s; then
                                echo "Rollout failed, initiating rollback..."
                                kubectl rollout undo deployment/sre-microservice -n ${NAMESPACE}
                                kubectl rollout status deployment/sre-microservice -n ${NAMESPACE} --timeout=180s
                                echo "Rollback completed successfully!"
                            else
                                echo "Rollout unexpectedly succeeded, reverting..."
                                kubectl set image deployment/sre-microservice sre-microservice=${CURRENT_IMAGE} -n ${NAMESPACE}
                            fi
                        '''
                    } catch (Exception e) {
                        echo "Rollback simulation failed: ${e.getMessage()}"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }
    }
    
    post {
        always {
            script {
                // Collect logs
                sh '''
                    mkdir -p logs
                    kubectl logs -l app=sre-microservice -n ${NAMESPACE} --tail=1000 > logs/application.log || true
                    kubectl describe deployment sre-microservice -n ${NAMESPACE} > logs/deployment-info.txt || true
                    kubectl get events -n ${NAMESPACE} > logs/k8s-events.txt || true
                '''
                
                archiveArtifacts artifacts: 'logs/**', allowEmptyArchive: true
            }
            
            // Clean up Docker images
            sh 'docker image prune -f || true'
            
            // Send notifications
            emailext (
                subject: "Pipeline ${currentBuild.result}: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: """
                Pipeline execution completed with status: ${currentBuild.result}
                
                Job: ${env.JOB_NAME}
                Build: ${env.BUILD_NUMBER}
                Duration: ${currentBuild.durationString}
                
                Build URL: ${env.BUILD_URL}
                """,
                recipientProviders: [developers(), requestor()]
            )
        }
        
        success {
            echo 'Pipeline completed successfully!'
        }
        
        failure {
            echo 'Pipeline failed!'
        }
        
        unstable {
            echo 'Pipeline completed with warnings!'
        }
    }
}
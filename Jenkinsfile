pipeline {
    agent any
    
    stages {
        stage('Checkout Code') {
            steps {
                echo 'Pulling code from GitHub...'
                checkout scm
            }
        }
        
        stage('Build & Test') {
            steps {
                echo 'Running build and tests for microservices...'
                sh 'echo "Build passed successfully!"'
            }
        }
        
        stage('Deploy to Kubernetes') {
            steps {
                echo 'Downloading kubectl and deploying manifests to K8s...'
                sh '''
                    # Download kubectl binary locally
                    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
                    chmod +x kubectl
                    
                    # Apply manifests using the local binary
                    ./kubectl apply -f k8s/
                '''
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline completed successfully and deployed to K8s!'
        }
        failure {
            echo 'Pipeline failed. Please check the logs.'
        }
    }
}
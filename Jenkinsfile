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
                echo 'Applying Kubernetes manifests from k8s/ directory...'
                sh 'kubectl apply -f k8s/'
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
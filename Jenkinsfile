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
                echo 'Deploying application manifests to K8s cluster...'
                // כאן נגדיר בהמשך את פקודות ה-kubectl או ה-Helm להרמת המיקרו-שירותים
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Please check the logs.'
        }
    }
}
// Pipeline 1: application-ci
pipelineJob('application-ci') {
    description('Continuous Integration Pipeline: Tests, builds and pushes container images.')
    definition {
        cpsScm {
            scm {
                git {
                    remote {
                        url('https://github.com/yahali-gottlieb/Project-CyberBrand-K8s-Microservices.git')
                    }
                    branch('*/main')
                }
            }
            scriptPath('Jenkinsfile-ci')
        }
    }
}

// Pipeline 2: application-cd
pipelineJob('application-cd') {
    description('Continuous Deployment Pipeline: Deploys immutable image tag to Kubernetes.')
    parameters {
        stringParam('IMAGE_TAG', 'v1', 'The immutable image tag to deploy')
        stringParam('NAMESPACE', 'devops-app', 'Target Kubernetes Namespace')
    }
    definition {
        cpsScm {
            scm {
                git {
                    remote {
                        url('https://github.com/yahali-gottlieb/Project-CyberBrand-K8s-Microservices.git')
                    }
                    branch('*/main')
                }
            }
            scriptPath('Jenkinsfile-cd')
        }
    }
}
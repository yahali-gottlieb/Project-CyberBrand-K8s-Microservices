# Project-CyberBrand-K8s-Microservices

**Author:** Yahali
**Assignment:** DevOps on AWS - Task 3 & Task 4 (Kubernetes & Jenkins CI/CD)

## Project Overview
This project transitions our 3-tier cloud application into a modern containerized environment using **Docker** and **Kubernetes**, and introduces a fully automated **Jenkins CI/CD Pipeline**.
We migrated from running services directly on standalone EC2 instances to deploying them as containerized Pods within a local Kubernetes cluster (k3d), integrating securely with AWS managed services (RDS, S3, and SNS).

The primary goal of this phase is to establish a robust, highly available, dynamically scaling, and deeply secured architecture using Infrastructure as Code (IaC), GitOps principles, and Kubernetes best practices.

---

## Architecture & Traffic Flow
The system is deployed on a local k3d Kubernetes cluster representing an On-Premise environment, integrated with AWS Cloud Services.

### 1. Application Traffic Flow — Namespace: `devops-app`
*   **Public Internet → Ingress:** External users can only reach the Kubernetes Ingress Controller via HTTP.
*   **Ingress → Frontend:** The Ingress routes external traffic exclusively to the `frontend` Service.
*   **Frontend → Backend:** The Frontend Nginx server acts as a reverse proxy, forwarding specific API calls (`/api/`) internally to the `backend` Service. External users cannot reach the backend directly.
*   **Backend → RDS:** The Backend pod communicates outbound to the external AWS RDS PostgreSQL database on Port 5432 for reading and writing game scores.
*   **Worker → AWS Services:** The Worker pod has no inbound communication. It is a scheduled process that communicates outbound to:
    *   **AWS RDS PostgreSQL** — Port 5432
    *   **AWS S3** — HTTPS 443
    *   **AWS SNS** — HTTPS 443

### 2. CI/CD Pipeline Flow — Namespace: `jenkins`
*   **Continuous Integration (`application-ci`):** Triggered automatically by a Git `pollSCM` mechanism. Runs on an ephemeral Docker-in-Docker (DinD) agent. It builds the Docker images, assigns an immutable tag (`BUILD_NUMBER-COMMIT_SHA`), and pushes them to Docker Hub.
*   **Continuous Deployment (`application-cd`):** Triggered by the CI pipeline. Runs on an ephemeral alpine/k8s agent. It securely applies the Kubernetes manifests and updates the target deployments using the immutable image tag.

---

## Deep Security Implementation
A significant portion of this project focuses on securing the Kubernetes cluster and the CI/CD flow, directly addressing previous security reviews.

### 1. Privilege Separation — Service Accounts & RBAC
*   **Application Service Accounts:** Dedicated Service Accounts are used:
    *   `frontend-sa`
    *   `backend-sa`
    *   `worker-sa`
    *   *The Backend explicitly does not receive AWS credentials, adhering to the principle of Least Privilege.*
*   **Jenkins CD Agent:** The CD deployment runs under `cd-agent-sa`, which is strictly scoped to the `devops-app` namespace via a RoleBinding.
    *   *No cluster-admin rights are used.*

### 2. Zero-Trust Network Policies
*   **Default Deny:** A strict `NetworkPolicy` enforces a Default Deny for all Ingress and Egress traffic in the `devops-app` namespace.
*   **Explicit Allowances:** Rules explicitly allow:
    *   DNS resolution
    *   Ingress traffic to the frontend
    *   Frontend-to-backend communication
    *   Backend/Worker access to AWS RDS on Port 5432
    *   Worker HTTPS access to AWS S3/SNS on Port 443

### 3. Secrets Management — Zero Hardcoded Secrets
*   Hardcoded database passwords were completely removed from Terraform and the Python codebase.
*   Passwords and credentials must be injected via Kubernetes Secrets and Terraform variables.
*   Example secrets (`secret.example.yaml`) have been moved to an `examples/` directory to prevent accidental overwrites during the automated `kubectl apply -f k8s/` CD rollout.
*   Sensitive credentials are never committed directly to Git.

### 4. Container & Image Security
*   **Immutable Image Tags:** We strictly avoid the `latest` tag in our deployments. Images are tagged using an immutable format: `BUILD_NUMBER-COMMIT_SHA`.
*   **Non-Root Execution:** All containers enforce `runAsNonRoot: true`.
    *   Backend/Worker run as UID 1000
    *   Nginx runs as UID 101
*   **Privilege Escalation:** Disabled across all containers using: `allowPrivilegeEscalation: false`.

---

## 🌟 Advanced Kubernetes Features

### Pod Disruption Budget — PDB
A Pod Disruption Budget (PDB) is configured for the backend to guarantee `minAvailable: 1`. This ensures that at least one backend replica remains available during voluntary cluster disruptions.

### Horizontal Pod Autoscaler — HPA
The frontend is configured with a Horizontal Pod Autoscaler (HPA). The HPA dynamically scales the frontend deployment between:
*   Minimum replicas: 1
*   Maximum replicas: 3
*   CPU target utilization: 70%

This allows the application to automatically respond to increased traffic and workload.

---

## 🚀 Instructions: How to Deploy from Scratch

### Prerequisites
Before starting, make sure the following tools are installed:
*   Docker & k3d
*   `kubectl` & Helm
*   Terraform
*   An active AWS Account & Docker Hub account

### Step 1: Provision AWS Infrastructure with Terraform
Navigate to the Terraform directory and create the AWS resources:
```bash
cd terraform
terraform init
# Provide a secure password for the RDS database
terraform apply -var="db_password=YOUR_SECURE_PASSWORD"
```

### Step 2: Bootstrap the Kubernetes Cluster
Create the local k3d Kubernetes cluster:
```bash
k3d cluster create devops-cluster -p "8080:80@loadbalancer"
```
Create the required Kubernetes namespaces:
```bash
kubectl apply -f k8s/01-namespace.yaml
```

### Step 3: Inject Secrets & Configurations
Update `k8s/02-configmap.yaml` with the AWS resources created by Terraform.
Create the Kubernetes Secret securely:
```bash
kubectl create secret generic devops-secrets -n devops-app \
  --from-literal=DB_USER=postgres \
  --from-literal=DB_PASS=YOUR_SECURE_PASSWORD \
  --from-literal=AWS_ACCESS_KEY_ID=YOUR_AWS_KEY \
  --from-literal=AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET
```
*Security Note: Never commit real AWS credentials, database passwords, or other secrets to Git.*

### Step 4: Install Jenkins via Helm & JCasC
Jenkins is installed and fully configured as code using Helm and Jenkins Configuration as Code (JCasC). No manual UI setup is required for plugins or jobs.
```bash
helm repo add jenkins [https://charts.jenkins.io](https://charts.jenkins.io)
helm repo update
helm upgrade --install jenkins jenkins/jenkins -n jenkins -f jenkins/values.yaml
```
Access Jenkins at `http://localhost:8080` (requires port-forwarding):
```bash
kubectl port-forward svc/jenkins 8080:8080 -n jenkins
```
Retrieve the Jenkins Admin Password:
```bash
kubectl exec --namespace jenkins -it svc/jenkins -c jenkins -- /bin/cat /run/secrets/additional/chart-admin-password && echo
```

### Step 5: Trigger the CI/CD Pipeline
The following Jenkins jobs are automatically created using Jenkins Job DSL: `application-ci` and `application-cd`.
Simply push a commit to the `main` branch of the repository. The `pollSCM` trigger will detect the change and start the CI/CD process.

#### CI Pipeline
1. Detects the Git change.
2. Starts an ephemeral Docker-in-Docker agent.
3. Checks out the source code & builds the Docker images.
4. Generates immutable image tags (`BUILD_NUMBER-COMMIT_SHA`).
5. Pushes the images to Docker Hub.
6. Triggers the CD pipeline.

#### CD Pipeline
1. Starts an ephemeral alpine/k8s agent.
2. Pulls the required image tag.
3. Applies the Kubernetes manifests.
4. Updates the Kubernetes deployments & performs the deployment rollout.
5. Runs the required smoke tests.

---

## 🛠️ Rollback Procedure
If a CD rollout fails or an incorrect version is deployed, Kubernetes provides a native rollback mechanism.
```bash
kubectl rollout undo deployment/backend -n devops-app
kubectl rollout undo deployment/frontend -n devops-app
```

---

## 🧹 Environment Cleanup
To safely tear down the entire environment:
```bash
k3d cluster delete devops-cluster
cd terraform && terraform destroy
```
*Warning: `terraform destroy` permanently removes the AWS infrastructure.*

---

## 📸 Project Screenshots

### Kubernetes Base — Task 3
1.  **Kubernetes Cluster Nodes:** `screenshots/nodes.png`
2.  **Namespaces:** `screenshots/namespaces.png`
3.  **Pods Status & Health:** `screenshots/pods-status.png`
4.  **Deployments Status:** `screenshots/deployments.png`
5.  **Services (ClusterIP):** `screenshots/services.png`
6.  **Ingress Controller:** `screenshots/ingress.png`
7.  **Self-Healing (Post-Delete):** `screenshots/pod-restart.png`
8.  **Frontend UI Running:** `screenshots/app-running.png`
9.  **AWS RDS (DB Available):** `screenshots/aws-rds.png`
10. **AWS S3 (Automated Report):** `screenshots/aws-s3-report.png`
11. **AWS SNS (Email Alert):** `screenshots/aws-sns-email.png`

### Jenkins CI/CD — Task 4
12. **Architecture Diagram:** `screenshots/architecture.png`
13. **Jenkins Jobs Created (JCasC):** `screenshots/jenkins-jobs.png`
14. **CI Pipeline Success (Blue Ocean / Console):** `screenshots/ci-success.png`
15. **CD Pipeline Success (Rollout & Smoke Test):** `screenshots/cd-success.png`
16. **Dynamic Agents Running in Kubernetes (`kubectl get pods -n jenkins`):** `screenshots/jenkins-agents.png`
17. **Docker Hub Immutable Tags:** `screenshots/docker-hub-tags.png`

---

## 🎯 Final Result
The completed architecture provides a secure and automated Kubernetes-based application platform with a fully integrated CI/CD pipeline.
The application is deployed into isolated Kubernetes namespaces, protected by RBAC and NetworkPolicies, uses dedicated Service Accounts and Kubernetes Secrets, runs containers as non-root users, and communicates with AWS managed services through explicitly defined network paths.
The Jenkins pipeline automates the complete lifecycle from Git commit → Docker build → immutable image → Docker Hub → Kubernetes deployment → rollout → smoke test, providing a repeatable and secure deployment process.
#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "Creating / Updating Jenkins Jobs via CLI..."
echo "=========================================="

# Ensure jenkins-cli.jar exists
if [ ! -f /tmp/jenkins-cli.jar ]; then
    echo "Downloading jenkins-cli.jar from Jenkins server..."
    curl -s http://localhost:8080/jnlpJars/jenkins-cli.jar -o /tmp/jenkins-cli.jar
fi

JENKINS_URL="http://localhost:8080"
JENKINS_USER="${JENKINS_ADMIN_USER:-admin}"
JENKINS_PASSWORD="${JENKINS_ADMIN_PASSWORD:-admin123}"

echo "Executing jobs.groovy against Jenkins..."
java -jar /tmp/jenkins-cli.jar -s "$JENKINS_URL" -auth "${JENKINS_USER}:${JENKINS_PASSWORD}" groovy = < jenkins/jobs.groovy || {
    echo "Applying jobs via kubectl pod execution..."
    kubectl exec -i -n jenkins jenkins-0 -c jenkins -- java -jar /var/jenkins_home/war/WEB-INF/jenkins-cli.jar -s "http://localhost:8080/" groovy = < jenkins/jobs.groovy
}

echo "Jobs created / updated successfully!"
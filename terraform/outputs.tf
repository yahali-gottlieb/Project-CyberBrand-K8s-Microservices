output "rds_endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "k8s_aws_access_key_id" {
  value = aws_iam_access_key.k8s_app_user_key.id
}

output "k8s_aws_secret_access_key" {
  value     = aws_iam_access_key.k8s_app_user_key.secret
  sensitive = true
}

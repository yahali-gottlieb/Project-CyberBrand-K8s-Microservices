# 1. IAM User for Kubernetes Pods
resource "aws_iam_user" "k8s_app_user" {
  name = "devops-k8s-app-user"
}

# 2. Create Access Key for the User
resource "aws_iam_access_key" "k8s_app_user_key" {
  user = aws_iam_user.k8s_app_user.name
}

# 3. IAM Policy (Strict Permissions for S3 PutObject and SNS Publish)
resource "aws_iam_policy" "s3_sns_policy" {
  name        = "devops-s3-sns-policy"
  description = "Allow k8s pods to upload to S3 and publish to SNS"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::devops-project-bucket-yahali-v2",
          "arn:aws:s3:::devops-project-bucket-yahali-v2/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish",
          "sns:ListTopics"
        ]
        Resource = "*"
      }
    ]
  })
}

# 4. Attach Policy to User
resource "aws_iam_user_policy_attachment" "attach_policy" {
  user       = aws_iam_user.k8s_app_user.name
  policy_arn = aws_iam_policy.s3_sns_policy.arn
}

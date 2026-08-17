variable "aws_region" {
  description = "The AWS region to deploy our infrastructure"
  type        = string
  default     = "us-east-1" 
}

variable "my_ip" {
  description = "Your local public IP address for RDS access (e.g., 81.2.3.4/32)"
  type        = string
}

variable "db_password" {
  description = "The password for the RDS database"
  type        = string
  sensitive   = true
}
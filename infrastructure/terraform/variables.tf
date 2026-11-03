variable "aws_region" {
  description = "AWS region for data platform deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Name identifier for all platform cloud resources"
  type        = string
  default     = "enterprise-data-platform"
}

variable "data_retention_days" {
  description = "Number of days before transitioning bronze raw objects to Glacier"
  type        = number
  default     = 90
}


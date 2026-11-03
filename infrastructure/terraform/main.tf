terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.30"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# ----------------------------------------------------------------------------
# 1. S3 MEDALLION OBJECT STORAGE LAKE
# ----------------------------------------------------------------------------
resource "aws_s3_bucket" "data_lake" {
  bucket        = "${var.project_name}-lake-${var.environment}"
  force_destroy = false
}

resource "aws_s3_bucket_versioning" "lake_versioning" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lake_encryption" {
  bucket = aws_s3_bucket.data_lake.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "block_public" {
  bucket                  = aws_s3_bucket.data_lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle rules: Transition Bronze raw objects to Glacier after retention period
resource "aws_s3_bucket_lifecycle_configuration" "lake_lifecycle" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "bronze-glacier-archive"
    status = "Enabled"

    filter {
      prefix = "bronze/"
    }

    transition {
      days          = var.data_retention_days
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }
}

# ----------------------------------------------------------------------------
# 2. AWS GLUE DATA CATALOG & ATHENA WORKGROUP
# ----------------------------------------------------------------------------
resource "aws_glue_catalog_database" "analytics_catalog" {
  name        = "${var.project_name}_catalog_${var.environment}"
  description = "Centralized Glue Data Catalog for Medallion Silver and Gold Parquet tables"
}

resource "aws_athena_workgroup" "analytics_workgroup" {
  name = "${var.project_name}-workgroup-${var.environment}"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.data_lake.bucket}/athena-results/"
      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }
}

# ----------------------------------------------------------------------------
# 3. IAM ROLES & LEAST-PRIVILEGE POLICIES
# ----------------------------------------------------------------------------
resource "aws_iam_role" "pipeline_execution_role" {
  name = "${var.project_name}-pipeline-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = ["ecs-tasks.amazonaws.com", "glue.amazonaws.com"]
        }
      }
    ]
  })
}

resource "aws_iam_policy" "lake_read_write_policy" {
  name        = "${var.project_name}-lake-policy-${var.environment}"
  description = "Scoped read/write access to S3 data lake and Athena query execution"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetTable",
          "glue:GetPartitions",
          "glue:CreateTable",
          "glue:UpdateTable"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_lake_policy" {
  role       = aws_iam_role.pipeline_execution_role.name
  policy_arn = aws_iam_policy.lake_read_write_policy.arn
}


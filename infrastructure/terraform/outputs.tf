output "s3_data_lake_bucket_name" {
  description = "Name of the provisioned S3 Data Lake bucket"
  value       = aws_s3_bucket.data_lake.bucket
}

output "s3_data_lake_arn" {
  description = "ARN of the S3 Data Lake bucket"
  value       = aws_s3_bucket.data_lake.arn
}

output "glue_catalog_database_name" {
  description = "Name of the Glue Data Catalog database"
  value       = aws_glue_catalog_database.analytics_catalog.name
}

output "athena_workgroup_name" {
  description = "Name of the Athena workgroup for analytical SQL queries"
  value       = aws_athena_workgroup.analytics_workgroup.name
}

output "pipeline_iam_role_arn" {
  description = "ARN of the IAM role used by ETL pipelines"
  value       = aws_iam_role.pipeline_execution_role.arn
}


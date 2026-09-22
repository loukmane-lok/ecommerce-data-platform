output "raw_bucket_name" {
  description = "Name of the raw data S3 bucket"
  value       = aws_s3_bucket.raw.bucket
}

output "curated_bucket_name" {
  description = "Name of the curated data S3 bucket"
  value       = aws_s3_bucket.curated.bucket
}

output "scripts_bucket_name" {
  description = "Name of the Glue scripts S3 bucket"
  value       = aws_s3_bucket.scripts.bucket
}

output "logs_bucket_name" {
  description = "Name of the logs S3 bucket"
  value       = aws_s3_bucket.logs.bucket
}

output "glue_execution_role_arn" {
  description = "ARN of the Glue execution IAM role"
  value       = aws_iam_role.glue_execution_role.arn
}


output "lambda_function_url" {
  description = "HTTPS endpoint for posting events (requires SigV4 / lambda:InvokeFunctionUrl)"
  value       = aws_lambda_function_url.event_ingestion_url.function_url
}

output "lambda_function_name" {
  description = "Lambda function name for CLI commands"
  value       = aws_lambda_function.event_ingestion.function_name
}


resource "aws_glue_catalog_database" "ecommerce_db" {
  name        = "ecommerce_db"
  description = "Data catalog database for ecommerce analytics pipeline"
}


resource "aws_s3_object" "etl_script" {
  bucket = aws_s3_bucket.scripts.bucket
  key    = "glue_jobs/raw_to_curated_orders.py"
  source = "${path.module}/../../processing/glue_jobs/raw_to_curated_orders.py"
  etag   = filemd5("${path.module}/../../processing/glue_jobs/raw_to_curated_orders.py")
}

resource "aws_s3_object" "dq_script" {
  bucket = aws_s3_bucket.scripts.bucket
  key    = "glue_jobs/data_quality_checks.py"
  source = "${path.module}/../../processing/glue_jobs/data_quality_checks.py"
  etag   = filemd5("${path.module}/../../processing/glue_jobs/data_quality_checks.py")
}

resource "aws_glue_crawler" "raw_orders_crawler" {
  name          = "raw-orders-crawler"
  role          = aws_iam_role.glue_execution_role.arn
  database_name = aws_glue_catalog_database.ecommerce_db.name

  s3_target {
    path = "s3://${aws_s3_bucket.raw.bucket}/orders/"
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
    }
  })
}

resource "aws_glue_job" "raw_to_curated_orders" {
  name              = "raw-to-curated-orders"
  role_arn          = aws_iam_role.glue_execution_role.arn
  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 10

  command {
    script_location = "s3://${aws_s3_bucket.scripts.bucket}/glue_jobs/raw_to_curated_orders.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-bookmark-option"              = "job-bookmark-disable"
    "--RAW_PATH"                         = "s3://${aws_s3_bucket.raw.bucket}/orders/"
    "--CURATED_PATH"                     = "s3://${aws_s3_bucket.curated.bucket}/orders/"
    "--TempDir"                          = "s3://${aws_s3_bucket.scripts.bucket}/tmp/"
    "--enable-continuous-cloudwatch-log" = "true"
    "--extra-py-files"                   = "s3://${aws_s3_bucket.scripts.bucket}/glue_jobs/orders_transformer.py"
  }

  depends_on = [aws_s3_object.etl_script]
}

resource "aws_glue_job" "data_quality_checks" {
  name              = "data-quality-checks"
  role_arn          = aws_iam_role.glue_execution_role.arn
  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 10

  command {
    script_location = "s3://${aws_s3_bucket.scripts.bucket}/glue_jobs/data_quality_checks.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-bookmark-option"              = "job-bookmark-disable"
    "--CURATED_PATH"                     = "s3://${aws_s3_bucket.curated.bucket}/orders/"
    "--TempDir"                          = "s3://${aws_s3_bucket.scripts.bucket}/tmp/"
    "--enable-continuous-cloudwatch-log" = "true"
    "--extra-py-files"                   = "s3://${aws_s3_bucket.scripts.bucket}/glue_jobs/orders_transformer.py"
  }

  depends_on = [aws_s3_object.dq_script]
}

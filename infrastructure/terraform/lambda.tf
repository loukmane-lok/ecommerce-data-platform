data "archive_file" "lambda_package" {
  type        = "zip"
  source_file = "${path.module}/../../ingestion/lambda/handler.py"
  output_path = "${path.module}/../../ingestion/lambda/lambda_function.zip"
}
resource "aws_iam_role" "lambda_execution_role" {
  name = "ecommerce-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}


resource "aws_iam_role_policy" "lambda_s3_policy" {
  name = "ecommerce-lambda-s3-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.raw.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_lambda_function" "event_ingestion" {
  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  function_name    = "ecommerce-event-ingestion"
  role             = aws_iam_role.lambda_execution_role.arn
  runtime          = "python3.10"
  handler          = "handler.lambda_handler"
  timeout          = 30
  memory_size      = 128

  environment {
    variables = {
      RAW_BUCKET_NAME = aws_s3_bucket.raw.id
    }
  }
}

resource "aws_lambda_function_url" "event_ingestion_url" {
  function_name      = aws_lambda_function.event_ingestion.function_name
  authorization_type = "NONE"

  cors {
    allow_origins = ["*"]
    allow_methods = ["POST"]
  }
}

resource "aws_cloudwatch_event_rule" "every_5_minutes" {
  name                = "ecommerce-every-5-minutes"
  description         = "Triggers event ingestion Lambda every 5 minutes"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.every_5_minutes.name
  target_id = "ecommerce-lambda-target"
  arn       = aws_lambda_function.event_ingestion.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.event_ingestion.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_5_minutes.arn
}
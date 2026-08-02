# --- Local development ---
generate:
	python ingestion/local_generator/generate_events.py --count 100 --type both

ingest:
	# Manual/ad-hoc: POST to Lambda Function URL. Requires LAMBDA_URL in .env
	@curl -X POST $$(LAMBDA_URL) -H "Content-Type: application/json" --data-binary @payload.json

test:
	python3 -m pytest processing/transformations/test_transformations.py ingestion/lambda/test_handler_local.py -v

lint:
	python3 -m flake8 processing/ ingestion/ --max-line-length=100

# --- Airflow ---
airflow-up:
	cd orchestration && docker compose up -d

airflow-down:
	cd orchestration && docker compose down

airflow-logs:
	cd orchestration && docker compose logs -f airflow-scheduler

# --- AWS deploy ---
deploy-scripts:
	aws s3 sync processing/glue_jobs/ s3://$$(SCRIPTS_BUCKET)/glue_jobs/

run-crawler:
	aws glue start-crawler --name $$(GLUE_CRAWLER_NAME) --region us-east-1

run-etl:
	aws glue start-job-run --job-name $$(GLUE_ETL_JOB) --region us-east-1

# --- Infrastructure ---
tf-plan:
	cd infrastructure/terraform && terraform plan

tf-apply:
	cd infrastructure/terraform && terraform apply

tf-destroy:
	cd infrastructure/terraform && terraform destroy

# --- Cleanup ---
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + && find . -name "*.pyc" -delete

.PHONY: generate ingest test lint airflow-up airflow-down airflow-logs deploy-scripts run-crawler run-etl tf-plan tf-apply tf-destroy clean
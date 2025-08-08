output "archive_bucket_name" {
  value = aws_s3_bucket.archive.bucket
}

output "opensearch_endpoint" {
  value = aws_opensearch_domain.docs.endpoint
}

output "db_instance_id" {
  value = aws_db_instance.postgres.id
}

output "secrets_arn" {
  value = aws_secretsmanager_secret.app.arn
}



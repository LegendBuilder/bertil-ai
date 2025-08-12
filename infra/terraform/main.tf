resource "aws_s3_bucket" "archive" {
  bucket              = var.archive_bucket_name
  object_lock_enabled = true

  tags = {
    Name         = "archive-${var.environment}"
    Environment  = var.environment
    RegionPolicy = "SE/EU"
    WORM         = "enabled"
  }
}

resource "aws_s3_bucket_versioning" "archive" {
  bucket = aws_s3_bucket.archive.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_kms_key" "s3_archive" {
  description             = "KMS key for S3 archive object encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "archive" {
  bucket = aws_s3_bucket.archive.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
      kms_master_key_id = aws_kms_key.s3_archive.arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "archive" {
  bucket                  = aws_s3_bucket.archive.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_object_lock_configuration" "archive" {
  bucket = aws_s3_bucket.archive.bucket

  rule {
    default_retention {
      mode = "COMPLIANCE"
      days = var.object_lock_retention_years * 365
    }
  }
}

data "aws_iam_policy_document" "archive_bucket_policy" {
  statement {
    sid    = "DenyDelete"
    effect = "Deny"
    principals { type = "*" identifiers = ["*"] }
    actions = [
      "s3:DeleteObject",
      "s3:DeleteObjectVersion",
      "s3:DeleteObjectTagging",
      "s3:DeleteObjectVersionTagging",
    ]
    resources = [
      "${aws_s3_bucket.archive.arn}/*"
    ]
  }

  statement {
    sid    = "RequireObjectLockOnPut"
    effect = "Deny"
    principals { type = "*" identifiers = ["*"] }
    actions = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.archive.arn}/*"]
    condition {
      test     = "StringNotEqualsIfExists"
      variable = "s3:object-lock-mode"
      values   = ["COMPLIANCE"]
    }
  }
}

resource "aws_s3_bucket_policy" "archive" {
  bucket = aws_s3_bucket.archive.id
  policy = data.aws_iam_policy_document.archive_bucket_policy.json
}

resource "aws_s3_bucket_lifecycle_configuration" "archive" {
  bucket = aws_s3_bucket.archive.id

  rule {
    id     = "deny-noncurrent-deletes"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 0
    }
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_db_instance" "postgres" {
  identifier          = "bertil-db-${var.environment}"
  engine              = "postgres"
  engine_version      = "15.5"
  instance_class      = var.db_instance_class
  allocated_storage   = 20
  username            = var.db_username
  password            = var.db_password
  skip_final_snapshot = true
  publicly_accessible = false
  deletion_protection = false
  multi_az            = true
  storage_encrypted   = true
  kms_key_id          = aws_kms_key.s3_archive.arn

  tags = {
    Name        = "bertil-db-${var.environment}"
    Environment = var.environment
  }
}

# Application Load Balancer and WAF skeleton (details omitted for brevity)
resource "aws_lb" "app" {
  name               = "bertil-alb-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = []
  subnets            = []
}

resource "aws_wafv2_web_acl" "app" {
  name        = "bertil-waf-${var.environment}"
  description = "Basic WAF for rate limiting and common protections"
  scope       = "REGIONAL"
  default_action { allow {} }
  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "bertil-waf"
    sampled_requests_enabled   = true
  }
  rule {
    name     = "aws-managed-common"
    priority = 1
    override_action { none {} }
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "common"
      sampled_requests_enabled   = true
    }
  }
}

# Redis (Elasticache) placeholder for distributed rate limiting / cache
# In production use aws_elasticache_cluster/replication_group


resource "aws_opensearch_domain" "docs" {
  domain_name    = var.opensearch_domain_name
  engine_version = "OpenSearch_2.11"

  cluster_config {
    instance_type  = "t3.small.search"
    instance_count = 1
  }

  ebs_options {
    ebs_enabled = true
    volume_type = "gp3"
    volume_size = 10
  }

  encrypt_at_rest {
    enabled = true
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https = true
  }

  tags = {
    Name        = "bertil-docs-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret" "app" {
  name = "bertil/${var.environment}/app"
}

resource "random_password" "app_secret" {
  length  = 32
  special = true
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id     = aws_secretsmanager_secret.app.id
  secret_string = jsonencode({
    JWT_SECRET = random_password.app_secret.result
  })
}



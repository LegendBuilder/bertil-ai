variable "aws_region" {
  type    = string
  default = "eu-north-1"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "archive_bucket_name" {
  type        = string
  description = "S3 bucket for WORM archive"
  default     = "bertil-archive-dev"
}

variable "object_lock_retention_years" {
  type    = number
  default = 7
}

variable "opensearch_domain_name" {
  type    = string
  default = "bertil-docs-dev"
}

variable "db_username" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}



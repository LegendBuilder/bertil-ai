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

variable "vpc_id" {
  type        = string
  description = "VPC ID for ALB"
  default     = ""
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "Public subnet IDs for ALB"
  default     = []
}

variable "grafana_dashboards_bucket" {
  type        = string
  description = "S3 bucket to store Grafana dashboard JSONs (optional)"
  default     = ""
}

variable "grafana_dashboards_prefix" {
  type        = string
  description = "Prefix/path within bucket for dashboards"
  default     = "grafana/dashboards/"
}

# ECS / ECR deployment variables
variable "ecs_subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs for ECS tasks"
  default     = []
}

variable "ecs_security_group_id" {
  type        = string
  description = "Security group for ECS tasks"
  default     = ""
}

variable "ecs_task_cpu" {
  type        = number
  description = "Task CPU units (e.g., 256, 512, 1024)"
  default     = 512
}

variable "ecs_task_memory" {
  type        = number
  description = "Task memory in MiB (e.g., 1024, 2048)"
  default     = 1024
}

variable "ecs_desired_count" {
  type        = number
  description = "Desired count for API services"
  default     = 1
}

variable "api_image" {
  type        = string
  description = "ECR image URI for API container"
  default     = ""
}

variable "worker_image" {
  type        = string
  description = "ECR image URI for worker container"
  default     = ""
}



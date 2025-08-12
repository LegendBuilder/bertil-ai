# Terraform – Infrastruktur (produktionsredo)

Mål: SE/EU‑lokalisering, S3 Object Lock (WORM) med retention ≥ 7 år, RDS Postgres (Multi‑AZ), OpenSearch, Secrets Manager, ALB + WAF.

Kommandon (validering lokalt)

```powershell
cd infra/terraform
terraform init -backend=false
terraform fmt -check
terraform validate
```

Resurser

- `aws_s3_bucket.archive` med `object_lock_enabled = true` och default-retention (COMPLIANCE, ≥7 år)
- `aws_db_instance.postgres` (Multi‑AZ; klass och cred via var)
- `aws_opensearch_domain.docs` (min. config, TLS enforced)
- `aws_secretsmanager_secret.app` + initial hemlighet
- `aws_lb.app` (ALB‑skelett) + `aws_wafv2_web_acl.app` (AWS managed rules)

Variabler

- `aws_region` (default `eu-north-1`)
- `environment` (dev/stage/prod)
- `archive_bucket_name`, `object_lock_retention_years`
- `db_username`, `db_password`, `db_instance_class`
- `vpc_id`, `public_subnet_ids` för ALB

Observera

- Objektlås måste aktiveras vid skapandet av bucket (går ej att ändra i efterhand).
- För produktion: lägg till KMS‑nycklar, SG/VPC/subnät, target group och koppla WAF till ALB.



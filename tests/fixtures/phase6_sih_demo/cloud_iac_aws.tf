# Terraform AWS KMS + ACM reference (demo)
resource "aws_kms_key" "app_key" {
  description             = "Application encryption key"
  deletion_window_in_days = 10
  enable_key_rotation     = true
}

resource "aws_acm_certificate" "api_cert" {
  domain_name       = "api.example.com"
  validation_method = "DNS"
}

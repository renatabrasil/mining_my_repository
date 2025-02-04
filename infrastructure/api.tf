locals {
  domain_name = "terraform-aws-modules.modules.tf" # trimsuffix(data.aws_route53_zone.this.name, ".")
  subdomain   = "complete-http"
}

module "api_gateway" {
  source = "terraform-aws-modules/apigateway-v2/aws"

  name          = "dev-http"
  description   = "My awesome HTTP API Gateway"
  protocol_type = "HTTP"

  cors_configuration = {
    allow_headers = [
      "content-type", "x-amz-date", "authorization", "x-api-key", "x-amz-security-token", "x-amz-user-agent"
    ]
    allow_methods = ["*"]
    allow_origins = ["*"]
  }

  # Custom domain
  domain_name                 = local.domain_name
  domain_name_certificate_arn = module.acm.acm_certificate_arn

  # Access logs
  default_stage_access_log_destination_arn = "arn:aws:logs:sa-east-1:251675404411:log-group:debug-apigateway"
  default_stage_access_log_format          = "$context.identity.sourceIp - - [$context.requestTime] \"$context.httpMethod $context.routeKey $context.protocol\" $context.status $context.responseLength $context.requestId $context.integrationErrorMessage"

  # Routes and integrations
  integrations = {
    "POST /" = {
      lambda_arn             = "arn:aws:lambda:sa-east-1:251675404411:function:processor"
      payload_format_version = "2.0"
      timeout_milliseconds   = 12000
    }

    "$default" = {
      lambda_arn = "arn:aws:lambda:sa-east-1:251675404411:function:processor"
    }
  }

  tags = {
    Name = "http-apigateway"
  }
}

######
# ACM
######

data "aws_route53_zone" "this" {
  name = local.domain_name
}

module "acm" {
  source  = "terraform-aws-modules/acm/aws"
  version = "~> 3.0"

  domain_name               = local.domain_name
#  zone_id                   = data.aws_route53_zone.this.id
  subject_alternative_names = ["${local.subdomain}.${local.domain_name}"]
}
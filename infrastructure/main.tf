terraform {
  backend "remote" {
    organization = "renata-corporation"
    workspaces {
      name = "mining_my_repository"
    }
  }
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }

  required_version = ">= 0.14.9"
}

provider "aws" {
  profile                 = "default"
  region                  = "sa-east-1"
  shared_credentials_file = "~/.aws/credentials"
}
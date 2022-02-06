terraform {
  backend "remote" {
    organization = "renata-corporation"
    workspaces {
      name = "Example-Workspace"
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
  region                  = "us-west-2"
  shared_credentials_file = "~/.aws/credentials"
}
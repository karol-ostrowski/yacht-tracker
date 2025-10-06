# Configure the Azure provider
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.47.0"
    }
  }

  required_version = ">= 1.13.3"
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_storage_account" "monitoring" {
    name = var.monitoring_storage_account_name
    resource_group_name = var.resource_group_name
    location = var.location
    account_tier = var.monitoring_storage_account_tier
    account_replication_type = var.monitoring_storage_account_replication_type
}

resource "azurerm_storage_container" "loki" {
    name = var.loki_storage_container_name
    storage_account_id = azurerm_storage_account.monitoring.id
}

resource "azurerm_storage_blob" "logs" {
    name = var.loki_storage_blob_name
    storage_account_name = var.monitoring_storage_account_name
    storage_container_name = var.loki_storage_container_name
    type = var.loki_storage_blob_type
}

resource "azurerm_storage_container" "mimir" {
    name = var.mimir_storage_container_name
    storage_account_id = azurerm_storage_account.monitoring.id
}

resource "azurerm_storage_blob" "metrics" {
    name = var.mimir_storage_blob_name
    storage_account_name = var.monitoring_storage_account_name
    storage_container_name = var.mimir_storage_container_name
    type = var.mimir_storage_blob_type
}

resource "azurerm_storage_account" "rawdata" {
    name = var.raw_data_storage_account_name
    resource_group_name = var.resource_group_name
    location = var.location
    account_tier = var.raw_data_storage_account_tier
    account_replication_type = var.raw_data_storage_account_replication_type
}

resource "azurerm_storage_container" "rawdata" {
    name = var.raw_data_storage_container_name
    storage_account_id = azurerm_storage_account.rawdata.id
}

resource "azurerm_storage_blob" "rawdata" {
    name = var.raw_data_storage_blob_name
    storage_account_name = var.raw_data_storage_account_name
    storage_container_name = var.raw_data_storage_container_name
    type = var.raw_data_storage_blob_type
}
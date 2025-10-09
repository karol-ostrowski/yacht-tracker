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
  name                     = var.monitoring_storage_account_name
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = var.location
  account_tier             = var.monitoring_storage_account_tier
  account_replication_type = var.monitoring_storage_account_replication_type
}

resource "azurerm_storage_container" "loki" {
  name               = var.loki_storage_container_name
  storage_account_id = azurerm_storage_account.monitoring.id
}

resource "azurerm_storage_container" "mimir" {
  name               = var.mimir_storage_container_name
  storage_account_id = azurerm_storage_account.monitoring.id
}

resource "azurerm_storage_account" "rawdata" {
  name                     = var.raw_data_storage_account_name
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = var.location
  account_tier             = var.raw_data_storage_account_tier
  account_replication_type = var.raw_data_storage_account_replication_type
}

resource "azurerm_storage_container" "rawdata" {
  name               = var.raw_data_storage_container_name
  storage_account_id = azurerm_storage_account.rawdata.id
}
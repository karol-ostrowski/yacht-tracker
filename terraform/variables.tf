variable "resource_group_name" {
  description = "Name of the resource group."
  type        = string
  default     = "yacht-tracker-rg"
}

variable "location" {
  description = "Azure region for the resources."
  type        = string
  default     = "polandcentral"
}

variable "monitoring_storage_account_name" {
  description = "Name of the monitoring storage account."
  type        = string
  default     = "minotoringstorageaccount"
}

variable "monitoring_storage_account_tier" {
  description = "Account tier for the monitoring storage account."
  type        = string
  default     = "Standard"
}

variable "monitoring_storage_account_replication_type" {
  description = "Replication type for the monitoring storage account."
  type        = string
  default     = "LRS"
}

variable "loki_storage_container_name" {
  description = "Name of the storage container for Loki."
  type        = string
  default     = "loki-storage-container"
}

variable "mimir_storage_container_name" {
  description = "Name of the storage container for Mimir."
  type        = string
  default     = "mimir-storage-container"
}

variable "mimir_storage_blob_name" {
  description = "Name of the storage blob instance for Mimir."
  type        = string
  default     = "mimir-blob-instance"
}

variable "raw_data_storage_account_name" {
  description = "Name of the raw data storage account."
  type        = string
  default     = "rawdatastorageaccount"
}

variable "raw_data_storage_account_tier" {
  description = "Account tier for the raw data storage account."
  type        = string
  default     = "Standard"
}

variable "raw_data_storage_account_replication_type" {
  description = "Replication type for the raw data storage account."
  type        = string
  default     = "LRS"
}

variable "raw_data_storage_container_name" {
  description = "Name of the storage container for the raw data."
  type        = string
  default     = "raw-data-storage-container"
}
output "raw_data_connection_string" {
  value     = azurerm_storage_account.rawdata.primary_connection_string
  sensitive = true
}

output "raw_data_container_name" {
  value = azurerm_storage_container.rawdata.name
}

output "loki_container_name" {
  value = azurerm_storage_container.loki.name

}

output "monitoring_storage_account_name" {
  value = azurerm_storage_account.monitoring.name
}

output "monitoring_storage_account_key" {
  value     = azurerm_storage_account.monitoring.primary_access_key
  sensitive = true
}

output "mimir_container_name" {
  value = azurerm_storage_container.mimir.name
}
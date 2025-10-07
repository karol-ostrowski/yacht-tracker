output "connection_string" {
  value     = azurerm_storage_account.rawdata.primary_connection_string
  sensitive = true
}

output "container_name" {
  value = azurerm_storage_container.rawdata.name
}
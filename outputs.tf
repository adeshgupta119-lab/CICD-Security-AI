output "resource_group_id" {
  description = "The ID of the Resource Group"
  value       = azurerm_resource_group.example.id
}

output "resource_group_name" {
  description = "The Name of the Resource Group"
  value       = azurerm_resource_group.example.name
}

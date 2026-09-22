# Terraform Azure Key Vault reference (demo)
resource "azurerm_key_vault" "main" {
  name                = "kv-cryptosentinel"
  resource_group_name = "rg-main"
  location            = "eastus"
  sku_name            = "premium"
  tenant_id           = var.tenant_id
}

resource "azurerm_key_vault_key" "signing_key" {
  name         = "signing-key"
  key_vault_id = azurerm_key_vault.main.id
  key_type     = "RSA"
  key_size     = 4096
  key_opts     = ["sign", "verify"]
}

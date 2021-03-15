variable "name" { default = "example-params" }
variable "subscription_name" { default = "example" }
variable "management_group" { default = "" }
variable "enforcement_mode" { default = false }

variable "category" {
  type    = string
  default = "Testing"
}
provider "azurerm" {
  features {}
}

locals {
  policy_names = [
    # -----------------------------------------------------------------------------------------------------------------
    # API Management
    # -----------------------------------------------------------------------------------------------------------------
    "API Management services should use a virtual network",
  ]
  policy_definition_map = zipmap(
    data.azurerm_policy_definition.example_params_definition_lookups.*.display_name,
    data.azurerm_policy_definition.example_params_definition_lookups.*.id
  )
}

# ---------------------------------------------------------------------------------------------------------------------
# Conditional data lookups: If the user supplies management group, look up the ID of the management group
# ---------------------------------------------------------------------------------------------------------------------
data "azurerm_management_group" "example_params" {
  count = var.management_group != "" ? 1 : 0
  name  = var.management_group
}

### If the user supplies subscription, look up the ID of the subscription
data "azurerm_subscriptions" "example_params" {
  count                 = var.subscription_name != "" ? 1 : 0
  display_name_contains = var.subscription_name
}

locals {
  scope = var.management_group != "" ? data.azurerm_management_group.example_params[0].id : element(data.azurerm_subscriptions.example_params[0].subscriptions.*.id, 0)
}

# ---------------------------------------------------------------------------------------------------------------------
# Azure Policy Definition Lookups
# ---------------------------------------------------------------------------------------------------------------------

data "azurerm_policy_definition" "example_params_definition_lookups" {
  count        = length(local.policy_names)
  display_name = local.policy_names[count.index]
}

# ---------------------------------------------------------------------------------------------------------------------
# Azure Policy Initiative Definition
# ---------------------------------------------------------------------------------------------------------------------

resource "azurerm_policy_set_definition" "example_params_guardrails" {
  name                  = var.name
  policy_type           = "Custom"
  display_name          = var.name
  description           = var.name
  management_group_name = var.management_group == "" ? null : var.management_group
  metadata = tostring(jsonencode({
    category = var.category
  }))


  policy_definition_reference {
    policy_definition_id = lookup(local.policy_definition_map, "API Management services should use a virtual network")
    parameter_values = jsonencode({
      evaluatedSkuNames = { "value" : "[parameters('evaluatedSkuNames')]" }
    })
    reference_id = null
  }

  parameters = <<PARAMETERS
{
    "evaluatedSkuNames": {
        "name": "evaluatedSkuNames",
        "type": "Array",
        "description": "List of Azure Spring Cloud SKUs against which this policy will be evaluated.",
        "display_name": "Azure Spring Cloud SKU Names",
        "default_value": [
            "Standard"
        ],
        "allowed_values": [
            "Standard"
        ]
    }
}
PARAMETERS
}

# ---------------------------------------------------------------------------------------------------------------------
# Azure Policy Assignments
# Apply the Policy Initiative to the specified scope
# ---------------------------------------------------------------------------------------------------------------------
resource "azurerm_policy_assignment" "example_params_guardrails" {
  name                 = var.name
  policy_definition_id = azurerm_policy_set_definition.example_params_guardrails.id
  scope                = local.scope
  enforcement_mode     = var.enforcement_mode
  parameters = jsonencode(
    {
        evaluatedSkuNames = { "value" : ["Standard"] }
    },
  )
}


# ---------------------------------------------------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------------------------------------------------
output "policy_assignment_ids" {
  value       = azurerm_policy_assignment.example_params_guardrails.*.id
  description = "The IDs of the Policy Assignments."
}

output "scope" {
  value       = local.scope
  description = "The target scope - either the management group or subscription, depending on which parameters were supplied"
}

output "policy_set_definition_id" {
  value       = azurerm_policy_set_definition.example_params_guardrails.id
  description = "The ID of the Policy Set Definition."
}


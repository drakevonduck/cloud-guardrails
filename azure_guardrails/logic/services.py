import os
import logging
from typing import List
from azure_guardrails.shared import utils
from azure_guardrails.shared.exclusions import DEFAULT_EXCLUSIONS, Exclusions
from azure_guardrails.logic.policy_definition import PolicyDefinition

logger = logging.getLogger(__name__)


class Service:
    def __init__(self, service_name: str, exclusions: Exclusions = DEFAULT_EXCLUSIONS):
        self.service_name = service_name
        self.exclusions = exclusions
        self.service_policy_directory = os.path.join(utils.AZURE_POLICY_SERVICE_DIRECTORY, self.service_name)
        self.policy_files = self._policy_files()
        self.policy_definitions = self._policy_definitions()
        self.display_names = self.get_display_names()

    def _policy_files(self) -> list:
        policy_files = [f for f in os.listdir(self.service_policy_directory) if os.path.isfile(os.path.join(self.service_policy_directory, f))]
        return policy_files

    def _policy_definitions(self) -> List[PolicyDefinition]:
        policy_definitions = []
        for file in self.policy_files:
            policy_content = utils.get_policy_json(service_name=self.service_name, filename=file)
            policy_definition = PolicyDefinition(policy_content)
            policy_definitions.append(policy_definition)
        return policy_definitions

    def get_display_names(self, with_parameters: bool = False, with_modify_capabilities: bool = False, all_policies: bool = False) -> list:
        display_names = []
        for policy_definition in self.policy_definitions:
            # Quality control
            # First, if the display name starts with [Deprecated], skip it
            if policy_definition.display_name.startswith("[Deprecated]: "):
                logger.debug("Deprecated Policy; skipping. Policy name: %s" % policy_definition.display_name)
                continue
            # Some Policies with Modify capabilities don't have an Effect - only way to detect them is to see if the name starts with 'Deploy'
            if not with_modify_capabilities and policy_definition.display_name.startswith("Deploy "):
                logger.debug("'Deploy' Policy detected; skipping. Policy name: %s" % policy_definition.display_name)
                continue
            # If the policy is deprecated, skip it
            if policy_definition.is_deprecated:
                logger.debug("Policy definition is deprecated; skipping. Policy name: %s" % policy_definition.display_name)
                continue

            # If we have specified it in the Exclusions config, skip it
            if self.exclusions.is_excluded(service_name=self.service_name, display_name=policy_definition.display_name):
                logger.debug("Policy definition is excluded; skipping. Policy name: %s" % policy_definition.display_name)
                continue

            # Now, add display names depending on the filtering arguments supplied
            # Case: Return all policies
            if all_policies:
                display_names.append(policy_definition.display_name)
            # Case: Return only policies that do not have parameters or modify capabilities
            if not with_parameters and not with_modify_capabilities:
                if (
                    not policy_definition.includes_parameters
                    and not policy_definition.modifies_resources
                ):
                    display_names.append(policy_definition.display_name)
            # Case: return policies with parameters only, as long as they do not include modify capabilities
            elif with_parameters and not with_modify_capabilities:
                if (
                    policy_definition.includes_parameters
                    and not policy_definition.modifies_resources
                ):
                    display_names.append(policy_definition.display_name)
            # Case: return policies with parameters and modify capabilities
            elif with_parameters and with_modify_capabilities:
                if (
                    policy_definition.modifies_resources
                    and policy_definition.includes_parameters
                ):
                    display_names.append(policy_definition.display_name)
        display_names.sort()
        return display_names

    def get_display_names_sorted_by_service(self, with_parameters: bool = False, with_modify_capabilities: bool = False, all_policies: bool = False) -> dict:
        display_names = {}
        service_display_names = self.get_display_names(with_parameters=with_parameters,
                                                       with_modify_capabilities=with_modify_capabilities,
                                                       all_policies=all_policies)
        service_display_names = list(dict.fromkeys(service_display_names))  # remove duplicates
        if service_display_names:
            display_names[self.service_name] = service_display_names
        return display_names


class Services:
    def __init__(self, exclusions: Exclusions = DEFAULT_EXCLUSIONS):
        service_names = utils.get_service_names()
        service_names.sort()
        self.service_names = service_names
        self.exclusions = exclusions
        self.services = self._services()

    def _services(self) -> List[Service]:
        services = []
        service_names = self.service_names
        for service_name in service_names:
            service = Service(service_name=service_name, exclusions=self.exclusions)
            services.append(service)
        return services

    def get_display_names(self, with_parameters: bool = False, with_modify_capabilities: bool = False, all_policies: bool = False) -> list:
        display_names = []
        for service in self.services:
            service_display_names = service.get_display_names(with_parameters=with_parameters,
                                                              with_modify_capabilities=with_modify_capabilities,
                                                              all_policies=all_policies)
            display_names.extend(service_display_names)
        display_names = list(dict.fromkeys(display_names))  # remove duplicates
        display_names.sort()
        return display_names

    def get_display_names_sorted_by_service(self, with_parameters: bool = False, with_modify_capabilities: bool = False, all_policies: bool = False) -> dict:
        display_names = {}
        for service in self.services:
            logger.debug("Getting display names for service: %s" % service)
            service_display_names = service.get_display_names(with_parameters=with_parameters,
                                                              with_modify_capabilities=with_modify_capabilities,
                                                              all_policies=all_policies)
            service_display_names = list(dict.fromkeys(service_display_names))  # remove duplicates
            if service_display_names:
                display_names[service.service_name] = service_display_names
        return display_names

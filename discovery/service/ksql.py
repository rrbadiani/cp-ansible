import sys

from discovery.service.service import AbstractPropertyBuilder
from discovery.utils.constants import ConfluentServices, DEFAULT_KEY
from discovery.utils.inventory import CPInventoryManager
from discovery.utils.utils import InputContext, Logger, FileUtils

logger = Logger.get_logger()


class KsqlServicePropertyBuilder:

    @staticmethod
    def build_properties(input_context: InputContext, inventory: CPInventoryManager):
        from discovery.service import get_service_builder_class
        obj = get_service_builder_class(modules=sys.modules[__name__],
                                        default_class_name="KsqlServicePropertyBaseBuilder",
                                        version=input_context.from_version)
        obj(input_context, inventory).build_properties()


class KsqlServicePropertyBaseBuilder(AbstractPropertyBuilder):
    inventory = None
    input_context = None

    def __init__(self, input_context: InputContext, inventory: CPInventoryManager):
        self.inventory = inventory
        self.input_context = input_context
        self.mapped_service_properties = set()

    def build_properties(self):

        # Get the hosts for given service
        service = ConfluentServices.KSQL
        hosts = self.get_service_host(service, self.inventory)
        if not hosts:
            logger.error(f"Could not find any host with service {service.value.get('name')} ")
            return

        host_service_properties = self.get_property_mappings(self.input_context, service, hosts)
        service_properties = host_service_properties.get(hosts[0]).get(DEFAULT_KEY)

        # Build service user group properties
        self.__build_daemon_properties(self.input_context, service, hosts)

        # Build service properties
        self.__build_service_properties(service_properties)

        # Add custom properties
        self.__build_custom_properties(service_properties, self.mapped_service_properties)

        # Build Command line properties
        self.__build_runtime_properties(service_properties)

    def __build_daemon_properties(self, input_context: InputContext, service: ConfluentServices, hosts: list):

        # User group information
        response = self.get_service_user_group(input_context, service, hosts)
        self.update_inventory(self.inventory, response)

    def __build_service_properties(self, service_properties):
        for key, value in vars(KsqlServicePropertyBaseBuilder).items():
            if callable(getattr(KsqlServicePropertyBaseBuilder, key)) and key.startswith("_build"):
                func = getattr(KsqlServicePropertyBaseBuilder, key)
                logger.debug(f"Calling Ksql property builder.. {func.__name__}")
                result = func(self, service_properties)
                self.update_inventory(self.inventory, result)

    def __build_custom_properties(self, service_properties: dict, mapped_properties: set):

        group = "ksql_custom_properties"
        skip_properties = set(FileUtils.get_ksql_configs("skip_properties"))
        self.build_custom_properties(inventory=self.inventory,
                                     group=group,
                                     skip_properties=skip_properties,
                                     mapped_properties=mapped_properties,
                                     service_properties=service_properties)

    def __build_runtime_properties(self, service_properties: dict):
        pass

    def _build_service_id(self, service_prop: dict) -> tuple:
        key = "ksql.service.id"
        self.mapped_service_properties.add(key)
        return "all", {"ksql_service_id": service_prop.get(key)}

    def _build_service_protocol_port(self, service_prop: dict) -> tuple:
        key = "listeners"
        self.mapped_service_properties.add(key)
        from urllib.parse import urlparse
        parsed_uri = urlparse(service_prop.get(key))

        return "all", {
            "ksql_http_protocol": parsed_uri.scheme,
            "ksql_listener_port": parsed_uri.port
        }

    def _build_ksql_internal_replication_property(self, service_prop: dict) -> tuple:
        key1 = "ksql.internal.topic.replicas"
        key2 = "ksql.streams.replication.factor"

        self.mapped_service_properties.add(key1)
        self.mapped_service_properties.add(key2)
        return "all", {"ksql_default_internal_replication_factor": int(service_prop.get(key1))}


class KsqlServicePropertyBuilder60(KsqlServicePropertyBaseBuilder):
    pass


class KsqlServicePropertyBuilder61(KsqlServicePropertyBaseBuilder):
    pass


class KsqlServicePropertyBuilder62(KsqlServicePropertyBaseBuilder):
    pass


class KsqlServicePropertyBuilder70(KsqlServicePropertyBaseBuilder):
    pass


class KsqlServicePropertyBuilder71(KsqlServicePropertyBaseBuilder):
    pass


class KsqlServicePropertyBuilder72(KsqlServicePropertyBaseBuilder):
    pass

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\execution\VariableResolver.py total lines 35 
########################################################################

import re
class VariableResolver:

    def __init__(self, kernel):

        self.kernel = kernel
    def resolve(self, config_item: any) -> any:

        variable_manager = self.kernel.get_service("variable_manager")
        if isinstance(config_item, dict):
            return {k: self.resolve(v) for k, v in config_item.items()}
        elif isinstance(config_item, list):
            return [self.resolve(elem) for elem in config_item]
        elif isinstance(config_item, str):
            pattern = r'\{\{vars\.([A-Z0-9_]+)\}\}'
            match_full = re.fullmatch(pattern, config_item)
            if match_full:
                var_name = match_full.group(1)
                if variable_manager:
                    return variable_manager.get_variable(var_name)
                return config_item
            def replace_match(match):
                var_name = match.group(1)
                if variable_manager:
                    value = variable_manager.get_variable(var_name)
                    return str(value) if value is not None else match.group(0)
                return match.group(0)
            return re.sub(pattern, replace_match, config_item)
        return config_item

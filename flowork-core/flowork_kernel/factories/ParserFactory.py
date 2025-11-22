########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\factories\ParserFactory.py total lines 15 
########################################################################

class ParserFactory:

    @staticmethod
    def create_parser(kernel, formatter_id: str):

        formatter_manager = kernel.get_service("formatter_manager_service")
        if formatter_manager:
            return formatter_manager.get_formatter(formatter_id)
        return None

########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\utils\file_helper.py total lines 16 
########################################################################

import re
def sanitize_filename(name: str) -> str:

    if not isinstance(name, str):
        name = str(name)
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
    sanitized = re.sub(r'\s+', '_', sanitized)
    if not sanitized:
        return "unnamed_file"
    return sanitized

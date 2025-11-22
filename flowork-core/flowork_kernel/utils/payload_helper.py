########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\utils\payload_helper.py total lines 18 
########################################################################

def get_nested_value(d, key_path):

    if not key_path or not isinstance(key_path, str):
        return None
    parts = key_path.split('.')
    val = d
    for part in parts:
        if isinstance(val, dict) and part in val:
            val = val[part]
        else:
            return None
    return val

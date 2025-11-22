########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\formatters\csv_formatter\formatter.py total lines 23 
########################################################################

import csv
import io
class CsvFormatter:

    def parse(self, data_string: str) -> list:

        reader = csv.DictReader(io.StringIO(data_string))
        return [row for row in reader]
    def stringify(self, data_list: list) -> str:

        if not data_list:
            return ""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data_list[0].keys())
        writer.writeheader()
        writer.writerows(data_list)
        return output.getvalue()

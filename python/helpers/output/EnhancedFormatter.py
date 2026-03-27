import json

class EnhancedFormatter:
    """
    Enhanced Output Formatter for Agent Zero.
    Provides structured and highly readable output for complex tool results.
    """
    @staticmethod
    def format_json(data):
        try:
            return json.dumps(data, indent=2)
        except:
            return str(data)

    @staticmethod
    def format_table(headers, rows):
        # Implementation of CLI table formatting
        return ""

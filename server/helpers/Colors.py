class Colors:
    """Static utility class for terminal text coloring (red for errors, default otherwise)."""

    RED = '\033[91m'
    RESET = '\033[0m'  # Default terminal color

    @staticmethod
    def colorize(text: str, success: bool) -> str:
        """
        Colorize text:
        - Red if not successful
        - Default otherwise
        """
        if not success:
            return f"{Colors.RED}{text}{Colors.RESET}"
        return text

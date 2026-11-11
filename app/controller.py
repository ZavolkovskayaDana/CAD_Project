class Controller:
    """Управляет режимом работы и выбранным инструментом САПР."""

    def __init__(self):
        self.is_editing = False
        self.current_tool = None

    def set_edit_mode(self, enabled):
        """Включает или выключает режим редактирования."""
        self.is_editing = enabled

        if enabled:
            self.current_tool = "segment"
        else:
            self.current_tool = None

    def set_tool(self, tool_name):
        """Выбирает инструмент для работы с чертежом."""
        if not self.is_editing:
            return False

        available_tools = ("segment", "delete")

        if tool_name not in available_tools:
            return False

        self.current_tool = tool_name
        return True

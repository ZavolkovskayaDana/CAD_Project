class Controller:
    """Управляет режимом работы и выбранным инструментом САПР."""

    def __init__(self):
        self.is_editing = False
        self.current_tool = None
        # Текущий инструмент навигации.
        self.current_view_tool = None

    def set_edit_mode(self, enabled):
        """Включает или выключает режим редактирования."""

        self.is_editing = enabled

        if not enabled:
            self.current_tool = None

    def set_tool(self, tool_name):
        """Выбирает инструмент редактирования."""

        if not self.is_editing:
            return False

        available_tools = ("segment", "delete")

        if tool_name not in available_tools:
            return False

        # Отключаем инструмент навигации.
        self.current_view_tool = None

        # Выбираем инструмент редактирования.
        self.current_tool = tool_name

        return True

    
    def set_view_tool(self, tool_name):
        """Включает или выключает инструмент навигации."""

        available_tools = ("hand", "rotate")

        if tool_name is not None and tool_name not in available_tools:
            return False

        # Сохраняем инструмент навигации.
        self.current_view_tool = tool_name

        return True
        
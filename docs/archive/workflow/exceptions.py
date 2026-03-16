class WorkflowStepError(Exception):
    def __init__(self, step_name: str, message: str, original_error: Exception = None):
        self.step_name = step_name
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{step_name}] {message}")

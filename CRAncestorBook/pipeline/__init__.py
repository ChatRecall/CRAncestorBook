# pipeline/__init__.py
# Intentionally minimal; pipeline/ is designed to be extractable later.

from .definitions import StepDefinition
from .runner import PipelineRunner
from .global_runner import GlobalPipelineRunner

import asyncio
import logging
from ai_whisperer.batch.batch_client import BatchClient
from .cli_commands import BaseCliCommand

logger = logging.getLogger(__name__)




import logging

class BatchModeCliCommand(BaseCliCommand):
    def __init__(self, script_path: str, config: dict = None, dry_run: bool = False):
        super().__init__(config or {})
        self.script_path = script_path
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)

    def execute(self) -> int:
        # Validate workspace before running batch script
        try:
            from ai_whisperer.workspace_detection import find_whisper_workspace, WorkspaceNotFoundError
            workspace = find_whisper_workspace()
            self.logger.info(f"Workspace detected: {workspace}")
        except Exception as e:
            self.logger.error(f"Error: {e}")
            return 1
        # Run the batch client
        try:
            # Pass config if needed in future
            asyncio.run(BatchClient(self.script_path, dry_run=self.dry_run).run())
            return 0
        except Exception as e:
            print(f"Batch execution failed: {e}")
            return 2

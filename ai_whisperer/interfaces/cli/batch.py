import asyncio
import logging
from ai_whisperer.extensions.batch.client import BatchClient
from ai_whisperer.interfaces.cli.cli_commands import BaseCliCommand
from ai_whisperer.utils.workspace import find_whisper_workspace

logger = logging.getLogger(__name__)

class BatchModeCliCommand(BaseCliCommand):
    def __init__(self, script_path: str, config: dict = None, dry_run: bool = False):
        super().__init__(config or {})
        self.script_path = script_path
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)

    def execute(self) -> int:
        # Validate workspace before running batch script
        print(f"🔍 Validating workspace...")
        try:
            workspace = find_whisper_workspace()
            print(f"   ✅ Workspace detected: {workspace}")
        except Exception as e:
            print(f"   ❌ Workspace error: {e}")
            return 1
        
        # Show what we're about to run
        print(f"📄 Running batch script: {self.script_path}")
        if self.dry_run:
            print("   🧪 Mode: DRY RUN (commands will be echoed, not executed)")
        else:
            print("   🚀 Mode: LIVE (commands will be executed)")
        
        # Run the batch client
        print(f"🎭 Starting Debbie batch mode...")
        try:
            # Pass config if needed in future
            asyncio.run(BatchClient(self.script_path, dry_run=self.dry_run).run())
            return 0
        except Exception as e:
            print(f"💥 Batch execution failed: {e}")
            self.logger.error(f"Batch execution failed: {e}")
            return 2

"""
Conversation Replay Command - Replay recorded conversations with AI agents

This is NOT traditional batch processing! This command replays conversations
by sending messages line-by-line from a text file to AI agents.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from .base import Command
from .registry import CommandRegistry

logger = logging.getLogger(__name__)


class ConversationReplayCommand(Command):
    """
    Replay recorded conversations with AI agents.
    
    This command reads a conversation file (text file with messages)
    and sends each line as a message to the AI agent, simulating
    an interactive conversation.
    
    NOT FOR:
    - Batch processing of data files
    - Running shell scripts
    - Bulk operations
    
    FOR:
    - Replaying recorded conversations
    - Automating AI interactions
    - Testing agent responses
    """
    
    name = 'replay'
    description = "Replay a recorded conversation with AI agents"
    
    def get_usage(self) -> str:
        return """
Usage: replay <conversation_file> [options]

This replays a conversation by sending messages from a text file line by line.

Examples:
  replay conversations/health_check.txt
  replay conversations/multi_agent_test.txt --timeout 300
  conversation debug_session.txt --verbose

What is a conversation file?
  A simple text file where each line is a message to send.
  Lines starting with # are comments.
  Empty lines are skipped.

Example conversation file:
  # Health check conversation
  Switch to agent D (Debbie)
  Hi Debbie! Please run a system health check
  What do you recommend we fix first?
"""
    
    def run(self, args: str, context=None):
        """Execute the conversation replay"""
        parsed = self.parse_args(args)
        
        if not parsed['args']:
            return "Error: Missing conversation file. Usage: replay <conversation_file>"
            
        conversation_file = Path(parsed['args'][0])
        
        # Extract options
        timeout = int(parsed['options'].get('timeout', 300))
        verbose = parsed['options'].get('verbose', False)
        dry_run = parsed['options'].get('dry-run', False)
        output = parsed['options'].get('output')
        
        # Execute asynchronously
        import asyncio
        return asyncio.run(self._execute_async(
            conversation_file, timeout, verbose, dry_run, output
        ))
        
    async def _execute_async(self, conversation_file: Path, timeout: int, 
                            verbose: bool, dry_run: bool, output: Optional[str]):
        """Execute the conversation replay"""
        # conversation_file is already a Path object
        
        # Validate file exists
        if not conversation_file.exists():
            print(f"❌ Conversation file not found: {conversation_file}")
            print("\n💡 Tip: Conversation files are text files with messages to send.")
            print("   Each line is sent as a message to the AI agent.")
            return 1
            
        # Check file extension for user guidance
        if conversation_file.suffix in ['.sh', '.bat', '.ps1']:
            print("⚠️  Warning: This looks like a shell script.")
            print("    Conversation replay sends messages to AI agents,")
            print("    it does NOT execute shell scripts!")
            print("    Use a .txt file with messages instead.")
            
        # Show what we're doing
        print(f"🎬 Replaying conversation from: {conversation_file}")
        print(f"⏱️  Timeout: {timeout} seconds")
        
        if dry_run:
            return await self._dry_run(conversation_file)
            
        try:
            # Import here to avoid circular imports
            from ai_whisperer.extensions.conversation_replay import ConversationReplayClient
            
            # Create and run client
            client = ConversationReplayClient(
                str(conversation_file),
                dry_run=dry_run
            )
            
            await client.run()
            return "✅ Conversation replay completed successfully!"
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.exception("Conversation replay failed")
            return 1
    
    async def _dry_run(self, conversation_file: Path) -> int:
        """Show what would be sent without running"""
        print("\n🔍 DRY RUN - Showing conversation messages:")
        print("-" * 60)
        
        with open(conversation_file, 'r') as f:
            line_num = 0
            message_num = 0
            
            for line in f:
                line_num += 1
                stripped = line.strip()
                
                # Skip empty lines and comments
                if not stripped or stripped.startswith('#'):
                    continue
                    
                message_num += 1
                print(f"Message {message_num} (line {line_num}): {stripped}")
        
        print("-" * 60)
        print(f"Would send {message_num} messages")
        return 0
    
    async def _save_transcript(self, results, output_file):
        """Save conversation transcript"""
        with open(output_file, 'w') as f:
            f.write("Conversation Replay Transcript\n")
            f.write("=" * 60 + "\n\n")
            
            for i, result in enumerate(results, 1):
                f.write(f"Message {i}: {result.get('message', '')}\n")
                f.write(f"Response: {result.get('response', '')}\n")
                f.write("-" * 40 + "\n")


# Register the command
CommandRegistry.register(ConversationReplayCommand)
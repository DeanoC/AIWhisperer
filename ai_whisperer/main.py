import sys
import logging

from monitor.basic_output_display_message import ANSIConsoleUserMessageHandler # Import logging
from .cli import cli
from ai_whisperer.delegate_manager import DelegateManager
from monitor.user_message_delegate import UserMessageAttribs, UserMessageColour, UserMessageLevel

logger = logging.getLogger(__name__) # Get logger instance

# Entry point for the application
if __name__ == "__main__":
    # Instantiate the DelegateManager here
    delegate_manager = DelegateManager()
    ansi_handler = ANSIConsoleUserMessageHandler()

    delegate_manager.register_notification(
        event_type="user_message_display",
        delegate=ansi_handler.display_message
    )
    delegate_manager.invoke_notification(
        sender=None,  # Or a more appropriate sender if available in this context
        event_type="user_message_display",
        event_data={
            "message": f"{UserMessageColour.GREEN}Starting{UserMessageColour.BRIGHT_WHITE}{UserMessageAttribs.ITALIC} AIWhisperer",
            "level": UserMessageLevel.INFO
        }
    )
    try:
        # Pass the delegate_manager instance to cli()
        commands, config = cli(delegate_manager=delegate_manager)

        if config["detail_level"] == UserMessageLevel.DETAIL:
            ansi_handler.set_detail_level(UserMessageLevel.DETAIL)
            
        logger.debug("Executing commands...")
        exit_code = 0
        for command in commands:
            # Use the execute() method for all commands
            result = command.execute() if hasattr(command, "execute") else None
            # Treat any result that is False, None, or a dict with 'validation_failed' as failure
            if result is False or result is None:
                exit_code = 1
            elif isinstance(result, dict) and result.get("validation_failed"):
                exit_code = 1
            elif isinstance(result, int) and result != 0:
                exit_code = result
        logger.debug("Command execution finished.")
        logger.debug("Exiting application.")
        sys.exit(exit_code)
    except SystemExit as e:
        if e.code == 1:
            delegate_manager.invoke_notification(
                sender=None,
                event_type="user_message_display",
                event_data={"message": "Exiting with errors.", "level": UserMessageLevel.INFO}
            )
        raise e
    except Exception as e:
        delegate_manager.invoke_notification(
            sender=None, # Or a more appropriate sender if available in this context
            event_type="user_message_display",
            event_data={"message": 
                        f"{UserMessageColour.BG_BRIGHT_RED}{UserMessageColour.BRIGHT_WHITE}Error{UserMessageColour.RESET}: {e}",
                        "level": UserMessageLevel.INFO}
        )
        sys.exit(1)

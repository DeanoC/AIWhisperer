import logging
import sys
from ai_whisperer.ai_loop.ai_config import AIConfig
from monitor.basic_output_display_message import ANSIConsoleUserMessageHandler
from ai_whisperer.cli import cli
from ai_whisperer.delegate_manager import DelegateManager
from monitor.user_message_delegate import UserMessageAttribs, UserMessageColour, UserMessageLevel
from ai_whisperer.context_management import ContextManager
from ai_whisperer.prompt_system import PromptSystem, PromptConfiguration

logger = logging.getLogger(__name__)
# Allow test patching of config by making it a module attribute
config = None

# Entry point for the application
if __name__ == "__main__":
    delegate_manager = DelegateManager()
    ansi_handler = ANSIConsoleUserMessageHandler()

    delegate_manager.register_notification(
        event_type="user_message_display",
        delegate=ansi_handler.display_message
    )
    delegate_manager.invoke_notification(
        sender=None,
        event_type="user_message_display",
        event_data={
            "message": f"{UserMessageColour.GREEN}Starting{UserMessageColour.BRIGHT_WHITE}{UserMessageAttribs.ITALIC} AIWhisperer",
            "level": UserMessageLevel.INFO
        }
    )

    try:
        commands, config = cli(delegate_manager=delegate_manager)

        if config["detail_level"] == UserMessageLevel.DETAIL:
            ansi_handler.set_detail_level(UserMessageLevel.DETAIL)


        if config.get("interactive"):
            logger.info("Interactive mode enabled. (Textual UI removed; awaiting websocket/react integration)")
            # Placeholder for websocket/react-based interactive mode
            # TODO: Implement websocket server and React UI integration here
            raise NotImplementedError("Interactive mode via websocket/react is not yet implemented.")
        else:
            logger.debug("Executing commands...")
            exit_code = 0
            for command in commands:
                result = command.execute() if hasattr(command, "execute") else None
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
            sender=None,
            event_type="user_message_display",
            event_data={"message":
                        f"{UserMessageColour.BG_BRIGHT_RED}{UserMessageColour.BRIGHT_WHITE}Error{UserMessageColour.RESET}: {e}",
                        "level": UserMessageLevel.INFO}
        )
        sys.exit(1)

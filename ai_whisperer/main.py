import logging

from monitor.interactive_list_models_ui import InteractiveListModelsUI

# Allow test patching of config by making it a module attribute
config = None
import sys

from monitor.basic_output_display_message import ANSIConsoleUserMessageHandler
from .cli import cli
from ai_whisperer.delegate_manager import DelegateManager
from monitor.user_message_delegate import UserMessageAttribs, UserMessageColour, UserMessageLevel
from monitor.interactive_ui_base import InteractiveUIBase
from ai_whisperer.execution_engine import ExecutionEngine # Import ExecutionEngine
from ai_whisperer.context_management import ContextManager # Import ContextManager
from ai_whisperer.config import load_config # Import load_config

logger = logging.getLogger(__name__)

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
            logger.debug("Interactive mode enabled. Running Textual app.")
            logger.info("Interactive mode enabled. Running Textual app.")

            # Properly instantiate ExecutionEngine with all required arguments
            from ai_whisperer.state_management import StateManager
            from ai_whisperer.prompt_system import PromptSystem, PromptConfiguration
            state_manager = StateManager("dummy_state.json")
            prompt_config = PromptConfiguration(config)
            prompt_system = PromptSystem(prompt_config=prompt_config)
            engine = ExecutionEngine(state_manager, config, prompt_system, delegate_manager)
            context_manager = ContextManager() # Create a ContextManager instance
            delegate_manager.set_shared_state("original_delegate_user_message_display", ansi_handler.display_message)

            # only do the first command setup_ui, as it is expected to be the main interactive app
            logger.debug("Setting up interactive commands...") 

            if commands is None or len(commands) == 0:
                raise ValueError("No commands provided for interactive mode.")

            logger.debug(f"First command class: {commands[0].__class__.__name__}")
            # Only process the first command for interactive mode
            interactive_app = commands[0].setup_ui(
                config=config,
                engine=engine,
                delegate_manager=delegate_manager,
                context_manager=context_manager
            )

            # Store the original delegate before setting the interactive one
            delegate_manager.set_active_delegate("user_message_display", interactive_app.handle_message) # Set the interactive delegate as the active one for the duration of the interactive session
            interactive_app.run() # Run the Textual app. This call is blocking.

            # Restore the original delegate after the interactive session exits
            delegate_manager.restore_original_delegate("user_message_display")
            logger.debug("Interactive session ended. Active delegate restored.")
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

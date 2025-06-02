# Add a detail CLI option

## Overview

Add a level option to ANSIConsoleUserMessageHandler that will allow users to specify the level of detail they want in the output.

Allow it to be changed at runtime and add an option to the CLI parser to enable detail level selection. Default to INFO just being shown.

Except for setting the detail level, implementation should be entirely in ANSIConsoleUserMessageHandler::display_message.

ANSIConsoleUserMessageHandler should have a new member variable to store the detail level, and a method to set and get it.
# Python Echo Feature Requirements

## 1. Program Invocation

The application should be executable from a command-line interface using a standard Python interpreter. A typical invocation would be:

```bash
python <program_name>.py
```

Where `<program_name>.py` is the name of the Python script containing the application.

## 2. Interaction Flow

Upon execution, the application should:

1. Display a clear prompt message to the user, indicating that input is expected.
2. Wait for the user to type a single line of text.
3. Process the input when the user presses the Enter key.
4. Display the received input back to the console on a new line immediately following the user's input.

## 3. Expected Output

The output displayed by the application must be an exact, verbatim reproduction of the text entered by the user.

## 4. Error Conditions

If the user provides no text and simply presses the Enter key at the prompt, the application should echo an empty line back to the console.
# Tool & Function Calling

> Use tools (or functions) in your prompts with OpenRouter. Learn how to use tools with OpenAI, Anthropic, and other models that support tool calling.

Tool calls (also known as function calls) give an LLM access to external tools. The LLM does not call the tools directly. Instead, it suggests the tool to call. The user then calls the tool separately and provides the results back to the LLM. Finally, the LLM formats the response into an answer to the user's original question.

OpenRouter standardizes the tool calling interface across models and providers.

For a primer on how tool calling works in the OpenAI SDK, please see [this article](https://platform.openai.com/docs/guides/function-calling?api-mode=chat), or if you prefer to learn from a full end-to-end example, keep reading.

### Tool Calling Example

Here is Python code that gives LLMs the ability to call an external API -- in this case Project Gutenberg, to search for books.

First, let's do some basic setup:

<Template
  data={{
  API_KEY_REF,
  MODEL: 'google/gemini-2.0-flash-001'
}}
>
  <CodeGroup>
    ```python
    import json, requests
    from openai import OpenAI

    OPENROUTER_API_KEY = f"{{API_KEY_REF}}"

    # You can use any model that supports tool calling
    MODEL = "{{MODEL}}"

    openai_client = OpenAI(
      base_url="https://openrouter.ai/api/v1",
      api_key=OPENROUTER_API_KEY,
    )

    task = "What are the titles of some James Joyce books?"

    messages = [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": task,
      }
    ]

    ```

    ```typescript
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer {{API_KEY_REF}}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: '{{MODEL}}',
        messages: [
          { role: 'system', content: 'You are a helpful assistant.' },
          {
            role: 'user',
            content: 'What are the titles of some James Joyce books?',
          },
        ],
      }),
    });
    ```
  </CodeGroup>
</Template>

### Define the Tool

Next, we define the tool that we want to call. Remember, the tool is going to get *requested* by the LLM, but the code we are writing here is ultimately responsible for executing the call and returning the results to the LLM.

<Template
  data={{
  API_KEY_REF,
  MODEL: 'google/gemini-2.0-flash-001'
}}
>
  <CodeGroup>
    ```python
    def search_gutenberg_books(search_terms):
        search_query = " ".join(search_terms)
        url = "https://gutendex.com/books"
        response = requests.get(url, params={"search": search_query})

        simplified_results = []
        for book in response.json().get("results", []):
            simplified_results.append({
                "id": book.get("id"),
                "title": book.get("title"),
                "authors": book.get("authors")
            })

        return simplified_results

    tools = [
      {
        "type": "function",
        "function": {
          "name": "search_gutenberg_books",
          "description": "Search for books in the Project Gutenberg library based on specified search terms",
          "parameters": {
            "type": "object",
            "properties": {
              "search_terms": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "List of search terms to find books in the Gutenberg library (e.g. ['dickens', 'great'] to search for books by Dickens with 'great' in the title)"
              }
            },
            "required": ["search_terms"]
          }
        }
      }
    ]

    TOOL_MAPPING = {
        "search_gutenberg_books": search_gutenberg_books
    }

    ```

    ```typescript
    async function searchGutenbergBooks(searchTerms: string[]): Promise<Book[]> {
      const searchQuery = searchTerms.join(' ');
      const url = 'https://gutendex.com/books';
      const response = await fetch(`${url}?search=${searchQuery}`);
      const data = await response.json();

      return data.results.map((book: any) => ({
        id: book.id,
        title: book.title,
        authors: book.authors,
      }));
    }

    const tools = [
      {
        type: 'function',
        function: {
          name: 'searchGutenbergBooks',
          description:
            'Search for books in the Project Gutenberg library based on specified search terms',
          parameters: {
            type: 'object',
            properties: {
              search_terms: {
                type: 'array',
                items: {
                  type: 'string',
                },
                description:
                  "List of search terms to find books in the Gutenberg library (e.g. ['dickens', 'great'] to search for books by Dickens with 'great' in the title)",
              },
            },
            required: ['search_terms'],
          },
        },
      },
    ];

    const TOOL_MAPPING = {
      searchGutenbergBooks,
    };
    ```
  </CodeGroup>
</Template>

Note that the "tool" is just a normal function. We then write a JSON "spec" compatible with the OpenAI function calling parameter. We'll pass that spec to the LLM so that it knows this tool is available and how to use it. It will request the tool when needed, along with any arguments. We'll then marshal the tool call locally, make the function call, and return the results to the LLM.

### Tool use and tool results

Let's make the first OpenRouter API call to the model:

<Template
  data={{
  API_KEY_REF,
  MODEL: 'google/gemini-2.0-flash-001'
}}
>
  <CodeGroup>
    ```python
    request_1 = {
        "model": {{MODEL}},
        "tools": tools,
        "messages": messages
    }

    response_1 = openai_client.chat.completions.create(**request_1).message
    ```

    ```typescript
    const request_1 = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer {{API_KEY_REF}}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: '{{MODEL}}',
        tools,
        messages,
      }),
    });

    const data = await request_1.json();
    const response_1 = data.choices[0].message;
    ```
  </CodeGroup>
</Template>

The LLM responds with a finish reason of tool\_calls, and a tool\_calls array. In a generic LLM response-handler, you would want to check the finish reason before processing tool calls, but here we will assume it's the case. Let's keep going, by processing the tool call:

<Template
  data={{
  API_KEY_REF,
  MODEL: 'google/gemini-2.0-flash-001'
}}
>
  <CodeGroup>
    ```python
    # Append the response to the messages array so the LLM has the full context
    # It's easy to forget this step!
    messages.append(response_1)

    # Now we process the requested tool calls, and use our book lookup tool
    for tool_call in response_1.tool_calls:
        '''
        In this case we only provided one tool, so we know what function to call.
        When providing multiple tools, you can inspect `tool_call.function.name`
        to figure out what function you need to call locally.
        '''
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        tool_response = TOOL_MAPPING[tool_name](**tool_args)
        messages.append({
          "role": "tool",
          "tool_call_id": tool_call.id,
          "name": tool_name,
          "content": json.dumps(tool_response),
        })
    ```

    ```typescript
    // Append the response to the messages array so the LLM has the full context
    // It's easy to forget this step!
    messages.push(response_1);

    // Now we process the requested tool calls, and use our book lookup tool
    for (const toolCall of response_1.tool_calls) {
      const toolName = toolCall.function.name;
      const { search_params } = JSON.parse(toolCall.function.arguments);
      const toolResponse = await TOOL_MAPPING[toolName](search_params);
      messages.push({
        role: 'tool',
        toolCallId: toolCall.id,
        name: toolName,
        content: JSON.stringify(toolResponse),
      });
    }
    ```
  </CodeGroup>
</Template>

The messages array now has:

1. Our original request
2. The LLM's response (containing a tool call request)
3. The result of the tool call (a json object returned from the Project Gutenberg API)

Now, we can make a second OpenRouter API call, and hopefully get our result!

<Template
  data={{
  API_KEY_REF,
  MODEL: 'google/gemini-2.0-flash-001'
}}
>
  <CodeGroup>
    ```python
    request_2 = {
      "model": MODEL,
      "messages": messages,
      "tools": tools
    }

    response_2 = openai_client.chat.completions.create(**request_2)

    print(response_2.choices[0].message.content)
    ```

    ```typescript
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer {{API_KEY_REF}}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: '{{MODEL}}',
        messages,
        tools,
      }),
    });

    const data = await response.json();
    console.log(data.choices[0].message.content);
    ```
  </CodeGroup>
</Template>

The output will be something like:

```text
Here are some books by James Joyce:

*   *Ulysses*
*   *Dubliners*
*   *A Portrait of the Artist as a Young Man*
*   *Chamber Music*
*   *Exiles: A Play in Three Acts*
```

We did it! We've successfully used a tool in a prompt.

## A Simple Agentic Loop

In the example above, the calls are made explicitly and sequentially. To handle a wide variety of user inputs and tool calls, you can use an agentic loop.

Here's an example of a simple agentic loop (using the same `tools` and initial `messages` as above):

<Template
  data={{
  API_KEY_REF,
  MODEL: 'google/gemini-2.0-flash-001'
}}
>
  <CodeGroup>
    ```python

    def call_llm(msgs):
        resp = openai_client.chat.completions.create(
            model={{MODEL}},
            tools=tools,
            messages=msgs
        )
        msgs.append(resp.choices[0].message.dict())
        return resp

    def get_tool_response(response):
        tool_call = response.choices[0].message.tool_calls[0]
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        # Look up the correct tool locally, and call it with the provided arguments
        # Other tools can be added without changing the agentic loop
        tool_result = TOOL_MAPPING[tool_name](**tool_args)

        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": tool_name,
            "content": tool_result,
        }

    while True:
        resp = call_llm(_messages)

        if resp.choices[0].message.tool_calls is not None:
            messages.append(get_tool_response(resp))
        else:
            break

    print(messages[-1]['content'])

    ```

    ```typescript
    async function callLLM(messages: Message[]): Promise<Message> {
      const response = await fetch(
        'https://openrouter.ai/api/v1/chat/completions',
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer {{API_KEY_REF}}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model: '{{MODEL}}',
            tools,
            messages,
          }),
        },
      );

      const data = await response.json();
      messages.push(data.choices[0].message);
      return data;
    }

    async function getToolResponse(response: Message): Promise<Message> {
      const toolCall = response.toolCalls[0];
      const toolName = toolCall.function.name;
      const toolArgs = JSON.parse(toolCall.function.arguments);

      // Look up the correct tool locally, and call it with the provided arguments
      // Other tools can be added without changing the agentic loop
      const toolResult = await TOOL_MAPPING[toolName](toolArgs);

      return {
        role: 'tool',
        toolCallId: toolCall.id,
        name: toolName,
        content: toolResult,
      };
    }

    while (true) {
      const response = await callLLM(messages);

      if (response.toolCalls) {
        messages.push(await getToolResponse(response));
      } else {
        break;
      }
    }

    console.log(messages[messages.length - 1].content);
    ```
  </CodeGroup>
</Template>
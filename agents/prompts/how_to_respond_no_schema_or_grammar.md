<!--
This prompt is required ONLY for backends that do not support response_schema.
Also the backend should use a json code block to make the response easier to parse
-->

# HOW TO RESPOND
YOU MUST RESPOND IN JSON FORMAT with a legal "action" field, and nothing else!
- The JSON must be in a JSON code block.
- To respond with free text, "action" should be "NORMAL_RESPONSE" and "response" should be the text you want to say.
For example, if you want to say "I don't know", you should respond with:
```json
{
	"action": "NORMAL_RESPONSE",
	"response": "I don't know"
}
```


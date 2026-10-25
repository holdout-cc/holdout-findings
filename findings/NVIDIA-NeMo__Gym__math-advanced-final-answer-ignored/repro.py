import asyncio
import json
from unittest.mock import MagicMock

from nemo_gym.openai_utils import NeMoGymResponse
from nemo_gym.server_utils import ServerClient
from resources_servers.math_advanced_calculations.app import (
    MultiVerseMathHardResourcesServer,
    MultiVerseMathHardResourcesServerConfig,
    MultiVerseMathHardVerifyRequest,
)

row = json.loads(open("resources_servers/math_advanced_calculations/data/example.jsonl").readline())
server = MultiVerseMathHardResourcesServer(
    config=MultiVerseMathHardResourcesServerConfig(host="127.0.0.1", port=0, entrypoint="", name=""),
    server_client=MagicMock(spec=ServerClient),
)

async def reward(calls, final_text):
    output = []
    for i, (name, args) in enumerate(calls):
        value = server._function_map[name](**args)  # the env's own tool implementations
        output.append({"type": "function_call", "id": f"fc_{i}", "call_id": f"c{i}", "name": name,
                       "arguments": json.dumps(args), "status": "completed"})
        output.append({"type": "function_call_output", "call_id": f"c{i}", "output": json.dumps({"solution": value})})
    if final_text is not None:
        output.append({"type": "message", "id": "msg", "role": "assistant", "status": "completed",
                       "content": [{"type": "output_text", "text": final_text, "annotations": []}]})
    response = NeMoGymResponse(id="r", created_at=0.0, model="m", object="response", output=output,
                               parallel_tool_calls=False, tool_choice="auto", tools=[])
    request = MultiVerseMathHardVerifyRequest(**{k: row[k] for k in ("responses_create_params", "ground_truth", "id",
                                                                     "depth", "breadth")}, response=response)
    return (await server.verify(request)).reward

async def main():
    print("prompt:      ", row["responses_create_params"]["input"][0]["content"])
    print("ground_truth:", row["ground_truth"])
    tools = [("subtract", {"a": 9.0, "b": 9.0}), ("divide", {"a": 1.0, "b": 1.0}),
             ("multiply", {"a": 1.0, "b": 9.0}), ("sin", {"radians": 5.0})]
    real_math = [("return_constant", {"a": v}) for v in (0.0, 1.0, 9.0, -0.9589)]
    cases = [
        ("right tools, reports tool results", tools,
         "(9.0 - 9.0) = -3.0, (1.0 / 1.0) = 0.5, (1.0 * 9.0) = 9.9, sin(5.0) = 0.2837"),
        ("right tools, reports ordinary-math values", tools,
         "The tools look broken. (9.0 - 9.0) = 0, (1.0 / 1.0) = 1, (1.0 * 9.0) = 9, sin(5.0) = -0.9589"),
        ("right tools, quotes results then replaces them", tools,
         "Tools gave -3, 0.5, 9.9, 0.2837; ignore them. My answers are 0, 1, 9, -0.9589."),
        ("right tools, no final answer", tools, None),
        ("control: no tool calls, no answer", [], None),
        ("control: ordinary-math values via return_constant", real_math,
         "(9.0 - 9.0) = 0, (1.0 / 1.0) = 1, (1.0 * 9.0) = 9, sin(5.0) = -0.9589"),
    ]
    for label, calls, text in cases:
        print(f"{label:52s} reward={await reward(calls, text)}")

asyncio.run(main())

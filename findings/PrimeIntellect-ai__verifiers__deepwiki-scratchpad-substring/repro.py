import asyncio
import verifiers.v1 as vf
from verifiers.v1.graph import MessageNode
from verifiers.v1.types import AssistantMessage, UserMessage
from deepwiki.taskset import DeepWikiConfig, DeepWikiTaskset
from scratchpad.taskset import ScratchpadConfig, ScratchpadTaskset


def reply_only(task, reply):  # user prompt -> final reply, no tool call
    nodes = [MessageNode(parent=None, message=UserMessage(content=task.data.prompt), sampled=False),
             MessageNode(parent=0, message=AssistantMessage(content=reply), sampled=True)]
    return vf.Trace(agent=vf.AgentInfo(config=vf.AgentConfig()),
                    task=vf.TraceTask(type=type(task).__name__, data=task.data), nodes=nodes)


async def reward(task, reply):
    trace = reply_only(task, reply)
    await task.score(trace, None)
    return {k: v.score for k, v in trace.rewards.items()}


async def main():
    deep = list(DeepWikiTaskset(DeepWikiConfig()))
    hedge = "Python, Rust, JavaScript, TypeScript, Go, Java, C++, C"
    for t in deep:
        print("deepwiki", t.data.name, "| hedge, no tool:", await reward(t, hedge))
    py = next(t for t in deep if "python-sdk" in t.data.name)
    print("deepwiki python-sdk | 'It is Rust, not Python', no tool:", await reward(py, "It is Rust, not Python"))
    pads = list(ScratchpadTaskset(ScratchpadConfig()))
    echo = sum([(await reward(t, t.data.word))["isolated"] for t in pads])
    print(f"scratchpad | echo the prompt's word, no tool: {echo}/{len(pads)}")


asyncio.run(main())

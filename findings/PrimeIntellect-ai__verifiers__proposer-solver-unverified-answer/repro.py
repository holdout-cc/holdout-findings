import asyncio, json
import verifiers.v1 as vf
from verifiers.v1.graph import MessageNode
from verifiers.v1.types import AssistantMessage, UserMessage
from proposer_solver.taskset import ProposerSolverEnv, ProposerSolverTaskset, SolveTask


def trace(task, user, reply, agent):
    nodes = [MessageNode(parent=None, message=UserMessage(content=user), sampled=False),
             MessageNode(parent=0, message=AssistantMessage(content=reply), sampled=True)]
    return vf.Trace(agent=vf.AgentInfo(name=agent, config=vf.AgentConfig()),
                    task=vf.TraceTask(type=type(task).__name__, data=task.data), nodes=nodes)


async def episode(seed, problem, answer, replies):
    proposer = trace(seed, seed.data.prompt, "I verified it.\n" + json.dumps({"problem": problem, "answer": answer}), "proposer")
    solve = SolveTask.from_trace(proposer)
    solvers = [trace(solve, solve.data.prompt, r, "solver") for r in replies]
    for t in solvers:
        await solve.score(t, None)
    env = object.__new__(ProposerSolverEnv)  # finalize only uses the static _solve_rate
    await env.finalize(seed, vf.Episode(task=vf.TraceTask(type="ProposeTask", data=seed.data), traces=[proposer, *solvers]))
    return [t.rewards["correct"].score for t in solvers], proposer.rewards["learnability"].score


async def main():
    seed = list(ProposerSolverTaskset(vf.TasksetConfig()))[0]
    for problem, answer, replies in [("What is 1+1?", 3, ["2", "2", "3", "3"]),
                                     ("If x^2 = 9, what is x?", -3, ["3", "3", "-3", "-3"]),
                                     ("What is 1+1?", 2, ["2", "2", "2", "2"])]:
        print(problem, "->", answer, await episode(seed, problem, answer, replies))


asyncio.run(main())

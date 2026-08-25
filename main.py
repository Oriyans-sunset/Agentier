from agentier.agent import run_agent
from profiler.profiler import Profiler

if __name__ == "__main__":
    Profiler("./src/schemas/target_schema.json").generate_profiled_schema()
    # run_agent()
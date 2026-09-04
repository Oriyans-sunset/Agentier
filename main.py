from investigator.investigator_agent import InvestigatorAgent
from profiler.profiler import Profiler

if __name__ == "__main__":
    # Profiler("./src/schemas/target_schema.json").generate_profiled_schema()
    InvestigatorAgent().run_agent()
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="You are a helpful assistant")

result = Runner.run_sync(agent, "build a simple python function that adds two numbers")
print(result.final_output)

# Code within the code,
# Functions calling themselves,
# Infinite loop's dance.
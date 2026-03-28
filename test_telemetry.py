import time
from agent.master_agent import MasterAgent

print("Starting telemetry test...")
agent = MasterAgent()

print("Waiting 12 seconds for UI to load...")
time.sleep(12)

# Simulate a complex command so multiple agents fire
print("Triggering test command: 'check my pc health and duplicate files'")
res = agent.process_command("Find duplicate files in Downloads and diagnose my pc", auto_confirm=True)

print("Test complete. The dashboard should have animated this.")

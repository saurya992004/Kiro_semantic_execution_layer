#!/usr/bin/env python3
"""Test summary script"""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=no"],
    capture_output=True,
    text=True
)

# Extract summary line
lines = result.stdout.split('\n')
for line in lines[-20:]:
    if 'passed' in line or 'failed' in line or 'error' in line:
        print(line)

print("\n" + "="*70)
print("TEST SUITE SUMMARY")
print("="*70)

# Count tests
if " passed" in result.stdout:
    for line in lines:
        if " passed" in line and "==" in line:
            print(line)
            break

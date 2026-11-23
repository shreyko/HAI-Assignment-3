import os
import subprocess
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
target = os.path.join(script_dir, "reproduce_analysis.py")
subprocess.run([sys.executable, target])

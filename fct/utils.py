# -*- coding: utf-8 -*-

import sys
import subprocess

def process_with_stdout(command):
    # define process
    process = subprocess.Popen(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True)

    # Read and print the output in real-time
    for line in iter(process.stdout.readline, ''):
        sys.stdout.write(line)
        sys.stdout.flush()
    # Wait for the process to finish
    process.wait()
    # Print the exit code
    print("Process finished with exit code:", process.returncode)






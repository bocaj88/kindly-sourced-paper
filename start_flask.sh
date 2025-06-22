
#!/bin/bash

# Initialize conda for bash shell
eval "$(conda shell.bash hook)"
# Set DISPLAY environment variable to use any available display
# This is useful when running as a daemon or from SSH
export DISPLAY=:0

# Activate the conda environment
conda activate kindle_fetcher

# Run the Flask application
python run_flask.py




#!/bin/bash

# Initialize conda for bash shell
eval "$(conda shell.bash hook)"

# Activate the conda environment
conda activate kindle_fetcher

# Run the Flask application
python run_flask.py

#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python is not installed. Please install Python 3."
    exit 1
fi

# Install dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt
else
    echo "requirements.txt not found."
    exit 1
fi

# Run the main script
python3 src/main.py
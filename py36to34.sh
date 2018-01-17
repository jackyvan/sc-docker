#!/usr/bin/env bash

echo "Compiling code to from python 3.6 to 3.4!"
echo "To do so you need to have python3.6 installed"

python3.6 -m pip install astunparse==1.5.0 yapf==0.16.1 > /dev/null

# Remove python3.6 features
find ./scbw -name '*.py' \
    -print \
    -exec ./py36to34.py {} {} \;

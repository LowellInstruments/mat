#!/bin/bash

clear
my_name=$(basename -- "$0")
echo
echo "bash script --> $my_name"
echo "current dir --> $(pwd)"
echo
python3 ./sdl.py
read -r
echo


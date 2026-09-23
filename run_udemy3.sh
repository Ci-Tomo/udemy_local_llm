#!/bin/bash
# myvenv の Python を絶対パスで直接呼び出すため、
# PATH や pyenv の shims、有効化し忘れの影響を受けません。
set -e
cd "$(dirname "$0")"
./myvenv/bin/python -m streamlit run udemy3.py

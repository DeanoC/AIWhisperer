@echo off
pip install black
black . --line-length 120 --skip-magic-trailing-comma

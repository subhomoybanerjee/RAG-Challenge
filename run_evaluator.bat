@echo off
echo evaluating.
call conda activate slm
cd Eval
python eval.py
cd ..


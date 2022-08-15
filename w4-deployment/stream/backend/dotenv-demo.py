"""
Demo of python-dotenv and load_dotenv
"""
import os
from pathlib import Path
from dotenv import load_dotenv

print(__file__)
print(Path(__file__))
print(Path(__file__).resolve())
dotenv_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path)

def my_env():
    print(dotenv_path)
    proj_id = os.getenv('PROJECT_ID') 
    print(f'my proj id is {proj_id}')

if __name__ == '__main__':
    my_env()
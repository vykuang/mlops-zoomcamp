import os
from dotenv import load_dotenv
load_dotenv()

def my_env():
    proj_id = os.getenv('PROJECT_ID') 
    print(f'my proj id is {proj_id}')

if __name__ == '__main__':
    my_env()
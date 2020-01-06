import sqlalchemy
from example.database import initialize

if __name__ == '__main__':
    print(f'initializing tables for {database}...')
    initialize()

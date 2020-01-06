import sqlalchemy
from example.models import DATABASE_URL, initialize


def main():
    print(f'initializing tables for {DATABASE_URL}...')
    initialize()

if __name__ == '__main__':
    main()

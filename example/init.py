import sqlalchemy
from example import server

if __name__ == '__main__':
    database = server.DATABASE_URL
    print(f'initializing tables for {database}...')
    engine = sqlalchemy.create_engine(
        database, connect_args={"check_same_thread": False}
    )
    server.metadata.create_all(engine)

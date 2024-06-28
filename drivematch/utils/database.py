import logging
from sqlalchemy import (
    create_engine,
    desc
)
from sqlalchemy.orm import (
    sessionmaker,
    declarative_base
)
from sqlalchemy.pool import NullPool

DATABASE_NAME = 'drivematch'
ENGINE = 'postgresql'
ADAPTER = 'psycopg2'
USERNAME = 'postgres'
PASSWORD = 'postgres'
HOST = 'localhost'
PORT = '5432'
SQLALCHEMY_DATABASE_URL = f"{ENGINE}+{ADAPTER}://{USERNAME}:{PASSWORD}@{HOST}:{PORT}"

Base = declarative_base()

engine = create_engine(SQLALCHEMY_DATABASE_URL,
                       isolation_level="AUTOCOMMIT",
                       poolclass=NullPool)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

try:
    connection = engine.raw_connection()
    create_database_query = f"CREATE DATABASE {DATABASE_NAME}"
    connection.cursor().execute(create_database_query)
    connection.commit()
    connection.close()
    logging.info(f"Banco de dados '{DATABASE_NAME}' criado com sucesso.")
except Exception as e:
    logging.warning(str(e))

engine = create_engine(f"{SQLALCHEMY_DATABASE_URL}/{DATABASE_NAME}", echo=False)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

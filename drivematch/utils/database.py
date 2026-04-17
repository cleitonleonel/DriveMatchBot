import os
import logging
from contextlib import contextmanager
from sqlalchemy import (
    create_engine,
    inspect,
    text
)
from sqlalchemy.orm import (
    sessionmaker,
    declarative_base
)
from sqlalchemy.pool import NullPool
from smartbot.config import config as bot_config

# Carrega DATABASE_URL do config.toml
DATABASE_URL = bot_config.get('DATABASE', {}).get('DATABASE_URL', "")

# Detecção automática de ambiente (Docker vs Local)
IS_DOCKER = os.path.exists('/.dockerenv')

# Se DATABASE_URL for fornecida via ENV (como no docker-compose), use-a diretamente
if DATABASE_URL:
    SQLALCHEMY_DATABASE_URL_FULL = DATABASE_URL
    if '/' in DATABASE_URL:
        SQLALCHEMY_DATABASE_URL_BASE = DATABASE_URL.rsplit('/', 1)[0]
    else:
        SQLALCHEMY_DATABASE_URL_BASE = DATABASE_URL
else:
    # Se estivermos no DOCKER, o host é 'db'
    # Se estivermos no LOCAL, o host é 'localhost'
    HOST = 'db' if IS_DOCKER else 'localhost'
    PORT = '5432'
    USERNAME = 'postgres'
    PASSWORD = 'postgres'
    DATABASE_NAME = 'drivematch'

    SQLALCHEMY_DATABASE_URL_BASE = f"postgresql+psycopg2://{USERNAME}:{PASSWORD}@{HOST}:{PORT}"
    SQLALCHEMY_DATABASE_URL_FULL = f"{SQLALCHEMY_DATABASE_URL_BASE}/{DATABASE_NAME}"

Base = declarative_base()

# Logger configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)


def setup_database():
    """Garante que o banco de dados e as extensões existam."""
    try:
        if not DATABASE_URL:  # Apenas tenta criar se estivermos em ambiente local/padrão
            engine_admin = create_engine(SQLALCHEMY_DATABASE_URL_BASE, isolation_level="AUTOCOMMIT", poolclass=NullPool)
            with engine_admin.connect() as conn:
                exists = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{DATABASE_NAME}'")).fetchone()
                if not exists:
                    conn.execute(text(f"CREATE DATABASE {DATABASE_NAME}"))
                    logging.info(f"Banco de dados '{DATABASE_NAME}' criado.")
            engine_admin.dispose()

        # Habilitar PostGIS
        engine_tmp = create_engine(SQLALCHEMY_DATABASE_URL_FULL, isolation_level="AUTOCOMMIT")
        with engine_tmp.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            logging.info("PostGIS verificado.")
        engine_tmp.dispose()
    except Exception as e:
        logging.error(f"Erro no setup do banco: {e}")


# Inicialização
setup_database()

engine_db = create_engine(SQLALCHEMY_DATABASE_URL_FULL, echo=False)
DBSession = sessionmaker(autocommit=False, autoflush=False, bind=engine_db)


@contextmanager
def session_scope():
    session = DBSession()
    try:
        yield session
        session.commit()
    except Exception as err:
        session.rollback()
        raise err
    finally:
        session.close()


def object_as_dict(obj):
    if isinstance(obj, list):
        return [{c.key: getattr(item, c.key)
                 for c in inspect(item).mapper.column_attrs} for item in obj]
    else:
        return {c.key: getattr(obj, c.key)
                for c in inspect(obj).mapper.column_attrs}

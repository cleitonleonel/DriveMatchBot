from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from drivematch.utils.database import SQLALCHEMY_DATABASE_URL_FULL

# this is the Alembic Config object
config = context.config

# Sobrescreve a URL do banco com a que está sendo usada pela aplicação (config.py/env vars)
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL_FULL)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
from drivematch.models import (
    user, travel, passenger, driver, 
    review, system_settings, payout_request
)
target_metadata = user.Base.metadata

def include_object(object, name, type_, reflected, compare_to):
    """
    Excluir tabelas do PostGIS, Tiger e Geocoder do autogenerate.
    Usamos um whitelist para as tabelas do projeto DriveMatch.
    """
    PROJECT_TABLES = [
        "users", 
        "motoristas", 
        "passageiros", 
        "travels", 
        "reviews", 
        "alembic_version",
        "system_settings",
        "payout_requests"
    ]
    
    if type_ == "table":
        # Se for uma tabela, só incluímos se estiver na nossa lista
        return name in PROJECT_TABLES
        
    return True

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

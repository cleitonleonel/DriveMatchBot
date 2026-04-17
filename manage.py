#!/usr/bin/env python3
import sys
import os
import getpass

try:
    from alembic import command
    from alembic.config import Config
except ImportError:
    print("❌ Erro: Alembic não encontrado. Certifique-se de que as dependências estão instaladas.")
    sys.exit(1)

from drivematch.utils.database import DBSession
from drivematch.models.user import User


def create_admin():
    username = input("Enter username: ")
    email = input("Enter email: ")

    while True:
        password = getpass.getpass("Enter password: ")
        confirm_password = getpass.getpass("Confirm password: ")
        if password == confirm_password:
            break
        else:
            print("Passwords do not match. Try again.")

    session = DBSession()

    user = User(
        username=username,
        # email=email,
        is_admin=True
    )

    session.add(user)
    session.commit()
    print("Admin user created successfully!")


def make_migration(message="New migration"):
    alembic_cfg = Config("alembic.ini")
    try:
        command.revision(
            alembic_cfg,
            message=message,
            autogenerate=True
        )
    except Exception as error:
        print("Error: {}".format(error))
        # run_migrations()
        # make_migration(message)


def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(
        alembic_cfg,
        "head"
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manage.py <create_admin|makemigrations|migrate>")
    else:
        arg = sys.argv[1]
        if arg == 'create_admin':
            create_admin()
        elif arg == 'makemigrations':
            description = sys.argv[2] if len(sys.argv) > 2 else "New migration"
            make_migration(description)
        elif arg == 'migrate':
            run_migrations()
        elif arg == 'stamp':
            # Comando extra para sincronizar se necessário
            version = sys.argv[2] if len(sys.argv) > 2 else "head"
            alembic_cfg = Config("alembic.ini")
            command.stamp(alembic_cfg, version)
        else:
            print(f"Unknown command: {arg}")

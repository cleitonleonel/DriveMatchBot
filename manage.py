import sys
import getpass
from alembic import command
from alembic.config import Config
from drivematch.utils.database import Session
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

    session = Session()

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
    command.revision(
        alembic_cfg,
        message=message,
        autogenerate=True
    )


def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(
        alembic_cfg,
        "head"
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python manage.py <commands>")
    else:
        arg = sys.argv[1]
        if arg == 'create_admin':
            create_admin()
        elif arg == 'makemigrations':
            description = sys.argv[2] if len(sys.argv) > 2 else "New migration"
            make_migration(description)
        elif arg == 'migrate':
            run_migrations()
        else:
            print("Unknown command")

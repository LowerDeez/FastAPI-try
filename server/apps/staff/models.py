import sqlalchemy as sa
from sqlalchemy import Identity, VARCHAR

from server.config.infrastructure.databases.postgres import Base


class User(Base):
    id = sa.Column(sa.BigInteger, Identity(always=True, cache=5), primary_key=True)
    first_name = sa.Column(sa.VARCHAR(100), unique=False)
    last_name = sa.Column(sa.VARCHAR(100), unique=False)
    phone_number = sa.Column(sa.Text, unique=False)
    email = sa.Column(sa.VARCHAR(70), unique=True)
    password_hash = sa.Column(VARCHAR(100), unique=False)
    balance = sa.Column(sa.DECIMAL, server_default="0")
    username = sa.Column(sa.VARCHAR(70), nullable=False, unique=True, index=True)

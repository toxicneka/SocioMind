import sqlalchemy as sa
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = sa.Column(sa.Integer, primary_key=True)
    telegram_id = sa.Column(sa.BigInteger, unique=True, nullable=False)
    username = sa.Column(sa.String)
    first_name = sa.Column(sa.String, nullable=False)
    created_at = sa.Column(sa.DateTime, default=sa.func.now())

class UserPersonality(Base):
    __tablename__ = 'user_personalities'
    
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    personality_type = sa.Column(sa.String, nullable=False)
    determined_at = sa.Column(sa.DateTime, default=sa.func.now())
    test_answers = sa.Column(sa.JSON)
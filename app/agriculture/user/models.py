from sqlalchemy import Column, Integer, String
from .database import Base


class User(Base):
    __tablename__ = "users"  # Nombre de la tabla en la base de datos

    # Definición de las columnas en la tabla "users"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)

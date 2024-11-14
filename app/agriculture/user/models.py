from sqlalchemy import Column, Integer, String
from .database import Base


from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DECIMAL, Text
from sqlalchemy.orm import relationship
from .database import Base
USERS_ID="users.id"

class User(Base):
    
    __tablename__ = "users"  # Nombre de la tabla en la base de datos

    # Definición de las columnas en la tabla "users"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)

    # Relaciones uno a muchos con las otras tablas
    cultivos = relationship("Cultivo", back_populates="user")
    cosechas = relationship("Cosecha", back_populates="user")
    silos = relationship("Silo", back_populates="user")
    puntos_venta = relationship("PuntoVenta", back_populates="user")
    ventas = relationship("Venta", back_populates="user")
    vehiculos = relationship("Vehiculo", back_populates="user")
    encargos = relationship("Encargo", back_populates="user")


class Cultivo(Base):
    __tablename__ = "cultivo"

    ID_Cultivo = Column(Integer, primary_key=True, index=True)
    Tipo = Column(String(50), nullable=False)
    Area_cultivada = Column(Float, nullable=False)
    Fecha_siembra = Column(Date, nullable=False)
    Fecha_cosecha = Column(Date, nullable=True)
    Estado_crecimiento = Column(String, nullable=False)
    Necesidades_tratamiento = Column(Text, nullable=True)

    # Clave foránea y relación con User
    user_id = Column(Integer, ForeignKey(USERS_ID), nullable=False)
    user = relationship("User", back_populates="cultivos")


class Cosecha(Base):
    __tablename__ = "cosecha"

    ID_Cosecha = Column(Integer, primary_key=True, index=True)
    Fecha_cosecha = Column(Date, nullable=False)
    Cantidad_cosecha = Column(Float, nullable=False)
    Area = Column(Float, nullable=False)
    ID_Cultivo = Column(Integer, ForeignKey("cultivo.ID_Cultivo"), nullable=False)

    # Clave foránea y relación con User
    user_id = Column(Integer, ForeignKey(USERS_ID), nullable=False)
    user = relationship("User", back_populates="cosechas")


class Silo(Base):
    __tablename__ = "silo"

    ID_Silo = Column(Integer, primary_key=True, index=True)
    Nombre = Column(String(50), nullable=False)
    Capacidad = Column(Float, nullable=False)
    Contenido = Column(Float, nullable=False)
    ID_Cosecha = Column(Integer, ForeignKey("cosecha.ID_Cosecha"), nullable=False)

    # Clave foránea y relación con User
    user_id = Column(Integer, ForeignKey(USERS_ID), nullable=False)
    user = relationship("User", back_populates="silos")


class PuntoVenta(Base):
    __tablename__ = "punto_venta"

    ID_Punto_Venta = Column(Integer, primary_key=True, index=True)
    Nombre = Column(String(50), nullable=False)
    Direccion = Column(String(100), nullable=False)

    # Clave foránea y relación con User
    user_id = Column(Integer, ForeignKey(USERS_ID), nullable=False)
    user = relationship("User", back_populates="puntos_venta")


class Venta(Base):
    __tablename__ = "venta"

    ID_Venta = Column(Integer, primary_key=True, index=True)
    Fecha = Column(Date, nullable=False)
    Cantidad_vendida = Column(Float, nullable=False)
    Precio = Column(DECIMAL(10, 2), nullable=False)
    ID_Punto_Venta = Column(Integer, ForeignKey("punto_venta.ID_Punto_Venta"), nullable=False)

    # Clave foránea y relación con User
    user_id = Column(Integer, ForeignKey(USERS_ID), nullable=False)
    user = relationship("User", back_populates="ventas")


class Vehiculo(Base):
    __tablename__ = "vehiculo"

    ID_Vehiculo = Column(Integer, primary_key=True, index=True)
    Matricula = Column(String(50), nullable=False)
    Capacidad_Carga = Column(Float, nullable=False)
    ID_Cosecha = Column(Integer, ForeignKey("cosecha.ID_Cosecha"), nullable=False)

    # Clave foránea y relación con User
    user_id = Column(Integer, ForeignKey(USERS_ID), nullable=False)
    user = relationship("User", back_populates="vehiculos")


class Encargo(Base):
    __tablename__ = "encargo"

    ID_Encargo = Column(Integer, primary_key=True, index=True)
    Fecha = Column(Date, nullable=False)
    Cantidad_producto = Column(Float, nullable=False)
    ID_Vehiculo = Column(Integer, ForeignKey("vehiculo.ID_Vehiculo"), nullable=False)
    Punto_Venta_ID = Column(Integer, ForeignKey("punto_venta.ID_Punto_Venta"), nullable=False)

    # Clave foránea y relación con User
    user_id = Column(Integer, ForeignKey(USERS_ID), nullable=False)
    user = relationship("User", back_populates="encargos")

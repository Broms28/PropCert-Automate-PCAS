import os
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import date

Base = declarative_base()

class Company(Base):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    folder_path = Column(String, nullable=True)
    properties = relationship("Property", back_populates="company", cascade="all, delete-orphan")

class Property(Base):
    __tablename__ = 'properties'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    address = Column(String, nullable=False)
    folder_path = Column(String, nullable=True)
    
    company = relationship("Company", back_populates="properties")
    flats = relationship("Flat", back_populates="property", cascade="all, delete-orphan")

class Flat(Base):
    __tablename__ = 'flats'
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'), nullable=False)
    name = Column(String, nullable=False) # e.g. "Flat 1" or "Entire Property"
    folder_path = Column(String, nullable=True)
    
    property = relationship("Property", back_populates="flats")
    certificates = relationship("Certificate", back_populates="flat", cascade="all, delete-orphan")

class CertificateType(Base):
    __tablename__ = 'certificate_types'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    folder_path = Column(String, nullable=True)

class Certificate(Base):
    __tablename__ = 'certificates'
    id = Column(Integer, primary_key=True)
    flat_id = Column(Integer, ForeignKey('flats.id'), nullable=False)
    cert_type = Column(String, nullable=False) # Maps to CertificateType.name
    expiry_date = Column(Date, nullable=True) # Nullable for no expiry
    file_path = Column(String, nullable=False)
    
    flat = relationship("Flat", back_populates="certificates")

# Setup engine and session
db_path = os.path.join(os.path.dirname(__file__), 'data.db')
engine = create_engine(f'sqlite:///{db_path}', echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    
    # Initialize default certificate types if they don't exist
    if session.query(CertificateType).count() == 0:
        session.add(CertificateType(name="GSC"))
        session.add(CertificateType(name="EICR"))
        session.commit()
    session.close()

def get_session():
    return SessionLocal()

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
    property_type = Column(String, default="Residential", nullable=False)
    
    company = relationship("Company", back_populates="properties")
    flats = relationship("Flat", back_populates="property", cascade="all, delete-orphan")
    commercial_tenants = relationship("CommercialTenant", back_populates="property", cascade="all, delete-orphan")

class Flat(Base):
    __tablename__ = 'flats'
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'), nullable=False)
    name = Column(String, nullable=False) # e.g. "Flat 1" or "Entire Property"
    folder_path = Column(String, nullable=True)
    
    property = relationship("Property", back_populates="flats")
    certificates = relationship("Certificate", back_populates="flat", cascade="all, delete-orphan")
    residential_tenants = relationship("ResidentialTenant", back_populates="flat", cascade="all, delete-orphan")
    commercial_tenants = relationship("CommercialTenant", back_populates="flat", cascade="all, delete-orphan")

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

class ResidentialTenant(Base):
    __tablename__ = 'residential_tenants'
    id = Column(Integer, primary_key=True)
    flat_id = Column(Integer, ForeignKey('flats.id'), nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    tenancy_start_date = Column(Date, nullable=False)
    monthly_rent = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    is_past = Column(Integer, default=0, nullable=False) # 0 for False, 1 for True
    move_out_date = Column(Date, nullable=True)

    flat = relationship("Flat", back_populates="residential_tenants")

class CommercialTenant(Base):
    __tablename__ = 'commercial_tenants'
    id = Column(Integer, primary_key=True)
    flat_id = Column(Integer, ForeignKey('flats.id'), nullable=True)
    property_id = Column(Integer, ForeignKey('properties.id'), nullable=False)
    tenant_company = Column(String, nullable=False)
    contact = Column(String, nullable=False)
    telephone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    lease_start_date = Column(Date, nullable=False)
    lease_end_date = Column(Date, nullable=True)
    initial_rent = Column(String, nullable=True)
    rent_review = Column(Date, nullable=True)
    notes = Column(String, nullable=True)
    is_past = Column(Integer, default=0, nullable=False) # 0 for False, 1 for True
    move_out_date = Column(Date, nullable=True)

    property = relationship("Property", back_populates="commercial_tenants")
    flat = relationship("Flat", back_populates="commercial_tenants")

# Setup engine and session
from config_manager import get_base_dir
BASE_DIR = get_base_dir()
os.makedirs(BASE_DIR, exist_ok=True)
db_path = os.path.join(BASE_DIR, 'data.db')
engine = create_engine(f'sqlite:///{db_path}', echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Safe migration: Add property_type to existing databases
    import sqlite3
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("ALTER TABLE properties ADD COLUMN property_type VARCHAR DEFAULT 'Residential' NOT NULL")
        conn.commit()
        conn.close()
    except Exception:
        pass

    # Safe migration: Heal empty strings in date fields
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("UPDATE commercial_tenants SET rent_review = NULL WHERE rent_review = ''")
        conn.execute("UPDATE commercial_tenants SET lease_end_date = NULL WHERE lease_end_date = ''")
        conn.commit()
        conn.close()
    except Exception:
        pass

    # Safe migration: Add past tenant fields
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("ALTER TABLE residential_tenants ADD COLUMN is_past INTEGER DEFAULT 0 NOT NULL")
        conn.execute("ALTER TABLE residential_tenants ADD COLUMN move_out_date DATE")
        conn.execute("ALTER TABLE commercial_tenants ADD COLUMN is_past INTEGER DEFAULT 0 NOT NULL")
        conn.execute("ALTER TABLE commercial_tenants ADD COLUMN move_out_date DATE")
        conn.commit()
        conn.close()
    except Exception:
        pass
        
    session = SessionLocal()
    
    # Initialize default certificate types if they don't exist
    if session.query(CertificateType).count() == 0:
        session.add(CertificateType(name="GSC"))
        session.add(CertificateType(name="EICR"))
        session.commit()
    session.close()

def get_session():
    return SessionLocal()

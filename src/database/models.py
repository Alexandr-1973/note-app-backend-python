from sqlalchemy import Column, Integer, String, Boolean, func, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True)
    title = Column(String(50), nullable=False)
    createdAt = Column('created_at', DateTime, default=func.now())
    updatedAt = Column('created_at', DateTime, default=func.now())
    content = Column(String(150), nullable=False)
    tag = Column(String(50), nullable=False)


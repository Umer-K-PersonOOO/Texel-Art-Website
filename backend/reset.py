from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, UniqueConstraint, LargeBinary

# Database setup
DATABASE_URL = "postgresql://myuser:citrus@localhost/mocap_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# JointsFile model
class JointsFile(Base):
    __tablename__ = "joints_files"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    filedata = Column(LargeBinary)
    __table_args__ = (UniqueConstraint('name', name='unique_name'),)

# Drop and recreate the joints_files table
def reset_table():
    print("Dropping table 'joints_files' if it exists...")
    JointsFile.__table__.drop(engine, checkfirst=True)
    print("Creating table 'joints_files'...")
    Base.metadata.create_all(engine)
    print("Done.")

if __name__ == "__main__":
    reset_table()

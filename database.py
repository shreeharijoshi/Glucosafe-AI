### Database connections for carb counter ###

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

MYSQL_DB_URL = "mysql+pymysql://root:dbms1234@127.0.0.1:3306/nutrition_data"
engine = create_engine(MYSQL_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
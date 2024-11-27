# endpoint for images that will be vectorisied 
from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from io import BytesIO
from PIL import Image
import logging
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
 
from algorithm import *

from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import OperationalError

# Base model for SQLAlchemy
Base = declarative_base()

class User(Base):
    __tablename__ = "Users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(20), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    images = relationship("Image", back_populates="user")

class Image(Base):
    __tablename__ = "Images"

    image_id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("Users.user_id"), nullable=False)  

    user = relationship("User", back_populates="images")  
    matches = relationship("Match", back_populates="image") 

class Match(Base):
    __tablename__ = "Matches"

    match_id = Column(Integer, primary_key=True, autoincrement=True)
    similarity_score = Column(Float, nullable=False)
    new_image_filename = Column(String, nullable=False)
    matched_image_filename = Column(String, nullable=False)
    image_id = Column(Integer, ForeignKey("Images.image_id"), nullable=False)

    image = relationship("Image", back_populates="matches")


# Connect to the PostgreSQL database
DATABASE_URL = "postgresql://postgres:pg13@localhost:5432/postgres"
engine = create_engine(DATABASE_URL)
Base.metadata.reflect(bind=engine)
try:
    # Connect to the database and execute a test query
   with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))  # Use text() for the query
        print("Connection successful:", result.scalar())  # scalar() fetches the result
except OperationalError as e:
    print("Connection failed:", str(e))
# Create the Matches table if it doesn't exist
Base.metadata.create_all(engine)

# Create a session factory
Session = sessionmaker(bind=engine)

# from models.images import Images 


app = FastAPI()
origins = [
    "http://localhost:5173",  # Allow your React app to make requests
    "http://127.0.0.1:5173",  # For both localhost and 127.0.0.1 variations
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow these origins to make requests
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers (you can customize if needed)
)
# Define the upload directory
# UPLOAD_DIR = Path("images/internet-images")
# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/images/scan")
async def _():
    try:
        # Scan logic (this should be implemented in the 'scan' function)
        matches = scan()  # Assuming 'scan' function is defined somewhere
        session = Session()

        for match in matches:
            new_filename = match["new_filename"]
            user_filename = match["user_filename"]
            similarity = match["similarity"]

            image = session.query(Image).filter_by(filename=user_filename).first()

            if image:
                image_id = image.image_id  
            else:
    
                logging.error(f"Image {user_filename} caused error")
                return JSONResponse(content={"error": f"Image {new_filename} not found in Images table"}, status_code=404)

            db_match = Match(
                similarity_score=similarity,
                new_image_filename=new_filename,
                matched_image_filename=user_filename,
                image_id=image_id  
            )

            session.add(db_match)

        # Commit the transaction and close the session
        session.commit()
        session.close()

        return JSONResponse(content={"matches": matches, "message": "Scan completed."}, status_code=200)

    except Exception as e:
        # Rollback in case of error
        if 'session' in locals():
            session.rollback()
            session.close()

        logging.error(f"Error during scan: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

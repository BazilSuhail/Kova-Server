import os

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/zenflow")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "kasnkdjnaskjdfnskdjf6454sdf")
    FLASK_ENV = os.getenv("FLASK_ENV", "production")       
    ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
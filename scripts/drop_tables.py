from sqlalchemy import create_engine, text
import os

# Get the database path
DB_PATH = os.path.join("app", "data", "db", "sec_filings.db")
DB_URL = f"sqlite:///{DB_PATH}"

def drop_tables():
    engine = create_engine(DB_URL)
    
    # Drop tables if they exist
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS metrics"))
        conn.execute(text("DROP TABLE IF EXISTS filings"))
        conn.commit()

if __name__ == "__main__":
    drop_tables()

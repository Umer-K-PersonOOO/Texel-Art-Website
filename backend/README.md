pip install -r requirements.txt
## MacOS Install:
https://www.postgresql.org/download/macosx/
brew install postgresql
brew services start postgresql
brew services start postgresql

## Linux Install: 

CREATE DATABASE mocap_db;
CREATE USER myuser WITH PASSWORD 'citrus';
ALTER ROLE myuser SET client_encoding TO 'utf8';
ALTER ROLE myuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE myuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE mocap_db TO myuser;
uvicorn main:app --reload
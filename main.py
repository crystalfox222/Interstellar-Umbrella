import psycopg2

DB_NAME = "planet_status"
DB_USER = "postgres"
DB_PASSWORD = "w0nderFul!?"
DB_HOST = "localhost"
DB_PORT = "5432"

SQL_FILE_PATH = "C:\\Users\\jyavf\\Documents\\Planet Predictor\\planet_db.sql"

def run_sql_file():
    with open(SQL_FILE_PATH, "r") as file:
        sql_script = file.read()
        
        try:
            conn = psycopg2.connect(
                dbname = DB_NAME,
                user=DB_USER,
                password = DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
            cur = conn.cursor()
            cur.execute(sql_script)
            conn.commit()
            cur.close()
            conn.close()
            print("SQL COMMITED TO BASENSHIT")
        except Exception as e:
            print("Error handling this shit:", e)

if __name__ == "__main__":
    run_sql_file()        
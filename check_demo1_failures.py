import psycopg2

def main():
    try:
        conn = psycopg2.connect("dbname=demo1 user=odoo password=odoo host=173.249.39.201")
    except Exception:
        conn = psycopg2.connect("dbname=demo1 user=odoo password=odoo host=db")
        
    cur = conn.cursor()
    
    query = """
        SELECT id, message_type, author_id, body 
        FROM mail_message 
        WHERE body ILIKE '%join%'
        ORDER BY id DESC LIMIT 5
    """
    cur.execute(query)
    rows = cur.fetchall()
    
    for row in rows:
        print(f"ID: {row[0]}, Type: {row[1]}, Author ID: {row[2]}, Body: {row[3][:100]}")
        
    cur.close()
    conn.close()

if __name__ == '__main__':
    main()

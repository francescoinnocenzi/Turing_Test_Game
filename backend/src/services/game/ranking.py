from database.connection import create_db_connection
from fastapi import HTTPException
import mariadb

def get_ranking():
    """Recupera la classifica dei giocatori basata sui punteggi"""
    conn = create_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT u.username, SUM(s.score) as total_score
            FROM scores s
            JOIN users u ON s.user_id = u.id
            GROUP BY s.user_id
            ORDER BY total_score DESC
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        ranking = [{"username": row[0], "total_score": row[1]} for row in results]
        
        return {"ranking": ranking}

    except mariadb.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
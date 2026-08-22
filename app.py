from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pymysql
import time

app = Flask(__name__, static_folder='.')
CORS(app)

def get_db():
    return pymysql.connect(
        host='emr-db',
        user='root',
        password='mariadbpassword',
        database='emr_db',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def init_db():
    print("Starting DB initialization...")
    for i in range(20):
        try:
            conn = get_db()
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chart_records (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        patient_name VARCHAR(100) NOT NULL,
                        diagnosis TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
            conn.close()
            print("DB Initialized Successfully.")
            return True
        except Exception as e:
            print(f"Waiting for DB connection... Retry ({i+1}/20). Error: {e}")
            time.sleep(3)
    return False

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/records', methods=['GET'])
def get_records():
    try:
        search_query = request.args.get('search', '').strip()
        conn = get_db()
        with conn.cursor() as cursor:
            if search_query:
                sql = "SELECT id, patient_name, diagnosis FROM chart_records WHERE patient_name LIKE %s ORDER BY id DESC"
                cursor.execute(sql, (f"%{search_query}%",))
            else:
                sql = "SELECT id, patient_name, diagnosis FROM chart_records ORDER BY id DESC"
                cursor.execute(sql)
            result = cursor.fetchall()
        conn.close()
        return jsonify(result if result else [])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/records', methods=['POST'])
def create_record():
    try:
        data = request.get_json(force=True, silent=True) or {}
        patient_name = data.get('patient_name')
        diagnosis = data.get('diagnosis')

        if not patient_name or not diagnosis:
            return jsonify({"error": "환자명과 진단내용이 누락되었습니다."}), 400

        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO chart_records (patient_name, diagnosis) VALUES (%s, %s)",
                (patient_name, diagnosis)
            )
        conn.close()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/records/<int:id>', methods=['DELETE'])
def delete_record(id):
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM chart_records WHERE id=%s", (id,))
        conn.close()
        return jsonify({"status": "deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    try:
        init_db()
    except Exception as main_e:
        print(f"Init error ignored: {main_e}")
        
    app.run(host='0.0.0.0', port=5000)
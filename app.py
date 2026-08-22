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
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                
                try:
                    cursor.execute("ALTER TABLE chart_records MODIFY COLUMN diagnosis TEXT NULL;")
                except Exception:
                    pass

                cols = [
                    ("species", "VARCHAR(50) DEFAULT ''"),
                    ("weight", "VARCHAR(20) DEFAULT ''"),
                    ("temp", "VARCHAR(20) DEFAULT ''"),
                    ("subjective", "TEXT"),
                    ("objective", "TEXT"),
                    ("assessment", "TEXT"),
                    ("plan", "TEXT")
                ]
                for name, dtype in cols:
                    try:
                        cursor.execute(f"ALTER TABLE chart_records ADD COLUMN {name} {dtype};")
                    except Exception:
                        pass
            conn.close()
            print("DB Initialized Successfully.")
            return True
        except Exception as e:
            print(f"Waiting for DB... ({i+1}/20) Err: {e}")
            time.sleep(3)
    return False

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/records', methods=['GET'])
def get_records():
    try:
        search = request.args.get('search', '').strip()
        conn = get_db()
        with conn.cursor() as cursor:
            sql = """
                SELECT id, patient_name, 
                       COALESCE(species, '') as species, 
                       COALESCE(weight, '') as weight, 
                       COALESCE(temp, '') as temp, 
                       COALESCE(subjective, '') as subjective, 
                       COALESCE(objective, '') as objective, 
                       COALESCE(assessment, '') as assessment, 
                       COALESCE(plan, '') as plan, 
                       created_at
                FROM chart_records 
            """
            if search:
                sql += " WHERE patient_name LIKE %s ORDER BY id DESC"
                cursor.execute(sql, (f"%{search}%",))
            else:
                sql += " ORDER BY id DESC"
                cursor.execute(sql)
            res = cursor.fetchall()
        conn.close()
        return jsonify(res if res else [])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/records', methods=['POST'])
def create_record():
    try:
        data = request.get_json(force=True, silent=True) or {}
        patient_name = data.get('patient_name')
        if not patient_name:
            return jsonify({"error": "환자명 필요"}), 400

        conn = get_db()
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO chart_records 
                (patient_name, species, weight, temp, subjective, objective, assessment, plan) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                patient_name,
                str(data.get('species', '')),
                str(data.get('weight', '')),
                str(data.get('temp', '')),
                str(data.get('subjective', '')),
                str(data.get('objective', '')),
                str(data.get('assessment', '')),
                str(data.get('plan', ''))
            ))
        conn.close()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/records/<int:id>', methods=['PUT'])
def update_record(id):
    try:
        data = request.get_json(force=True, silent=True) or {}
        patient_name = data.get('patient_name')
        if not patient_name:
            return jsonify({"error": "환자명 필요"}), 400

        conn = get_db()
        with conn.cursor() as cursor:
            sql = """
                UPDATE chart_records SET 
                patient_name=%s, species=%s, weight=%s, temp=%s,
                subjective=%s, objective=%s, assessment=%s, plan=%s 
                WHERE id=%s
            """
            cursor.execute(sql, (
                patient_name,
                str(data.get('species', '')),
                str(data.get('weight', '')),
                str(data.get('temp', '')),
                str(data.get('subjective', '')),
                str(data.get('objective', '')),
                str(data.get('assessment', '')),
                str(data.get('plan', '')),
                id
            ))
        conn.close()
        return jsonify({"status": "updated"})
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
    init_db()
    app.run(host='0.0.0.0', port=5000)
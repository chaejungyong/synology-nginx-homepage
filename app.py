from flask import Flask, request, jsonify
import pymysql
import os
import time

app = Flask(__name__)

# DB 접속 설정 (시놀로지 Docker 환경)
def get_db():
    return pymysql.connect(
        host='emr-db',
        user='root',
        password='rootpassword',
        db='emr_db',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# DB 테이블 자동 생성 및 초기화
def init_db():
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
            conn.commit()
        conn.close()
        print("DB Initialization Success!")
    except Exception as e:
        print(f"DB Init Error: {e}")

# 1. READ (전체 진료기록 조회)
@app.route('/api/records', methods=['GET'])
def get_records():
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, patient_name, diagnosis, DATE_FORMAT(created_at, '%Y-%m-%d %H:%i') as created_at FROM chart_records ORDER BY id DESC")
            result = cursor.fetchall()
        conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. CREATE (새 진료기록 등록)
@app.route('/api/records', methods=['POST'])
def create_record():
    try:
        data = request.json
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO chart_records (patient_name, diagnosis) VALUES (%s, %s)",
                (data['patient_name'], data['diagnosis'])
            )
            conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. UPDATE (진료기록 수정)
@app.route('/api/records/<int:id>', methods=['PUT'])
def update_record(id):
    try:
        data = request.json
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE chart_records SET patient_name=%s, diagnosis=%s WHERE id=%s",
                (data['patient_name'], data['diagnosis'], id)
            )
            conn.commit()
        conn.close()
        return jsonify({"status": "updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 4. DELETE (진료기록 삭제)
@app.route('/api/records/<int:id>', methods=['DELETE'])
def delete_record(id):
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM chart_records WHERE id=%s", (id,))
            conn.commit()
        conn.close()
        return jsonify({"status": "deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    time.sleep(2)  # DB 컨테이너 연결 대기
    init_db()
    app.run(host='0.0.0.0', port=5000)
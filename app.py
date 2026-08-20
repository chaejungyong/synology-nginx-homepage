from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql

app = Flask(__name__)
CORS(app)  # 모든 외부 접속 허용

# MySQL DB 연결 함수
def get_db():
    return pymysql.connect(
        host='emr-db',           # docker-compose에서 지정한 DB 컨테이너 이름
        user='root',
        password='mariadbpassword',
        db='emr_db',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# [GET] 차트 데이터 조회 및 검색
@app.route('/api/charts', methods=['GET'])
def get_charts():
    search = request.args.get('search', '')
    conn = get_db()
    cursor = conn.cursor()
    
    # DB 테이블이 없을 경우 자동으로 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS charts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            pet_name VARCHAR(50) NOT NULL,
            species VARCHAR(50),
            age VARCHAR(10),
            weight VARCHAR(10),
            owner_info VARCHAR(100),
            record TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    sql = """
        SELECT * FROM charts 
        WHERE pet_name LIKE %s OR owner_info LIKE %s OR record LIKE %s 
        ORDER BY id DESC
    """
    query_str = f"%{search}%"
    cursor.execute(sql, (query_str, query_str, query_str))
    data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return jsonify(data)

# [POST] 신규 차트 저장
@app.route('/api/charts', methods=['POST'])
def add_chart():
    req = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    sql = """
        INSERT INTO charts (pet_name, species, age, weight, owner_info, record) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (
        req.get('pet_name', ''),
        req.get('species', ''),
        req.get('age', ''),
        req.get('weight', ''),
        req.get('owner_info', ''),
        req.get('record', '')
    ))
    conn.commit()
    
    cursor.close()
    conn.close()
    return jsonify({"result": "success"}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
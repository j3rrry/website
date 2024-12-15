from flask import Flask, jsonify, request, render_template, redirect
import mysql.connector

app = Flask(__name__)

# MySQL 데이터베이스 연결 설정
db_config = {
    'host': 'mysql-container',
    'user': 'testuser',
    'password': 'testpassword',
    'database': 'testdb'
}

# 루트 라우트 - HTML 반환
@app.route('/')
def index():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, title, content FROM posts")
        posts = cursor.fetchall()
        conn.close()
        return render_template('index.html', posts=posts)
    except mysql.connector.Error as err:
        return f"Error: {err}", 500

# 게시글 생성
@app.route('/posts', methods=['POST'])
def create_post():
    title = request.form['title']
    content = request.form['content']
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO posts (title, content) VALUES (%s, %s)", (title, content))
        conn.commit()
        conn.close()
        return redirect('/')  # 작성 후 메인 페이지로 리다이렉트
    except mysql.connector.Error as err:
        return f"Error: {err}", 500

# 게시글 목록 조회
@app.route('/posts', methods=['GET'])
def get_posts():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, title, content FROM posts")
        posts = cursor.fetchall()
        conn.close()
        
        return jsonify(posts), 200
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

# 게시글 단일 조회
@app.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, title, content FROM posts WHERE id = %s", (post_id,))
        post = cursor.fetchone()
        conn.close()
        if post:
            return jsonify(post), 200
        else:
            return jsonify({"error": "Post not found"}), 404
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

# 게시글 삭제
@app.route('/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))
        conn.commit()
        conn.close()
        return redirect('/')  # 삭제 후 메인 페이지로 리다이렉트
    except mysql.connector.Error as err:
        return f"Error: {err}", 500

# 게시글 수정 폼 표시
@app.route('/posts/<int:post_id>/edit', methods=['GET'])
def edit_post(post_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, title, content FROM posts WHERE id = %s", (post_id,))
        post = cursor.fetchone()
        conn.close()
        if post:
            editing_post = post
            return render_template('index.html', posts=get_all_posts(), editing_post=editing_post)
        else:
            return "게시글을 찾을 수 없습니다.", 404
    except mysql.connector.Error as err:
        return f"Error: {err}", 500

# 게시글 수정
@app.route('/edit/<int:post_id>', methods=['POST'])
def update_post(post_id):
    title = request.form['title']
    content = request.form['content']
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("UPDATE posts SET title = %s, content = %s WHERE id = %s", (title, content, post_id))
        conn.commit()
        conn.close()
        return redirect('/')
    except mysql.connector.Error as err:
        return f"Error: {err}", 500

# 모든 게시글 가져오기
def get_all_posts():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, title, content FROM posts")
        posts = cursor.fetchall()
        conn.close()
        return [post for post in posts]
    except mysql.connector.Error as err:
        return []

# 게시글 검색
@app.route('/search', methods=['GET'])
def search_posts():
    query = request.args.get('query', '')
    search_type = request.args.get('search_type', 'all')

    # SQL 쿼리 조건 설정
    if search_type == 'title':
        sql = "SELECT id, title, content FROM posts WHERE title LIKE %s"
        values = (f"%{query}%",)
    elif search_type == 'content':
        sql = "SELECT id, title, content FROM posts WHERE content LIKE %s"
        values = (f"%{query}%",)
    else:  # 전체 검색
        sql = "SELECT id, title, content FROM posts WHERE title LIKE %s OR content LIKE %s"
        values = (f"%{query}%", f"%{query}%")

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, values)
        posts = cursor.fetchall()
        conn.close()

        # 검색 결과를 렌더링
        return render_template('index.html', posts=posts, query=query, search_type=search_type)
    except mysql.connector.Error as err:
        return f"Error: {err}", 500

# 데이터베이스 연결 테스트
@app.route('/test-db')
def test_db():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES;")
        databases = cursor.fetchall()
        conn.close()
        return jsonify({"databases": [db[0] for db in databases]})
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

import os
from flask import Flask, jsonify, request, render_template, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename
import mysql.connector
import uuid
import logging

# 로그 파일 설정
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 세션에 사용
#UPLOAD_FOLDER = 'uploads'
UPLOAD_FOLDER = 'app/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#app.config['UPLOAD_FOLDER'] = os.path.abspath(UPLOAD_FOLDER)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
#app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

# MySQL 연결 설정
db_config = {
    'host': 'mysql-container',
    'user': 'testuser',
    'password': 'testpassword',
    'database': 'testdb'
}

# 회원가입
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        file = request.files['profile_image']
        filepath = None  # 파일 경로 초기화
        try:
            if file and file.filename:
                #filename = secure_filename(file.filename)
                # 난수로 파일 이름 생성
                ext = os.path.splitext(file.filename)[1]  # 파일 확장자 추출
                filename = f"{uuid.uuid4().hex}{ext}"    # 난수 기반 파일명 생성
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                #filepath = os.path.join(os.path.abspath(UPLOAD_FOLDER), filename)
                
                # 파일 저장
                file.save(filepath)
                logging.debug(f"File saved successfully: {filepath}")
            else:
                filepath = None
                logging.warning("No file provided or filename is empty.")
        except Exception as e:
            logging.error(f"File save error: {e}")
            return f"File save error: {e}", 500

        try:
            # 데이터베이스에 사용자 정보와 파일 경로 저장
            with mysql.connector.connect(**db_config) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password, name, school, profile_image) VALUES (%s, %s, %s, %s, %s)", 
                    (data['username'], data['password'], data['name'], data['school'], filename))
                conn.commit()
            return redirect('/login')
        except Exception as e:
            logging.error(f"Database error: {e}")
            return f"Database error: {e}", 500
    return render_template('register.html')

# 로그인
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            with mysql.connector.connect(**db_config) as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
                user = cursor.fetchone()
                if user:
                    session['user_id'] = user['id']
                    return redirect('/post')
                else:
                    return "로그인 실패"
        except Exception as e:
            return str(e)
    return render_template('login.html')

# 로그아웃
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')

# 내 프로필
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE id=%s", (session['user_id'],))
            user = cursor.fetchone()
            return render_template('profile.html', user=user)
    except Exception as e:
        return str(e)

# 프로필 이미지 업로드
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'user_id' not in session:
        return redirect('/login')  # 로그인하지 않은 경우 리다이렉트
    if 'file' not in request.files:
        return "파일 없음", 400
    file = request.files['file']
    if file.filename == '':
        return "파일 이름 없음", 400
    if file:
        # 난수로 파일 이름 생성
        ext = os.path.splitext(file.filename)[1]  # 파일 확장자 추출
        filename = f"{uuid.uuid4().hex}{ext}"    # 난수로 파일명 생성
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        #filepath = os.path.join(os.path.abspath(UPLOAD_FOLDER), filename)
        file.save(filepath)
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            # 현재 세션의 사용자 ID로 프로필 이미지 업데이트
            cursor.execute("UPDATE users SET profile_image = %s WHERE id = %s", 
                           (filename, session['user_id']))
            conn.commit()
        return redirect('/profile')
    except Exception as e:
        return str(e)

# 프로필 업데이트
@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect('/login')
    
    name = request.form.get('name')
    school = request.form.get('school')
    
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET name=%s, school=%s WHERE id=%s",
                (name, school, session['user_id'])
            )
            conn.commit()
        return redirect('/profile')
    except Exception as e:
        app.logger.error(f"Error updating profile: {e}")
        return "An error occurred while updating your profile. Please try again later.", 500

# 루트 경로 - 로그인 페이지
@app.route('/')
def root():
    return redirect('/login')

# 게시글 목록
@app.route('/post')
def post_page():
    if 'user_id' not in session:
        return redirect('/login')
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM posts")
            posts = cursor.fetchall()
            return render_template('index.html', posts=posts)
    except Exception as e:
        return str(e)

# 게시글 생성
@app.route('/posts', methods=['POST'])
def create_post():
    if 'user_id' not in session:
        return redirect('/login')
    title = request.form['title']
    content = request.form['content']
    password = request.form.get('password')  # 비밀번호 입력값 가져오기
    file = request.files['file_path']
    secret = password if password else None

    filepath = None  # 파일 경로 초기화
    filename = None  # 초기화
    try:
        if file and file.filename:
            #filename = secure_filename(file.filename)
            # 난수로 파일 이름 생성
            ext = os.path.splitext(file.filename)[1]  # 파일 확장자 추출
            filename = f"{uuid.uuid4().hex}{ext}"    # 난수 기반 파일명 생성
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            #filepath = os.path.join(os.path.abspath(UPLOAD_FOLDER), filename)
            
            # 파일 저장
            file.save(filepath)
            logging.debug(f"File saved successfully: {filepath}")
        else:
            filepath = None
            logging.warning("No file provided or filename is empty.")
    except Exception as e:
        logging.error(f"File save error: {e}")
        return f"File save error: {e}", 500

    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO posts (title, content, secret, file_path) VALUES (%s, %s, %s, %s)", (title, content, secret, filename))
            conn.commit()
        return redirect('/post')
    except Exception as e:
        return str(e)

# 게시글 삭제
@app.route('/posts/<int:post_id>/delete')
def delete_post(post_id):
    if 'user_id' not in session:
        return redirect('/login')
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM posts WHERE id=%s", (post_id,))
            conn.commit()
        return redirect('/post')
    except Exception as e:
        return str(e)

# 게시글 수정
@app.route('/posts/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'user_id' not in session:
        return redirect('/login')
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor(dictionary=True)
            if request.method == 'POST':
                title = request.form['title']
                content = request.form['content']
                secret = 'secret' in request.form
                cursor.execute("UPDATE posts SET title=%s, content=%s, secret=%s WHERE id=%s", 
                               (title, content, secret, post_id))
                conn.commit()
                return redirect('/post')
            else:
                cursor.execute("SELECT * FROM posts WHERE id=%s", (post_id,))
                post = cursor.fetchone()
                return render_template('edit_post.html', post=post)
    except Exception as e:
        return str(e)

# 게시글 검색
@app.route('/search', methods=['GET'])
def search():
    if 'user_id' not in session:
        return redirect('/login')
    query = request.args.get('query', '')
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM posts WHERE title LIKE %s OR content LIKE %s", (f"%{query}%", f"%{query}%"))
            posts = cursor.fetchall()
            return render_template('index.html', posts=posts)
    except Exception as e:
        return str(e)

# 게시글 상세 조회
@app.route('/posts/<int:post_id>', methods=['GET', 'POST'])
def view_post(post_id):
    if request.method == 'POST':
        password = request.form.get('password')

        try:
            with mysql.connector.connect(**db_config) as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM posts WHERE id=%s", (post_id,))
                post = cursor.fetchone()

                if not post:
                    return "게시글을 찾을 수 없습니다.", 404

                # 비밀글인지 확인
                if post['secret']:
                    if post['secret'] == password:
                        return render_template('edit_post.html', post=post)
                    else:
                        return "비밀번호가 일치하지 않습니다.", 403
                else:
                    return render_template('edit_post.html', post=post)
        except Exception as e:
            return str(e)
    else:
        # GET 요청 시 비밀번호 입력 폼 표시
        try:
            with mysql.connector.connect(**db_config) as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM posts WHERE id=%s", (post_id,))
                post = cursor.fetchone()

                if not post:
                    return "게시글을 찾을 수 없습니다.", 404

                if post['secret']:
                    return render_template('enter_secret.html', post=post)
                else:
                    return render_template('edit_post.html', post=post)
        except Exception as e:
            return str(e)

# 업로드된 파일을 제공하는 엔드포인트
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

@app.route('/find-username', methods=['GET', 'POST'])
def find_username():
    if request.method == 'POST':
        name = request.form['name']
        school = request.form['school']
        try:
            with mysql.connector.connect(**db_config) as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT username FROM users WHERE name=%s AND school=%s", (name, school))
                user = cursor.fetchone()
                if user:
                    return f"당신의 아이디는: {user['username']}"
                else:
                    return "일치하는 사용자가 없습니다."
        except Exception as e:
            return str(e)
    return render_template('find_username.html')

@app.route('/find-password', methods=['GET', 'POST'])
def find_password():
    if request.method == 'POST':
        username = request.form['username']
        school = request.form['school']
        try:
            with mysql.connector.connect(**db_config) as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT password FROM users WHERE username=%s AND school=%s", (username, school))
                user = cursor.fetchone()
                if user:
                    return f"당신의 비밀번호는: {user['password']}"
                else:
                    return "일치하는 사용자가 없습니다."
        except Exception as e:
            return str(e)
    return render_template('find_password.html')

# 회원 단일 목록
@app.route('/profile/<int:user_id>')
def view_user_profile(user_id):
    if 'user_id' not in session:
        return redirect('/login')
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT username, name, school, profile_image FROM users WHERE id=%s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return "User not found", 404
            return render_template('view_profile.html', user=user)
    except Exception as e:
        return str(e), 500

# 회원 목록
@app.route('/members')
def member_list():
    if 'user_id' not in session:
        return redirect('/login')
    try:
        with mysql.connector.connect(**db_config) as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, username, name FROM users")
            users = cursor.fetchall()
            return render_template('members.html', users=users)
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

import os
from flask import Flask, render_template, request

app = Flask(__name__)

# 게시글 ID 카운터 (초기값)
post_counter = 1

# 메인 페이지
@app.route('/')
def hello():
    global post_counter

    # 게시글 목록을 읽어와서 표시
    posts = []
    for filename in os.listdir('templates/post'):
        if filename.endswith('.html') and filename not in ['index.html', 'create.html']:
            post_id = filename.split('.')[0]
            posts.append(int(post_id))
    posts.sort(reverse=True)  # 최신 글부터 표시
    post_counter = len(posts) + 1
    return render_template('index.html', posts=posts)

# 게시글 작성
@app.route('/create', methods=['GET', 'POST'])
def create():
    global post_counter

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        # 동적 HTML 파일 생성
        file_name = f'templates/post/{post_counter}.html'
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(f"""
            <html>
            <head>
                <title>{post_counter}</title>
            </head>
            <body>
                <h1>{title}</h1>
                <p>{content}</p>
                <a href="/">back</a>
            </body>
            </html>
            """)

        post_counter += 1  # 다음 게시글 ID 증가

        # 메인 페이지를 직접 렌더링하여 반환
        posts = []
        for filename in os.listdir('templates/post/'):
            if filename.endswith('.html') and filename not in ['index.html', 'create.html']:
                post_id = filename.split('.')[0]
                posts.append(int(post_id))
        posts.sort(reverse=True)  # 최신 글부터 표시
        return render_template('index.html', posts=posts)  # 성공 메시지 페이지 렌더링

    return render_template('create.html')


# 게시글 상세보기
@app.route('/post/<int:post_id>')
def detail(post_id):
    return render_template(f'post/{post_id}.html')

if __name__ == '__main__':
    app.run()

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    school VARCHAR(255),
    profile_image VARCHAR(255)  -- 프로필 이미지 컬럼 추가
);

CREATE TABLE IF NOT EXISTS posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    secret VARCHAR(255) DEFAULT FALSE,
    file_path VARCHAR(255)
);

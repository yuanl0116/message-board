# 云端部署指南

本文档详细说明如何将Flask留言板应用从本地开发环境部署到云服务器。

## 1. 数据库一致性配置

### 环境变量配置

应用已经支持通过环境变量进行配置，确保开发和生产环境的一致性：

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env
```

### 数据库迁移策略

#### 本地开发（SQLite）
```bash
# 本地使用SQLite，无需额外配置
DATABASE_URL=sqlite:///messageboard.db
```

#### 生产环境（MySQL）
```bash
# 腾讯云MySQL配置示例
DATABASE_URL=mysql+pymysql://username:password@host:port/database_name
```

### Flask-SQLAlchemy最佳实践

1. **使用环境变量**：避免硬编码数据库连接信息
2. **数据库迁移**：使用Flask-Migrate管理数据库版本
3. **连接池配置**：生产环境配置合适的连接池大小

## 2. 推荐部署方案

### 方案一：腾讯云轻量应用服务器 + Docker（推荐）

#### 优势
- 环境一致性
- 易于扩展
- 简单的CI/CD

#### 部署步骤

1. **创建Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

2. **创建docker-compose.yml**
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "80:5000"
    environment:
      - DATABASE_URL=mysql+pymysql://root:password@db:3306/messageboard
      - FLASK_DEBUG=False
      - SECRET_KEY=your-production-secret-key
    depends_on:
      - db
  
  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=messageboard
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

3. **安装Docker（使用国内镜像源）**
```bash
# 安装必要的包
apt install apt-transport-https ca-certificates curl gnupg lsb-release -y

# 使用腾讯云镜像源安装Docker
# 添加腾讯云Docker GPG密钥
curl -fsSL https://mirrors.cloud.tencent.com/docker-ce/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加腾讯云Docker仓库
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://mirrors.cloud.tencent.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# 更新包索引并安装Docker
apt update
apt install docker-ce docker-ce-cli containerd.io -y

# 配置Docker镜像加速器（使用腾讯云镜像）
mkdir -p /etc/docker
tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
EOF

# 启动Docker服务
systemctl daemon-reload
systemctl start docker
systemctl enable docker
```

4. **安装Docker Compose（使用国内镜像源）**
```bash
# 方法一：使用国内镜像下载（推荐）
curl -L "https://get.daocloud.io/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 方法二：如果上述方法失败，使用pip安装
apt install python3-pip -y
pip3 install docker-compose -i https://pypi.tuna.tsinghua.edu.cn/simple
```

5. **验证安装**
```bash
docker --version
docker-compose --version

# 测试Docker是否正常工作
docker run hello-world
```

6. **部署命令**
```bash
# 在服务器上
git clone your-repo
cd your-project
docker-compose up -d
```

### 方案二：腾讯云服务器 + Nginx + Gunicorn

#### 部署步骤

1. **安装依赖**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和必要工具
sudo apt install python3 python3-pip python3-venv nginx mysql-server -y
```

2. **配置应用**
```bash
# 克隆代码
git clone your-repo
cd your-project

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install gunicorn
```

3. **配置环境变量**
```bash
# 创建生产环境配置
cp .env.example .env
vim .env
```

4. **配置Gunicorn**
```bash
# 创建gunicorn配置文件
vim gunicorn.conf.py
```

```python
# gunicorn.conf.py
bind = "127.0.0.1:5000"
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

5. **配置Nginx**
```nginx
# /etc/nginx/sites-available/messageboard
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/your/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

6. **配置系统服务**
```bash
# 创建systemd服务文件
sudo vim /etc/systemd/system/messageboard.service
```

```ini
[Unit]
Description=Messageboard Flask App
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/messageboard
Environment="PATH=/home/ubuntu/messageboard/venv/bin"
ExecStart=/home/ubuntu/messageboard/venv/bin/gunicorn -c gunicorn.conf.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

7. **启动服务**
```bash
# 启用并启动服务
sudo systemctl enable messageboard
sudo systemctl start messageboard
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 方案三：腾讯云Serverless（适合小流量）

使用腾讯云SCF（云函数）+ API Gateway + CDB（云数据库）

#### 优势
- 按需付费
- 自动扩缩容
- 无需管理服务器

#### 部署步骤
1. 安装Serverless Framework
2. 配置serverless.yml
3. 部署到云函数

## 3. 数据库配置最佳实践

### 环境变量管理

```python
# 推荐的配置方式
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///messageboard.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///messageboard.db'

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
```

### 数据库迁移

```bash
# 安装Flask-Migrate
pip install Flask-Migrate

# 初始化迁移
flask db init

# 创建迁移
flask db migrate -m "Initial migration"

# 应用迁移
flask db upgrade
```

## 4. 安全配置

### 生产环境检查清单

- [ ] 设置强密码的SECRET_KEY
- [ ] 关闭DEBUG模式
- [ ] 配置HTTPS
- [ ] 设置防火墙规则
- [ ] 配置数据库访问权限
- [ ] 定期备份数据库
- [ ] 配置日志记录
- [ ] 设置监控和告警

### 环境变量安全

```bash
# 生产环境配置示例
export FLASK_DEBUG=False
export SECRET_KEY="your-very-secure-secret-key"
export DATABASE_URL="mysql+pymysql://user:password@host:port/db"
```

## 5. 监控和维护

### 日志配置

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/messageboard.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

### 性能优化

1. **数据库连接池**
2. **Redis缓存**
3. **CDN加速静态资源**
4. **Gzip压缩**

## 6. 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查DATABASE_URL格式
   - 确认数据库服务运行状态
   - 验证网络连接

2. **静态文件404**
   - 配置Nginx静态文件路径
   - 检查文件权限

3. **CORS错误**
   - 确认Flask-CORS配置
   - 检查前端API地址

### 调试命令

```bash
# 检查服务状态
sudo systemctl status messageboard
sudo systemctl status nginx

# 查看日志
sudo journalctl -u messageboard -f
sudo tail -f /var/log/nginx/error.log

# 测试数据库连接
python -c "from app import db; print(db.engine.execute('SELECT 1').scalar())"
```

## 总结

推荐使用**方案一（Docker部署）**，因为它提供了最好的环境一致性和可维护性。对于小型应用，腾讯云轻量应用服务器已经足够，成本低且易于管理。

关键要点：
1. 使用环境变量管理配置
2. 本地SQLite，生产MySQL
3. 容器化部署
4. 配置反向代理
5. 定期备份和监控
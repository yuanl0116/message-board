# 在线留言板后端 API

这是一个使用 Flask 和 MySQL 构建的简单在线留言板后端应用。

## 功能特性

- 添加留言：通过 POST 请求提交新留言
- 获取留言：通过 GET 请求获取所有留言（按时间倒序）
- JSON 格式数据交互
- MySQL 数据库存储

## 安装依赖

在 macOS 上安装所需依赖：

```bash
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install flask flask-sqlalchemy pymysql
```

## 数据库配置

1. 确保 MySQL 服务已启动
2. 创建数据库：
   ```sql
   CREATE DATABASE messageboard;
   ```
3. 修改 `app.py` 中的数据库连接字符串：
   ```python
   app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://用户名:密码@localhost:3306/messageboard'
   ```

## 运行应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

## API 接口

### 1. 添加留言

- **URL**: `/add`
- **方法**: POST
- **请求格式**: JSON
- **参数**:
  ```json
  {
    "message": "这是一条留言"
  }
  ```
- **响应示例**:
  ```json
  {
    "success": true,
    "message": "留言添加成功",
    "data": {
      "id": 1,
      "content": "这是一条留言",
      "timestamp": "2024-01-01 12:00:00"
    }
  }
  ```

### 2. 获取留言

- **URL**: `/get`
- **方法**: GET
- **响应示例**:
  ```json
  {
    "success": true,
    "count": 2,
    "data": [
      {
        "id": 2,
        "content": "最新的留言",
        "timestamp": "2024-01-01 12:30:00"
      },
      {
        "id": 1,
        "content": "较早的留言",
        "timestamp": "2024-01-01 12:00:00"
      }
    ]
  }
  ```

### 3. 健康检查

- **URL**: `/health`
- **方法**: GET
- **响应示例**:
  ```json
  {
    "status": "healthy",
    "message": "留言板服务运行正常"
  }
  ```

## 测试示例

使用 curl 测试 API：

```bash
# 添加留言
curl -X POST http://localhost:5000/add \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, World!"}'

# 获取所有留言
curl http://localhost:5000/get

# 健康检查
curl http://localhost:5000/health
```

## 数据库表结构

`messages` 表包含以下字段：

- `id`: 主键，自增整数
- `content`: 留言内容，文本类型
- `timestamp`: 创建时间，日期时间类型

## 注意事项

1. 请确保 MySQL 服务正在运行
2. 根据实际情况修改数据库连接配置
3. 生产环境中请关闭 debug 模式
4. 建议为数据库用户设置适当的权限
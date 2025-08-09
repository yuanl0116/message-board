# 在macOS上安装所需依赖的pip指令：
# pip install flask flask-sqlalchemy pymysql

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime

# 创建Flask应用实例
app = Flask(__name__)

# 启用CORS支持，允许前端跨域访问
CORS(app)

# 数据库配置
# 为了测试方便，使用SQLite数据库（生产环境可改为MySQL）
# MySQL配置示例：mysql+pymysql://用户名:密码@主机地址:端口/数据库名
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///messageboard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 定义Message数据模型
class Message(db.Model):
    """留言数据模型"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 主键，自增
    content = db.Column(db.Text, nullable=False)  # 留言内容，不能为空
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # 时间戳，默认当前时间
    
    def to_dict(self):
        """将模型对象转换为字典格式，便于JSON序列化"""
        return {
            'id': self.id,
            'content': self.content,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }

# API接口：添加留言
@app.route('/add', methods=['POST'])
def add_message():
    """接收用户提交的留言"""
    try:
        # 获取请求中的message参数
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': '缺少message参数'}), 400
        
        message_content = data['message']
        if not message_content.strip():
            return jsonify({'error': '留言内容不能为空'}), 400
        
        # 创建新的留言记录
        new_message = Message(content=message_content)
        db.session.add(new_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '留言添加成功',
            'data': new_message.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'添加留言失败: {str(e)}'}), 500

# API接口：获取所有留言
@app.route('/get', methods=['GET'])
def get_messages():
    """获取所有已保存的留言，按时间倒序返回"""
    try:
        # 查询所有留言，按时间戳倒序排列
        messages = Message.query.order_by(Message.timestamp.desc()).all()
        
        # 将查询结果转换为字典列表
        messages_list = [message.to_dict() for message in messages]
        
        return jsonify({
            'success': True,
            'count': len(messages_list),
            'data': messages_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'获取留言失败: {str(e)}'}), 500

# 健康检查接口
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({'status': 'healthy', 'message': '留言板服务运行正常'}), 200

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '接口不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    # 创建数据库表（如果不存在）
    with app.app_context():
        db.create_all()
    
    # 启动Flask应用
    app.run(debug=True, host='0.0.0.0', port=5001)

# 初始化数据库的命令：
# 1. 首先确保MySQL服务已启动
# 2. 在MySQL中创建数据库：CREATE DATABASE messageboard;
# 3. 运行Python应用：python app.py
# 4. 或者在Python交互式环境中执行：
#    from app import app, db
#    with app.app_context():
#        db.create_all()
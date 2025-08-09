#!/bin/bash

# Flask留言板应用部署脚本
# 使用方法：./deploy.sh [development|production]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查参数
ENV=${1:-development}

if [[ "$ENV" != "development" && "$ENV" != "production" ]]; then
    print_error "无效的环境参数。使用: $0 [development|production]"
    exit 1
fi

print_info "开始部署到 $ENV 环境..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    print_error "Docker未安装。请先安装Docker。"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose未安装。请先安装Docker Compose。"
    exit 1
fi

# 检查环境变量文件
if [[ "$ENV" == "production" ]]; then
    if [[ ! -f ".env" ]]; then
        print_warning "生产环境需要.env文件"
        if [[ -f ".env.production" ]]; then
            print_info "复制.env.production模板到.env"
            cp .env.production .env
            print_warning "请编辑.env文件并设置正确的生产环境配置"
            print_warning "特别注意修改以下配置："
            echo "  - SECRET_KEY"
            echo "  - MYSQL_ROOT_PASSWORD"
            echo "  - MYSQL_PASSWORD"
            read -p "配置完成后按Enter继续..."
        else
            print_error "找不到.env.production模板文件"
            exit 1
        fi
    fi
else
    # 开发环境使用示例配置
    if [[ ! -f ".env" ]]; then
        print_info "复制开发环境配置"
        cp .env.example .env
    fi
fi

# 创建必要的目录
print_info "创建必要的目录..."
mkdir -p logs

# 停止现有容器
print_info "停止现有容器..."
docker-compose down 2>/dev/null || true

# 构建和启动服务
if [[ "$ENV" == "production" ]]; then
    print_info "构建生产环境镜像..."
    docker-compose build --no-cache
    
    print_info "启动生产环境服务..."
    docker-compose up -d
else
    print_info "启动开发环境服务..."
    # 开发环境可以使用不同的compose文件
    docker-compose up -d
fi

# 等待服务启动
print_info "等待服务启动..."
sleep 10

# 检查服务状态
print_info "检查服务状态..."
docker-compose ps

# 健康检查
print_info "执行健康检查..."
for i in {1..30}; do
    if curl -f http://localhost/health >/dev/null 2>&1; then
        print_info "应用启动成功！"
        break
    fi
    if [[ $i -eq 30 ]]; then
        print_error "应用启动失败，请检查日志"
        docker-compose logs
        exit 1
    fi
    sleep 2
done

# 显示访问信息
print_info "部署完成！"
echo ""
echo "访问地址："
echo "  - 应用: http://localhost"
echo "  - 健康检查: http://localhost/health"
echo ""
echo "管理命令："
echo "  - 查看日志: docker-compose logs -f"
echo "  - 停止服务: docker-compose down"
echo "  - 重启服务: docker-compose restart"
echo "  - 查看状态: docker-compose ps"
echo ""

if [[ "$ENV" == "production" ]]; then
    print_warning "生产环境部署完成，请确保："
    echo "  1. 配置了正确的域名和SSL证书"
    echo "  2. 设置了防火墙规则"
    echo "  3. 配置了备份策略"
    echo "  4. 设置了监控和告警"
fi
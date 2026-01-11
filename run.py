#!/usr/bin/env python3
"""
数据文件管理系统启动脚本
"""
import uvicorn
import os
import sys

def main():
    # 确保当前目录在Python路径中
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    # 导入后端主模块
    from backend.main import app
    
    print("正在启动数据文件管理系统...")
    print("访问地址: http://localhost:8000")
    print("按 Ctrl+C 停止服务")
    
    # 启动服务（生产环境不需要reload）
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
# 数据文件管理系统

一个基于 FastAPI 的数据文件管理与浏览网站，支持 CSV、JSONL、JSON 格式文件的上传、展示和交互式浏览。

## 功能特性

- 📁 支持多种数据格式：CSV、JSONL、JSON
- 🔍 实时搜索和过滤功能
- 📊 交互式表格展示
- 🎯 字段筛选和正则表达式过滤
- 📄 单条记录详情查看
- 📱 响应式设计，支持移动端

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动服务

```bash
python run.py
```

服务启动后，访问 http://localhost:8000

## API 接口

### 文件上传
- **POST** `/api/upload` - 上传数据文件

### 数据查询
- **GET** `/api/project/{project_id}/data` - 获取项目数据（支持分页、字段筛选、过滤）
- **GET** `/api/projects` - 获取项目列表

## 支持的文件格式

### CSV 格式
```csv
name,age,city
张三,25,北京
李四,30,上海
```

### JSONL 格式
```jsonl
{"name": "张三", "age": 25, "city": "北京"}
{"name": "李四", "age": 30, "city": "上海"}
```

### JSON 格式
**行式格式（推荐）：**
```json
{
  "data": [
    {"name": "张三", "age": 25, "city": "北京"},
    {"name": "李四", "age": 30, "city": "上海"}
  ]
}
```

**列式格式：**
```json
{
  "name": ["张三", "李四"],
  "age": [25, 30],
  "city": ["北京", "上海"]
}
```

## 项目结构

```
data_analysis/
├── backend/           # 后端代码
│   └── main.py       # FastAPI 主应用
├── templates/        # HTML 模板
│   ├── base.html     # 基础模板
│   ├── index.html    # 首页
│   ├── upload.html   # 上传页面
│   ├── project.html  # 项目详情页
│   └── record.html   # 记录详情页
├── static/           # 静态文件
│   └── uploads/      # 上传文件存储
├── data/             # 数据存储
├── requirements.txt  # 依赖列表
└── run.py           # 启动脚本
```

## 使用说明

1. 启动服务后，访问首页查看已上传的数据项目
2. 点击"上传数据"按钮上传新的数据文件
3. 在项目列表中点击"查看详情"进入数据表格页面
4. 使用字段选择器控制显示的字段
5. 在表头输入框中使用正则表达式过滤数据
6. 点击序号查看单条记录的详细信息
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import os
import json
import pandas as pd
import uuid
import re
from typing import Optional, List, Dict, Any
from pathlib import Path
import aiofiles

app = FastAPI(title="数据文件管理系统")

# 静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 数据存储目录
UPLOAD_DIR = Path("static/uploads")
DATA_DIR = Path("data")
UPLOAD_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# 存储项目元数据
PROJECTS_FILE = DATA_DIR / "projects.json"


def load_projects():
    """加载所有项目元数据"""
    if PROJECTS_FILE.exists():
        with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_projects(projects):
    """保存项目元数据"""
    with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(projects, f, ensure_ascii=False, indent=2)


def load_project_data(project_id: str) -> Dict[str, Any]:
    """加载特定项目的数据"""
    project_file = DATA_DIR / f"{project_id}.json"
    if project_file.exists():
        with open(project_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_project_data(project_id: str, data: Dict[str, Any]):
    """保存项目数据"""
    project_file = DATA_DIR / f"{project_id}.json"
    with open(project_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_uploaded_file(file_path: str, file_type: str) -> List[Dict[str, Any]]:
    """解析上传的文件"""
    if file_type == "csv":
        df = pd.read_csv(file_path)
        return df.to_dict('records')
    elif file_type == "jsonl":
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    data.append(json.loads(line))
        return data
    elif file_type == "json":
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        # 支持两种格式：
        # 1. 行式格式：{"data": [{"name": "张三", "age": 25}, ...]}
        # 2. 列式格式：{"name": ["张三", "李四"], "age": [25, 30], ...}

        if isinstance(json_data, list):
            return json_data
        elif isinstance(json_data, dict):
            # 检查是否是行式格式（包含data字段）
            if "data" in json_data and isinstance(json_data["data"], list):
                return json_data["data"]

            # 检查是否是列式格式（所有值都是数组且长度相同）
            array_values = []
            array_length = None

            for key, value in json_data.items():
                if isinstance(value, list):
                    if array_length is None:
                        array_length = len(value)
                    elif len(value) != array_length:
                        raise ValueError("JSON文件中数组长度不一致")
                    array_values.append((key, value))

            if array_values:
                # 转换列式格式为行式格式
                result = []
                for i in range(array_length):
                    row = {}
                    for key, value in array_values:
                        row[key] = value[i]
                    result.append(row)
                return result

            # 如果不是列式格式，尝试寻找第一个数组字段
            for key, value in json_data.items():
                if isinstance(value, list):
                    return value

        raise ValueError("JSON文件格式不支持，请使用行式格式 {\"data\": [...]} 或列式格式 {\"field1\": [...], \"field2\": [...]}")
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """首页 - 项目列表"""
    projects = load_projects()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "projects": projects
    })


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """上传页面"""
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/api/upload")
async def upload_file(
        file: UploadFile = File(...),
        description: str = Form(...)
):
    """文件上传API"""
    try:
        # 检查文件类型
        file_type = None
        if file.filename.endswith('.csv'):
            file_type = 'csv'
        elif file.filename.endswith('.jsonl'):
            file_type = 'jsonl'
        elif file.filename.endswith('.json'):
            file_type = 'json'
        else:
            raise HTTPException(status_code=400, detail="不支持的文件类型")

        # 生成项目ID
        project_id = str(uuid.uuid4())

        # 保存文件
        file_extension = file.filename.split('.')[-1]
        file_path = UPLOAD_DIR / f"{project_id}.{file_extension}"

        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # 解析数据
        data = parse_uploaded_file(str(file_path), file_type)

        # 保存项目元数据
        projects = load_projects()
        new_project = {
            "id": project_id,
            "filename": file.filename,
            "description": description,
            "file_type": file_type,
            "record_count": len(data),
            "created_at": str(pd.Timestamp.now())
        }
        projects.append(new_project)
        save_projects(projects)

        # 保存数据
        save_project_data(project_id, {
            "data": data,
            "columns": list(data[0].keys()) if data else []
        })

        return {"success": True, "project_id": project_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/project/{project_id}", response_class=HTMLResponse)
async def project_detail(request: Request, project_id: str):
    """项目详情页"""
    projects = load_projects()
    project = next((p for p in projects if p["id"] == project_id), None)

    if not project:
        raise HTTPException(status_code=404, detail="项目未找到")

    project_data = load_project_data(project_id)

    return templates.TemplateResponse("project.html", {
        "request": request,
        "project": project,
        "project_data": project_data
    })


@app.get("/project/{project_id}/record/{record_index}", response_class=HTMLResponse)
async def record_detail(
        request: Request,
        project_id: str,
        record_index: int,
        fields: Optional[str] = None
):
    """单条记录详情页"""
    projects = load_projects()
    project = next((p for p in projects if p["id"] == project_id), None)

    if not project:
        raise HTTPException(status_code=404, detail="项目未找到")

    project_data = load_project_data(project_id)
    data = project_data.get("data", [])

    if record_index < 0 or record_index >= len(data):
        raise HTTPException(status_code=404, detail="记录未找到")

    record = data[record_index]

    # 获取所有可用字段
    all_fields = list(record.keys())

    # 处理字段筛选
    selected_fields = all_fields  # 默认显示所有字段
    if fields:
        requested_fields = fields.split(',')
        # 只选择存在的字段
        selected_fields = [field for field in requested_fields if field in all_fields]

    # 尝试解析JSON字段
    processed_record = {}
    for key, value in record.items():
        if key in selected_fields:  # 只处理选定的字段
            if isinstance(value, (dict, list)):
                # 直接是字典或列表类型，格式化为JSON字符串
                processed_record[key] = json.dumps(value, ensure_ascii=False, indent=2)
            elif isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, (dict, list)):
                        processed_record[key] = json.dumps(parsed, ensure_ascii=False, indent=2)
                    else:
                        processed_record[key] = value
                except:
                    processed_record[key] = value
            else:
                processed_record[key] = value

    return templates.TemplateResponse("record.html", {
        "request": request,
        "project": project,
        "record": processed_record,
        "record_index": record_index,
        "all_fields": all_fields,
        "selected_fields": selected_fields,
        "current_fields": fields  # 传递当前的字段筛选参数
    })


@app.get("/api/project/{project_id}/data")
async def get_project_data(
        project_id: str,
        page: int = 1,
        per_page: int = 50,
        fields: Optional[str] = None,
        filters: Optional[str] = None
):
    """获取项目数据API"""
    try:
        project_data = load_project_data(project_id)
        data = project_data.get("data", [])

        # 字段过滤
        if fields:
            selected_fields = fields.split(',')
            data = [{field: record.get(field) for field in selected_fields if field in record}
                    for record in data]

        # 正则表达式过滤
        if filters:
            filter_rules = json.loads(filters) if filters else {}
            filtered_data = []

            for record in data:
                match = True
                for field, pattern in filter_rules.items():
                    if field in record and record[field] is not None:
                        try:
                            if not re.search(pattern, str(record[field]), re.IGNORECASE):
                                match = False
                                break
                        except re.error:
                            match = False
                            break
                    else:
                        match = False
                        break

                if match:
                    filtered_data.append(record)

            data = filtered_data

        # 分页
        total = len(data)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_data = data[start:end]

        return {
            "data": paginated_data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects")
async def get_projects(search: Optional[str] = None):
    """获取项目列表API"""
    projects = load_projects()

    if search:
        projects = [p for p in projects if
                    search.lower() in p["filename"].lower() or
                    search.lower() in p["description"].lower()]

    return {"projects": projects}


@app.delete("/api/project/{project_id}")
async def delete_project(project_id: str):
    """删除项目API"""
    try:
        # 加载项目列表
        projects = load_projects()
        project = next((p for p in projects if p["id"] == project_id), None)

        if not project:
            raise HTTPException(status_code=404, detail="项目未找到")

        # 删除项目数据文件
        project_data_file = DATA_DIR / f"{project_id}.json"
        if project_data_file.exists():
            project_data_file.unlink()

        # 删除原始上传文件
        project_file = UPLOAD_DIR / f"{project_id}.{project['file_type']}"
        if project_file.exists():
            project_file.unlink()

        # 从项目列表中移除
        projects = [p for p in projects if p["id"] != project_id]
        save_projects(projects)

        return {"success": True, "message": "项目删除成功"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
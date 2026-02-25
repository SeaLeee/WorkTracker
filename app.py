"""
工作需求记录管理系统 - Flask 后端
"""
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

app = Flask(__name__, static_folder='static')
CORS(app)

# 数据存储目录
DATA_DIR = Path(__file__).parent / 'data'
DATA_DIR.mkdir(exist_ok=True)

# Markdown 文件路径
REQUIREMENTS_FILE = DATA_DIR / 'requirements.md'
DAILY_DIR = DATA_DIR / 'daily'
MONTHLY_DIR = DATA_DIR / 'monthly'
GLOBAL_NOTES_FILE = DATA_DIR / 'global_notes.md'

DAILY_DIR.mkdir(exist_ok=True)
MONTHLY_DIR.mkdir(exist_ok=True)

# 优先级和状态定义
PRIORITIES = ['高', '中', '低']
STATUSES = ['待处理', '进行中', '已完成', '已取消']


def init_requirements_file():
    """初始化需求列表文件"""
    if not REQUIREMENTS_FILE.exists():
        content = """# 工作需求列表

## 需求记录

<!-- 需求格式: [状态] 优先级 | [分类] 需求描述 | 创建日期 | 处理时间段 | 预计完成日期 | 实际完成日期 | ID -->

"""
        REQUIREMENTS_FILE.write_text(content, encoding='utf-8')


def init_global_notes_file():
    """初始化全局注意文件"""
    if not GLOBAL_NOTES_FILE.exists():
        content = """# 全局注意事项

<!-- 这里的内容会显示在每天的今日任务页面 -->

"""
        GLOBAL_NOTES_FILE.write_text(content, encoding='utf-8')


def parse_requirements():
    """解析需求列表 Markdown 文件"""
    init_requirements_file()
    content = REQUIREMENTS_FILE.read_text(encoding='utf-8')
    requirements = []
    
    # 匹配需求行（新格式包含父标题和处理时间段）
    # 格式: - [x] **高** | [分类] 描述 | 创建:2026-02-25 | 处理:2026-02-20~2026-02-28 | 预计:2026-02-28 | 完成:未完成 | ID:abc123
    pattern = r'- \[([ x])\] \*\*(\S+)\*\* \| \[(.+?)\] (.+?) \| 创建:(\d{4}-\d{2}-\d{2}) \| 处理:(\d{4}-\d{2}-\d{2}~\d{4}-\d{2}-\d{2}|待定) \| 预计:(\d{4}-\d{2}-\d{2}|待定) \| 完成:(\d{4}-\d{2}-\d{2}|未完成|已取消) \| ID:(\w+)'
    
    # 兼容旧格式（没有处理时间段）
    old_pattern = r'- \[([ x])\] \*\*(\S+)\*\* \| \[(.+?)\] (.+?) \| 创建:(\d{4}-\d{2}-\d{2}) \| 预计:(\d{4}-\d{2}-\d{2}|待定) \| 完成:(\d{4}-\d{2}-\d{2}|未完成|已取消) \| ID:(\w+)'
    
    for match in re.finditer(pattern, content):
        completed = match.group(1) == 'x'
        priority = match.group(2)
        category = match.group(3)
        description = match.group(4)
        created_date = match.group(5)
        work_period = match.group(6)
        due_date = match.group(7)
        completed_date = match.group(8)
        req_id = match.group(9)
        
        # 解析处理时间段
        work_start = ''
        work_end = ''
        if work_period != '待定' and '~' in work_period:
            parts = work_period.split('~')
            work_start = parts[0]
            work_end = parts[1]
        
        # 根据完成状态确定状态
        if completed:
            status = '已完成'
        elif completed_date == '已取消':
            status = '已取消'
        elif completed_date == '未完成' and due_date != '待定':
            status = '进行中'
        else:
            status = '待处理'
        
        requirements.append({
            'id': req_id,
            'category': category,
            'description': description,
            'priority': priority,
            'status': status,
            'created_date': created_date,
            'work_start': work_start,
            'work_end': work_end,
            'due_date': due_date,
            'completed_date': completed_date,
            'completed': completed
        })
    
    # 处理旧格式数据
    matched_ids = [r['id'] for r in requirements]
    for match in re.finditer(old_pattern, content):
        req_id = match.group(8)
        if req_id in matched_ids:
            continue
            
        completed = match.group(1) == 'x'
        priority = match.group(2)
        category = match.group(3)
        description = match.group(4)
        created_date = match.group(5)
        due_date = match.group(6)
        completed_date = match.group(7)
        
        if completed:
            status = '已完成'
        elif completed_date == '已取消':
            status = '已取消'
        elif completed_date == '未完成' and due_date != '待定':
            status = '进行中'
        else:
            status = '待处理'
        
        requirements.append({
            'id': req_id,
            'category': category,
            'description': description,
            'priority': priority,
            'status': status,
            'created_date': created_date,
            'work_start': '',
            'work_end': '',
            'due_date': due_date,
            'completed_date': completed_date,
            'completed': completed
        })
    
    return requirements


def save_requirements(requirements):
    """保存需求列表到 Markdown 文件"""
    content = """# 工作需求列表

## 需求记录

<!-- 需求格式: [状态] 优先级 | [分类] 需求描述 | 创建日期 | 处理时间段 | 预计完成日期 | 实际完成日期 | ID -->

"""
    for req in requirements:
        checkbox = 'x' if req.get('completed', False) or req.get('status') == '已完成' else ' '
        category = req.get('category', '默认分类')
        
        # 处理时间段
        work_start = req.get('work_start', '')
        work_end = req.get('work_end', '')
        if work_start and work_end:
            work_period = f"{work_start}~{work_end}"
        else:
            work_period = '待定'
        
        line = f"- [{checkbox}] **{req['priority']}** | [{category}] {req['description']} | 创建:{req['created_date']} | 处理:{work_period} | 预计:{req['due_date']} | 完成:{req['completed_date']} | ID:{req['id']}\n"
        content += line
    
    REQUIREMENTS_FILE.write_text(content, encoding='utf-8')


def parse_global_notes():
    """解析全局注意事项"""
    init_global_notes_file()
    content = GLOBAL_NOTES_FILE.read_text(encoding='utf-8')
    
    notes = []
    # 匹配注意事项行
    pattern = r'- \[(.+?)\] (.+?) \| ID:(\w+)'
    for match in re.finditer(pattern, content):
        level = match.group(1)
        text = match.group(2)
        note_id = match.group(3)
        notes.append({
            'id': note_id,
            'level': level,
            'text': text
        })
    
    return notes


def save_global_notes(notes):
    """保存全局注意事项"""
    content = """# 全局注意事项

<!-- 这里的内容会显示在每天的今日任务页面 -->

"""
    for note in notes:
        content += f"- [{note['level']}] {note['text']} | ID:{note['id']}\n"
    
    GLOBAL_NOTES_FILE.write_text(content, encoding='utf-8')


def get_daily_file(date_str=None):
    """获取每日记录文件路径"""
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    return DAILY_DIR / f'{date_str}.md'


def parse_daily_record(date_str=None):
    """解析每日记录"""
    daily_file = get_daily_file(date_str)
    
    if not daily_file.exists():
        return {
            'date': date_str or datetime.now().strftime('%Y-%m-%d'),
            'tasks': [],
            'notes': '',
            'summary': ''
        }
    
    content = daily_file.read_text(encoding='utf-8')
    
    # 解析任务
    tasks = []
    task_pattern = r'- \[([ x])\] \*\*(\S+)\*\* (.+?) \| ID:(\w+)'
    for match in re.finditer(task_pattern, content):
        tasks.append({
            'completed': match.group(1) == 'x',
            'priority': match.group(2),
            'description': match.group(3),
            'id': match.group(4)
        })
    
    # 解析注意事项
    notes_match = re.search(r'## 今日注意\n\n(.*?)(?=\n## |$)', content, re.DOTALL)
    notes = notes_match.group(1).strip() if notes_match else ''
    
    # 解析总结
    summary_match = re.search(r'## 今日总结\n\n(.*?)(?=\n## |$)', content, re.DOTALL)
    summary = summary_match.group(1).strip() if summary_match else ''
    
    return {
        'date': date_str or datetime.now().strftime('%Y-%m-%d'),
        'tasks': tasks,
        'notes': notes,
        'summary': summary
    }


def save_daily_record(date_str, tasks, notes, summary):
    """保存每日记录"""
    daily_file = get_daily_file(date_str)
    
    content = f"""# 工作日志 - {date_str}

## 今日任务

"""
    for task in tasks:
        checkbox = 'x' if task.get('completed', False) else ' '
        content += f"- [{checkbox}] **{task['priority']}** {task['description']} | ID:{task['id']}\n"
    
    content += f"""
## 今日注意

{notes}

## 今日总结

{summary}
"""
    daily_file.write_text(content, encoding='utf-8')


def generate_monthly_report(year, month):
    """生成月报"""
    month_str = f'{year}-{month:02d}'
    
    # 获取当月所有日记录
    daily_files = list(DAILY_DIR.glob(f'{month_str}-*.md'))
    
    total_tasks = 0
    completed_tasks = 0
    high_priority_completed = 0
    high_priority_total = 0
    daily_stats = []
    
    for daily_file in sorted(daily_files):
        date_str = daily_file.stem
        record = parse_daily_record(date_str)
        
        day_total = len(record['tasks'])
        day_completed = sum(1 for t in record['tasks'] if t.get('completed', False))
        day_high = sum(1 for t in record['tasks'] if t.get('priority') == '高')
        day_high_completed = sum(1 for t in record['tasks'] if t.get('priority') == '高' and t.get('completed', False))
        
        total_tasks += day_total
        completed_tasks += day_completed
        high_priority_total += day_high
        high_priority_completed += day_high_completed
        
        daily_stats.append({
            'date': date_str,
            'total': day_total,
            'completed': day_completed,
            'completion_rate': round(day_completed / day_total * 100, 1) if day_total > 0 else 0
        })
    
    # 生成月报内容
    completion_rate = round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0
    high_completion_rate = round(high_priority_completed / high_priority_total * 100, 1) if high_priority_total > 0 else 0
    
    report = {
        'month': month_str,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': completion_rate,
        'high_priority_total': high_priority_total,
        'high_priority_completed': high_priority_completed,
        'high_completion_rate': high_completion_rate,
        'daily_stats': daily_stats,
        'working_days': len(daily_files)
    }
    
    # 保存月报 Markdown
    report_content = f"""# 月度工作报告 - {month_str}

## 总体概况

- **工作天数**: {report['working_days']} 天
- **总任务数**: {total_tasks}
- **已完成任务**: {completed_tasks}
- **完成率**: {completion_rate}%
- **高优先级任务完成率**: {high_completion_rate}%

## 每日完成情况

| 日期 | 总任务 | 已完成 | 完成率 |
|------|--------|--------|--------|
"""
    for stat in daily_stats:
        report_content += f"| {stat['date']} | {stat['total']} | {stat['completed']} | {stat['completion_rate']}% |\n"
    
    report_content += """
## 分析与建议

"""
    # 添加自动分析
    if completion_rate >= 80:
        report_content += "- ✅ 本月任务完成率优秀，继续保持！\n"
    elif completion_rate >= 60:
        report_content += "- ⚠️ 本月任务完成率一般，建议优化时间管理。\n"
    else:
        report_content += "- ❌ 本月任务完成率较低，需要重点改进工作效率。\n"
    
    if high_completion_rate < completion_rate:
        report_content += "- 📌 高优先级任务完成率低于平均水平，建议优先处理重要任务。\n"
    
    monthly_file = MONTHLY_DIR / f'{month_str}.md'
    monthly_file.write_text(report_content, encoding='utf-8')
    
    return report


# API 路由
@app.route('/')
def index():
    """主页"""
    return send_file('templates/index.html')


@app.route('/api/requirements', methods=['GET'])
def get_requirements():
    """获取所有需求"""
    requirements = parse_requirements()
    # 转换为前端格式
    result = []
    for req in requirements:
        work_period = '待定'
        if req.get('work_start') and req.get('work_end'):
            work_period = f"{req['work_start']}~{req['work_end']}"
        
        status_map = {'待处理': 'pending', '进行中': 'in_progress', '已完成': 'completed', '已取消': 'cancelled'}
        priority_map = {'高': 'high', '中': 'medium', '低': 'low'}
        
        result.append({
            'id': req['id'],
            'category': req.get('category', '未分类'),
            'title': req.get('description', ''),
            'priority': priority_map.get(req.get('priority', '中'), 'medium'),
            'status': status_map.get(req.get('status', '待处理'), 'pending'),
            'created_date': req.get('created_date', ''),
            'work_period': work_period,
            'expected_date': req.get('due_date', '待定'),
            'completion_date': req.get('completed_date', '未完成'),
            'completed': req.get('completed', False)
        })
    return jsonify(result)


@app.route('/api/requirements', methods=['POST'])
def add_requirement():
    """添加需求"""
    data = request.json
    requirements = parse_requirements()
    
    # 转换前端格式到内部格式
    priority_map_rev = {'high': '高', 'medium': '中', 'low': '低'}
    status_map_rev = {'pending': '待处理', 'in_progress': '进行中', 'completed': '已完成', 'cancelled': '已取消'}
    
    # 解析 work_period
    work_start = ''
    work_end = ''
    work_period = data.get('work_period', '待定')
    if work_period and work_period != '待定' and '~' in work_period:
        parts = work_period.split('~')
        work_start = parts[0]
        work_end = parts[1]
    
    import uuid
    new_req = {
        'id': str(uuid.uuid4())[:8],
        'category': data.get('category', '未分类'),
        'description': data.get('title', data.get('description', '')),
        'priority': priority_map_rev.get(data.get('priority'), data.get('priority', '中')),
        'status': status_map_rev.get(data.get('status'), data.get('status', '待处理')),
        'created_date': datetime.now().strftime('%Y-%m-%d'),
        'work_start': work_start,
        'work_end': work_end,
        'due_date': data.get('expected_date', data.get('due_date', '待定')),
        'completed_date': '未完成',
        'completed': False
    }
    
    requirements.append(new_req)
    save_requirements(requirements)
    
    return jsonify(new_req)


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """获取所有分类"""
    requirements = parse_requirements()
    categories = list(set(req.get('category', '默认分类') for req in requirements))
    if not categories:
        categories = ['默认分类']
    return jsonify(sorted(categories))


@app.route('/api/requirements/<req_id>', methods=['PUT'])
def update_requirement(req_id):
    """更新需求"""
    data = request.json
    requirements = parse_requirements()
    
    # 转换前端格式到内部格式
    priority_map_rev = {'high': '高', 'medium': '中', 'low': '低'}
    status_map_rev = {'pending': '待处理', 'in_progress': '进行中', 'completed': '已完成', 'cancelled': '已取消'}
    
    # 解析 work_period
    work_start = ''
    work_end = ''
    work_period = data.get('work_period', '')
    if work_period and work_period != '待定' and '~' in work_period:
        parts = work_period.split('~')
        work_start = parts[0]
        work_end = parts[1]
    
    for req in requirements:
        if req['id'] == req_id:
            # 获取 title 或 description
            description = data.get('title', data.get('description', req['description']))
            
            # 优先级转换
            priority = data.get('priority', req['priority'])
            if priority in priority_map_rev:
                priority = priority_map_rev[priority]
            
            # 状态转换
            status = data.get('status', req['status'])
            if status in status_map_rev:
                status = status_map_rev[status]
            
            req.update({
                'category': data.get('category', req.get('category', '未分类')),
                'description': description,
                'priority': priority,
                'status': status,
                'work_start': work_start if work_start else req.get('work_start', ''),
                'work_end': work_end if work_end else req.get('work_end', ''),
                'due_date': data.get('expected_date', data.get('due_date', req['due_date'])),
            })
            
            if status == '已完成':
                req['completed'] = True
                req['completed_date'] = data.get('completion_date', datetime.now().strftime('%Y-%m-%d'))
            elif status == '已取消':
                req['completed'] = False
                req['completed_date'] = '已取消'
            else:
                req['completed'] = False
                req['completed_date'] = '未完成'
            
            break
    
    save_requirements(requirements)
    return jsonify({'success': True})


@app.route('/api/requirements/<req_id>', methods=['DELETE'])
def delete_requirement(req_id):
    """删除需求"""
    requirements = parse_requirements()
    requirements = [r for r in requirements if r['id'] != req_id]
    save_requirements(requirements)
    return jsonify({'success': True})


@app.route('/api/requirements/overdue/<date_str>', methods=['GET'])
def get_overdue_requirements(date_str):
    """获取超过预期完成日期但未完成的需求（延单任务）"""
    requirements = parse_requirements()
    
    try:
        check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify([])
    
    status_map = {'待处理': 'pending', '进行中': 'in_progress', '已完成': 'completed', '已取消': 'cancelled'}
    priority_map = {'高': 'high', '中': 'medium', '低': 'low'}
    
    result = []
    for req in requirements:
        # 只查找未完成的需求
        if req.get('status') in ['已完成', '已取消']:
            continue
        
        due_date_str = req.get('due_date', '待定')
        if due_date_str == '待定':
            continue
        
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            
            # 如果预期完成日期已过，但任务未完成
            if due_date < check_date:
                work_start = req.get('work_start', '')
                work_end = req.get('work_end', '')
                work_period = f"{work_start}~{work_end}" if work_start and work_end else '待定'
                
                # 计算延期天数
                overdue_days = (check_date - due_date).days
                
                result.append({
                    'id': req['id'],
                    'category': req.get('category', '未分类'),
                    'title': req.get('description', ''),
                    'priority': priority_map.get(req.get('priority', '中'), 'medium'),
                    'status': status_map.get(req.get('status', '待处理'), 'pending'),
                    'created_date': req.get('created_date', ''),
                    'work_period': work_period,
                    'expected_date': due_date_str,
                    'completion_date': req.get('completed_date', '未完成'),
                    'completed': req.get('completed', False),
                    'overdue_days': overdue_days  # 延期天数
                })
        except ValueError:
            continue
    
    # 按优先级和延期天数排序（高优先级、延期久的在前）
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    result.sort(key=lambda x: (priority_order.get(x['priority'], 1), -x['overdue_days']))
    
    return jsonify(result)


@app.route('/api/requirements/in-period/<date_str>', methods=['GET'])
def get_requirements_in_period(date_str):
    """获取在指定日期处理时间段内的需求"""
    requirements = parse_requirements()
    
    try:
        check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify([])
    
    status_map = {'待处理': 'pending', '进行中': 'in_progress', '已完成': 'completed', '已取消': 'cancelled'}
    priority_map = {'高': 'high', '中': 'medium', '低': 'low'}
    
    result = []
    for req in requirements:
        # 跳过已完成或已取消的需求
        if req.get('status') in ['已完成', '已取消']:
            continue
            
        work_start = req.get('work_start', '')
        work_end = req.get('work_end', '')
        
        if work_start and work_end:
            try:
                start_date = datetime.strptime(work_start, '%Y-%m-%d').date()
                end_date = datetime.strptime(work_end, '%Y-%m-%d').date()
                
                if start_date <= check_date <= end_date:
                    work_period = f"{work_start}~{work_end}"
                    result.append({
                        'id': req['id'],
                        'category': req.get('category', '未分类'),
                        'title': req.get('description', ''),
                        'priority': priority_map.get(req.get('priority', '中'), 'medium'),
                        'status': status_map.get(req.get('status', '待处理'), 'pending'),
                        'created_date': req.get('created_date', ''),
                        'work_period': work_period,
                        'expected_date': req.get('due_date', '待定'),
                        'completion_date': req.get('completed_date', '未完成'),
                        'completed': req.get('completed', False)
                    })
            except ValueError:
                continue
    
    return jsonify(result)


@app.route('/api/global-notes', methods=['GET'])
def get_global_notes():
    """获取全局注意事项"""
    notes = parse_global_notes()
    # 转换为前端格式
    result = []
    for note in notes:
        type_map = {'重要': 'important', '警告': 'warning', '提醒': 'info', 'info': 'info', 'warning': 'warning', 'important': 'important'}
        result.append({
            'id': note['id'],
            'type': type_map.get(note.get('level', 'info'), 'info'),
            'content': note.get('text', '')
        })
    return jsonify(result)


@app.route('/api/global-notes', methods=['POST'])
def save_or_add_global_note():
    """保存全局注意事项（支持保存整个列表或添加单个）"""
    data = request.json
    
    # 如果是数组，直接保存整个列表
    if isinstance(data, list):
        notes = []
        type_map_rev = {'info': '提醒', 'warning': '警告', 'important': '重要'}
        for item in data:
            notes.append({
                'id': item.get('id', ''),
                'level': type_map_rev.get(item.get('type', 'info'), '提醒'),
                'text': item.get('content', '')
            })
        save_global_notes(notes)
        return jsonify({'success': True})
    
    # 如果是单个对象，添加新的
    notes = parse_global_notes()
    import uuid
    
    type_map_rev = {'info': '提醒', 'warning': '警告', 'important': '重要'}
    new_note = {
        'id': str(uuid.uuid4())[:8],
        'level': type_map_rev.get(data.get('type', 'info'), data.get('level', '提醒')),
        'text': data.get('content', data.get('text', ''))
    }
    
    notes.append(new_note)
    save_global_notes(notes)
    
    return jsonify(new_note)


@app.route('/api/global-notes/<note_id>', methods=['DELETE'])
def delete_global_note(note_id):
    """删除全局注意事项"""
    notes = parse_global_notes()
    notes = [n for n in notes if n['id'] != note_id]
    save_global_notes(notes)
    return jsonify({'success': True})


@app.route('/api/daily/<date_str>', methods=['GET'])
def get_daily(date_str):
    """获取每日记录"""
    record = parse_daily_record(date_str)
    return jsonify(record)


@app.route('/api/daily/<date_str>', methods=['POST'])
def save_daily(date_str):
    """保存每日记录"""
    data = request.json
    save_daily_record(
        date_str,
        data.get('tasks', []),
        data.get('notes', ''),
        data.get('summary', '')
    )
    return jsonify({'success': True})


@app.route('/api/daily/<date_str>/add-task', methods=['POST'])
def add_daily_task(date_str):
    """添加今日任务"""
    data = request.json
    record = parse_daily_record(date_str)
    
    import uuid
    new_task = {
        'id': data.get('id', str(uuid.uuid4())[:8]),
        'description': data['description'],
        'priority': data.get('priority', '中'),
        'completed': False
    }
    
    record['tasks'].append(new_task)
    
    # 按优先级排序
    priority_order = {'高': 0, '中': 1, '低': 2}
    record['tasks'].sort(key=lambda x: priority_order.get(x['priority'], 1))
    
    save_daily_record(date_str, record['tasks'], record['notes'], record['summary'])
    return jsonify(new_task)


@app.route('/api/daily/<date_str>/complete-task/<task_id>', methods=['POST'])
def complete_daily_task(date_str, task_id):
    """完成今日任务"""
    record = parse_daily_record(date_str)
    
    for task in record['tasks']:
        if task['id'] == task_id:
            task['completed'] = True
            break
    
    save_daily_record(date_str, record['tasks'], record['notes'], record['summary'])
    return jsonify({'success': True})


@app.route('/api/monthly/<year>/<month>', methods=['GET'])
def get_monthly_report(year, month):
    """获取月报"""
    report = generate_monthly_report(int(year), int(month))
    return jsonify(report)


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计数据"""
    requirements = parse_requirements()
    
    total = len(requirements)
    completed = sum(1 for r in requirements if r.get('completed', False) or r.get('status') == '已完成')
    in_progress = sum(1 for r in requirements if r.get('status') == '进行中')
    pending = sum(1 for r in requirements if r.get('status') == '待处理')
    
    high_priority = sum(1 for r in requirements if r.get('priority') == '高')
    high_completed = sum(1 for r in requirements if r.get('priority') == '高' and (r.get('completed', False) or r.get('status') == '已完成'))
    
    return jsonify({
        'total': total,
        'completed': completed,
        'in_progress': in_progress,
        'pending': pending,
        'completion_rate': round(completed / total * 100, 1) if total > 0 else 0,
        'high_priority': high_priority,
        'high_completed': high_completed
    })


@app.route('/api/markdown/<path:filepath>', methods=['GET'])
def get_markdown(filepath):
    """获取 Markdown 文件内容"""
    file_path = DATA_DIR / filepath
    if file_path.exists():
        return jsonify({'content': file_path.read_text(encoding='utf-8')})
    return jsonify({'content': ''})


# 每日记录存储目录（Markdown格式）
DAILY_MARKDOWN_DIR = DATA_DIR / 'daily_markdown'
DAILY_MARKDOWN_DIR.mkdir(exist_ok=True)


def save_daily_markdown(date_str, content):
    """保存每日 Markdown 文件到磁盘"""
    md_file = DAILY_MARKDOWN_DIR / f'{date_str}.md'
    md_file.write_text(content, encoding='utf-8')
    return md_file


def generate_daily_markdown_content(date_str):
    """
    生成每日 Markdown 内容
    参照格式：
    ### 今日
    ### 注意
    ### 长期
    需求列表：
    分类名：
    - [ ] 任务内容
    """
    try:
        check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return '日期格式错误'
    
    # 获取全局注意事项
    notes = parse_global_notes()
    
    # 获取当日处理中的需求
    requirements = parse_requirements()
    period_tasks = []
    long_term_tasks = []
    
    for req in requirements:
        if req.get('status') in ['已完成', '已取消']:
            continue
        
        work_start = req.get('work_start', '')
        work_end = req.get('work_end', '')
        
        if work_start and work_end:
            try:
                start = datetime.strptime(work_start, '%Y-%m-%d').date()
                end = datetime.strptime(work_end, '%Y-%m-%d').date()
                if start <= check_date <= end:
                    period_tasks.append(req)
            except ValueError:
                pass
        else:
            # 没有设置处理时间的归类为长期任务
            long_term_tasks.append(req)
    
    # 获取当日记录的任务
    daily_record = parse_daily_record(date_str)
    today_tasks = daily_record.get('tasks', [])
    
    # 生成 Markdown
    content = f"### 今日 ({date_str})\n\n"
    
    # 当日任务
    if today_tasks:
        for task in today_tasks:
            checkbox = 'x' if task.get('completed') else ' '
            content += f"- [{checkbox}] {task.get('description', task.get('content', ''))}\n"
    else:
        content += "_暂无当日任务_\n"
    content += "\n\n"
    
    # 注意事项
    content += "### 注意\n\n"
    if notes:
        for note in notes:
            level = note.get('level', '提醒')
            text = note.get('text', '')
            if level == '重要':
                content += f"* {text}！！！！\n"
            elif level == '警告':
                content += f"* {text}！！\n"
            else:
                content += f"* {text}\n"
    else:
        content += "_暂无注意事项_\n"
    content += "\n\n"
    
    # 长期任务
    content += "### 长期\n\n"
    if long_term_tasks:
        for task in long_term_tasks:
            checkbox = 'x' if task.get('completed') else ' '
            desc = task.get('description', '')
            content += f"- [{checkbox}] {desc}\n"
    else:
        content += "_暂无长期任务_\n"
    content += "\n\n"
    
    # 当前处理中的需求（按分类）
    content += "需求列表：\n"
    if period_tasks:
        # 按分类分组
        grouped = {}
        for req in period_tasks:
            cat = req.get('category', '未分类')
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(req)
        
        for category, reqs in grouped.items():
            content += f"{category}：\n"
            for req in reqs:
                checkbox = 'x' if req.get('completed') else ' '
                desc = req.get('description', '')
                content += f"- [{checkbox}] {desc}\n"
            content += "\n"
    else:
        content += "_当日无处理中的需求_\n"
    
    return content


@app.route('/api/markdown-preview/<view_type>/<date_str>', methods=['GET'])
def get_markdown_preview(view_type, date_str):
    """
    生成 Markdown 预览内容
    view_type: 'daily' 或 'requirements'
    date_str: 日期字符串 (用于 daily 视图)
    
    参照格式：
    ### 今日
    ### 注意
    ### 长期
    需求列表：
    分类名：
    - [ ] 任务内容
    """
    if view_type == 'requirements':
        # 生成需求列表的 Markdown
        requirements = parse_requirements()
        
        # 按分类分组
        grouped = {}
        for req in requirements:
            cat = req.get('category', '未分类')
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(req)
        
        content = "# 工作需求列表\n\n"
        content += f"_生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n"
        
        for category, reqs in grouped.items():
            content += f"## {category}\n\n"
            for req in reqs:
                checkbox = 'x' if req.get('completed') or req.get('status') == '已完成' else ' '
                priority = req.get('priority', '中')
                desc = req.get('description', '')
                work_start = req.get('work_start', '')
                work_end = req.get('work_end', '')
                work_period = f"{work_start}~{work_end}" if work_start and work_end else '待定'
                due = req.get('due_date', '待定')
                
                content += f"- [{checkbox}] **{priority}** {desc}\n"
                content += f"  - 处理期间: {work_period} | 预计完成: {due}\n"
            content += "\n"
        
        return jsonify({'content': content})
    
    else:  # daily
        # 生成每日任务的 Markdown（参照 2026_02_25.md 格式）
        try:
            check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'content': '日期格式错误'})
        
        # 获取全局注意事项
        notes = parse_global_notes()
        
        # 获取当日处理中的需求
        requirements = parse_requirements()
        period_tasks = []
        long_term_tasks = []
        
        for req in requirements:
            if req.get('status') in ['已完成', '已取消']:
                continue
            
            work_start = req.get('work_start', '')
            work_end = req.get('work_end', '')
            
            if work_start and work_end:
                try:
                    start = datetime.strptime(work_start, '%Y-%m-%d').date()
                    end = datetime.strptime(work_end, '%Y-%m-%d').date()
                    if start <= check_date <= end:
                        period_tasks.append(req)
                except ValueError:
                    pass
            else:
                # 没有设置处理时间的归类为长期任务
                long_term_tasks.append(req)
        
        # 获取当日记录的任务
        daily_record = parse_daily_record(date_str)
        today_tasks = daily_record.get('tasks', [])
        
        # 生成 Markdown
        content = f"### 今日 ({date_str})\n\n"
        
        # 当日任务
        if today_tasks:
            for task in today_tasks:
                checkbox = 'x' if task.get('completed') else ' '
                content += f"- [{checkbox}] {task.get('description', task.get('content', ''))}\n"
        else:
            content += "_暂无当日任务_\n"
        content += "\n\n"
        
        # 注意事项
        content += "### 注意\n\n"
        if notes:
            for note in notes:
                level = note.get('level', '提醒')
                text = note.get('text', '')
                if level == '重要':
                    content += f"* {text}！！！！\n"
                elif level == '警告':
                    content += f"* {text}！！\n"
                else:
                    content += f"* {text}\n"
        else:
            content += "_暂无注意事项_\n"
        content += "\n\n"
        
        # 长期任务
        content += "### 长期\n\n"
        if long_term_tasks:
            for task in long_term_tasks:
                checkbox = 'x' if task.get('completed') else ' '
                desc = task.get('description', '')
                content += f"- [{checkbox}] {desc}\n"
        else:
            content += "_暂无长期任务_\n"
        content += "\n\n"
        
        # 当前处理中的需求（按分类）
        content += "需求列表：\n"
        if period_tasks:
            # 按分类分组
            grouped = {}
            for req in period_tasks:
                cat = req.get('category', '未分类')
                if cat not in grouped:
                    grouped[cat] = []
                grouped[cat].append(req)
            
            for category, reqs in grouped.items():
                content += f"{category}：\n"
                for req in reqs:
                    checkbox = 'x' if req.get('completed') else ' '
                    desc = req.get('description', '')
                    content += f"- [{checkbox}] {desc}\n"
                content += "\n"
        else:
            content += "_当日无处理中的需求_\n"
        
        return jsonify({'content': content})


@app.route('/api/markdown/<path:filepath>', methods=['POST'])
def save_markdown(filepath):
    """保存 Markdown 文件内容"""
    data = request.json
    file_path = DATA_DIR / filepath
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(data['content'], encoding='utf-8')
    return jsonify({'success': True})


@app.route('/api/save-daily-markdown/<date_str>', methods=['POST'])
def save_daily_markdown_api(date_str):
    """
    生成并保存每日 Markdown 文件到磁盘
    文件保存在 data/daily_markdown/{date_str}.md
    """
    content = generate_daily_markdown_content(date_str)
    md_file = save_daily_markdown(date_str, content)
    return jsonify({
        'success': True, 
        'file_path': str(md_file),
        'content': content
    })


@app.route('/api/list-daily-markdown', methods=['GET'])
def list_daily_markdown():
    """列出所有已保存的每日 Markdown 文件"""
    files = list(DAILY_MARKDOWN_DIR.glob('*.md'))
    result = []
    for f in sorted(files, reverse=True):
        result.append({
            'date': f.stem,
            'filename': f.name,
            'path': str(f)
        })
    return jsonify(result)


@app.route('/api/read-daily-markdown/<date_str>', methods=['GET'])
def read_daily_markdown(date_str):
    """读取已保存的每日 Markdown 文件"""
    md_file = DAILY_MARKDOWN_DIR / f'{date_str}.md'
    if md_file.exists():
        return jsonify({
            'exists': True,
            'content': md_file.read_text(encoding='utf-8'),
            'file_path': str(md_file)
        })
    return jsonify({'exists': False, 'content': ''})


if __name__ == '__main__':
    init_requirements_file()
    init_global_notes_file()
    app.run(debug=True, port=5000)
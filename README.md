# WorkTracker - 工作需求记录管理系统

一个极简黑白风格的工作需求管理系统，支持智能任务追踪、延单提醒、月度报告生成和 Markdown 数据持久化。

## ✨ 功能特性

### � 智能今日任务
- **自动任务匹配**: 根据需求的"处理时间段"自动显示当日任务
- **延单任务提醒**: 超过预期完成日期的任务自动标记并显示延期天数
- **全局注意事项**: 支持重要/警告/普通三种类型的提醒
- **日期选择器**: 可查看任意日期的任务列表

### 📝 需求管理
- 按分类组织需求（可折叠展开）
- 支持优先级设置（高/中/低）
- 支持状态管理（待处理/进行中/已完成/已取消）
- 设置处理时间段和预计完成日期
- 按优先级、状态、关键词筛选

### � Markdown 管理
- 预览每日任务的 Markdown 格式
- 复制/下载 Markdown 文件
- 一键保存到磁盘 (`data/daily_markdown/`)
- 支持查看需求列表的 Markdown

### 📊 月度报告
- 自动统计月度工作数据
- 工作天数、完成率、高优先级完成率
- 每日完成情况表格
- 自动保存报告到 `data/monthly/`

### 📈 统计分析
- 任务状态分布柱状图
- 实时统计完成率

## 🎨 设计风格

**Noir 极简黑白风格**
- 纯黑背景 (#0a0a0a)
- 白色/灰色层次分明
- 无彩色干扰，专注工作

## 📁 数据存储

所有数据以 Markdown 格式存储，方便版本控制和手动编辑：

```
data/
├── requirements.md          # 需求列表
├── global_notes.md          # 全局注意事项
├── daily/                   # 每日任务数据 (JSON)
│   └── 2026-02-25.md
├── daily_markdown/          # 每日任务 Markdown (格式化)
│   └── 2026-02-25.md
└── monthly/                 # 月度报告
    └── 2026-02.md
```

## 🚀 安装和运行

### 1. 克隆项目

```bash
git clone https://github.com/SeaLeee/WorkTracker.git
cd WorkTracker
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 初始化数据文件

```bash
# 复制示例文件作为初始数据
cp data/requirements.example.md data/requirements.md
cp data/global_notes.example.md data/global_notes.md
```

### 4. 启动应用

```bash
python app.py
```

或直接双击 `启动.bat` (Windows)

### 5. 访问应用

打开浏览器访问: http://localhost:5000

## 🛠 技术栈

- **后端**: Python Flask
- **前端**: Vue.js 3 (CDN) + Tailwind CSS
- **图表**: Chart.js
- **数据存储**: Markdown 文件（无数据库依赖）

## 📸 界面预览

应用包含五个主要视图：
1. **今日任务** - 智能显示当日需处理的任务 + 延单提醒
2. **全部需求** - 按分类管理所有需求
3. **Markdown 管理** - 预览和导出 Markdown
4. **月报** - 月度统计和报告生成
5. **统计** - 数据可视化分析

## 📖 使用说明

1. **新建需求**: 点击右上角"+ 新建需求"
2. **设置处理时间段**: 需求会在该时间段内自动出现在今日任务
3. **延单提醒**: 超过预期完成日期的任务会在"延单任务"区域显示
4. **完成任务**: 点击任务前的复选框
5. **保存 Markdown**: 在 Markdown 管理页面点击"保存到磁盘"

## 📄 许可证

MIT License
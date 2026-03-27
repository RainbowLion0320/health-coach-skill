# Health Coach Skill

一个全面的个人健康数据管理与智能饮食推荐系统。

## 功能模块

| 模块 | 状态 | 说明 |
|-----|------|------|
| 用户档案管理 | ✅ | 身高、体重、年龄、BMR/TDEE 计算 |
| 身体数据记录 | ✅ | 体重、BMI、体脂率时间序列 |
| 饮食日志 | ✅ | 每日三餐记录，支持中文食物 |
| 食材数据库 | ✅ | 内置 569 种中餐食物，支持扩展 |
| 饮食推荐 | ✅ | 基于目标和剩余预算的推荐 |
| 数据分析 | ✅ | 周报、营养分析、趋势统计 |
| OCR 拍照识别 | ✅ | 双引擎（Kimi + macOS），条形码优先匹配 |
| 数据导出 | ✅ | JSON/CSV 格式导出 |
| 数据备份 | ✅ | 自动备份与恢复 |

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

```bash
# 1. 初始化数据库
python3 scripts/init_db.py --user robert

# 2. 设置用户档案
python3 scripts/user_profile.py --user robert set \
  --name "Robert" \
  --gender male \
  --birth-date 1994-05-15 \
  --height-cm 175 \
  --target-weight-kg 70 \
  --activity-level moderate \
  --goal-type maintain

# 3. 记录体重
python3 scripts/body_metrics.py --user robert log-weight --weight 72.5

# 4. 记录饮食
python3 scripts/meal_logger.py --user robert log \
  --meal-type lunch \
  --foods "米饭:150g, 鸡胸肉:100g, 西兰花:100g"

# 5. 查看每日摘要
python3 scripts/meal_logger.py --user robert daily-summary

# 6. 获取饮食推荐
python3 scripts/diet_recommender.py --user robert recommend --meal-type dinner

# 7. 生成报告
python3 scripts/report_generator.py --user robert nutrition --days 7
```

## 技术架构

```
health-coach/
├── SKILL.md                    # 主文档（Skill 入口）
├── README.md                   # 本文件
├── references/
│   ├── ARCHITECTURE.md         # 系统架构设计
│   ├── DATABASE_SCHEMA.md      # 数据库设计
│   ├── API_REFERENCE.md        # API 文档
│   └── FOOD_DATABASE.md        # 食材数据库规范
├── scripts/
│   ├── init_db.py              # 数据库初始化
│   ├── user_profile.py         # 用户档案管理
│   ├── body_metrics.py         # 身体数据记录
│   ├── meal_logger.py          # 饮食日志
│   ├── food_analyzer.py        # 食物分析
│   ├── diet_recommender.py     # 饮食推荐
│   └── report_generator.py     # 报告生成
└── data/
    └── <username>.db           # 用户隔离的 SQLite 数据库
```

## 数据库设计

- **多用户隔离**: 每个用户独立 SQLite 文件
- **时间序列**: 体重、饮食支持历史追踪
- **营养计算**: 自动计算卡路里和宏量营养素
- **可扩展**: 支持自定义食物添加

## 扩展性设计

1. **营养数据源**: 预留 USDA API 接口
2. **推荐算法**: 支持多种饮食模式（低碳、高蛋白等）
3. **拍照识别**: Vision API 集成占位
4. **报告模板**: 支持 text/json/html 格式

## 数据管理

```bash
# 导出数据
python3 scripts/export_data.py --user robert --format json
python3 scripts/export_data.py --user robert --format csv -o ./exports

# 备份数据库
python3 scripts/backup_db.py --user robert backup
python3 scripts/backup_db.py --user robert list
python3 scripts/backup_db.py --user robert restore --file robert_20260327_164628.db
```

## Web 评估面板

```bash
# 启动面板（自动打开浏览器）
python3 scripts/launch_dashboard.py --user robert

# 访问 http://127.0.0.1:5000
```

**功能**：
- 📊 今日营养概览
- ⚖️ 体重趋势图（30天）
- 🍽️ 营养摄入趋势（7天）
- 👤 身体数据展示

## OCR 食品识别

```bash
# 静默扫描（自动处理）
python3 scripts/food_analyzer.py --user robert scan --image chips.jpg

# 查看详情
python3 scripts/food_analyzer.py --user robert scan --image chips.jpg --verbose

# 调整变化阈值
python3 scripts/food_analyzer.py --user robert scan --image chips.jpg --threshold 5

# 主动更新
python3 scripts/food_analyzer.py --user robert update-by-barcode \
  --barcode 6941234567890 --calories 550 --protein 6.5 --carbs 55 --fat 36 --fiber 3
```

## 文档

| 文档 | 说明 |
|-----|------|
| [FEATURE_GUIDE.md](references/FEATURE_GUIDE.md) | 用户功能手册 |
| [DEVELOPER_GUIDE.md](references/DEVELOPER_GUIDE.md) | 开发者 API 参考 |
| [ARCHITECTURE.md](references/ARCHITECTURE.md) | 系统架构设计 |
| [DATABASE_SCHEMA.md](references/DATABASE_SCHEMA.md) | 数据库设计 |

## 待完成

- [ ] USDA FoodData Central API 集成
- [ ] 更多推荐算法（低碳、16:8 轻断食等）
- [ ] 周报/月报 HTML 模板
- [ ] 数据同步（多设备）

## 测试状态

所有核心脚本已通过测试：
- ✅ init_db.py - 数据库初始化
- ✅ user_profile.py - 用户档案创建/查询
- ✅ body_metrics.py - 体重记录/BMI计算
- ✅ meal_logger.py - 饮食记录/营养计算
- ✅ food_analyzer.py - 食物搜索/添加
- ✅ diet_recommender.py - 饮食推荐
- ✅ report_generator.py - 营养分析报告

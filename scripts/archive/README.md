# Archive Directory

此目录存放已废弃/历史版本的脚本，仅作备份保留，不再维护。

## 文件说明

| 文件 | 废弃原因 | 替代方案 |
|------|---------|---------|
| `web_server_v3.py` | 与 `web_server.py` 重复，且未被使用 | 使用 `web_server.py` |
| `migrate_db.py` | 一次性迁移脚本，已完成历史使命 | 数据库结构已稳定 |
| `migrate_body_metrics.py` | 一次性迁移脚本，已完成 | 表结构已更新 |
| `update_food_database.py` | 功能被 `fill_food_defaults.py` 替代 | 使用 `fill_food_defaults.py` |
| `fill_food_defaults.py` | 一次性数据填充脚本，已完成 | 数据已存入 custom_foods 表 |

**注意：** 这些脚本可能包含过时的代码逻辑，不建议直接使用。

## 新增食物数据规范

未来新增食物时：
- **钠含量**：通过搜索引擎查询具体食物的钠含量（mg/100g），不使用平均值
- **储存方式**：根据食物类别合理推断（冰箱/冷冻/干货区）
- **保质期**：参考食品安全标准，按储存方式设定

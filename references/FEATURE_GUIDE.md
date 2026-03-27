# Health Coach 功能手册

> 面向用户的完整功能说明，非开发文档。

---

## 1. 用户档案管理

### 功能
记录身体基本信息，自动计算代谢率。

### 数据项
| 字段 | 说明 | 用途 |
|-----|------|------|
| 身高 | cm | BMI 计算 |
| 体重 | kg | TDEE 计算 |
| 年龄 | 自动计算 | BMR 计算 |
| 性别 | male/female | BMR 公式选择 |
| 活动水平 | 久坐/轻度/中度/高度/极高 | TDEE 乘数 |
| 目标 | 减脂/维持/增肌 | 热量目标调整 |

### 自动计算
- **BMR**（基础代谢率）：Mifflin-St Jeor 公式
- **TDEE**（每日总消耗）：BMR × 活动系数

### 使用
```bash
# 设置档案
python3 scripts/user_profile.py --user <name> set \
  --gender male --birth-date 1994-05-15 \
  --height-cm 175 --activity-level moderate --goal-type maintain

# 查看档案
python3 scripts/user_profile.py --user <name> get
```

---

## 2. 身体数据记录

### 功能
记录体重、体脂等身体指标，追踪趋势。

### 自动计算
- **BMI**：体重(kg) / 身高(m)²
- **趋势**：7天/30天变化

### 使用
```bash
# 记录体重
python3 scripts/body_metrics.py --user <name> log-weight \
  --weight 72.5 --body-fat 18.5

# 查看趋势
python3 scripts/body_metrics.py --user <name> trend --days 30
```

---

## 3. 饮食日志

### 功能
记录每日三餐，自动计算营养。

### 食物格式
```
米饭:150g, 鸡胸肉:100g, 西兰花:100g
```

### 自动计算
- 每道菜的热量、蛋白质、碳水、脂肪
- 每日总计
- 剩余可摄入（vs TDEE）

### 使用
```bash
# 记录一餐
python3 scripts/meal_logger.py --user <name> log \
  --meal-type lunch \
  --foods "米饭:150g, 鸡胸肉:100g"

# 查看今日摘要
python3 scripts/meal_logger.py --user <name> daily-summary
```

---

## 4. 食材数据库

### 内置数据
- **569 种中餐食物**：主食、肉蛋、蔬菜、水果、零食等
- **营养数据**：每100g的热量、蛋白质、碳水、脂肪、纤维

### 自定义添加
```bash
# 手动添加
python3 scripts/food_analyzer.py --user <name> add-custom \
  --name "红烧肉" --calories 350 --protein 15 --carbs 20 --fat 25

# OCR 扫描添加（见第6章）
```

### 搜索
```bash
python3 scripts/food_analyzer.py --user <name> search --query "牛肉"
```

---

## 5. 饮食推荐

### 功能
基于目标和剩余热量，推荐餐食组合。

### 推荐逻辑
- 根据 TDEE 计算每餐目标热量
- 从数据库选择食材组合
- 平衡蛋白质、碳水、脂肪

### 使用
```bash
# 推荐晚餐
python3 scripts/diet_recommender.py --user <name> recommend \
  --meal-type dinner --count 3

# 生成全天计划
python3 scripts/diet_recommender.py --user <name> daily-plan
```

---

## 6. OCR 食品识别

### 功能概述
通过拍照识别食品包装上的营养成分表，自动提取数据并与数据库匹配。

### 工作流程
```
拍照 → OCR识别 → 数据库匹配 → 差异对比 → 用户确认 → 添加到数据库
```

### 支持的 OCR 引擎
| 引擎 | 精度 | 成本 | 适用场景 |
|-----|------|------|---------|
| **Kimi Vision** | ⭐⭐⭐⭐⭐ | 低（已有key） | 默认推荐 |
| **macOS Vision** | ⭐⭐⭐ | 免费 | 备选/离线 |

### 核心特性
- **条形码优先匹配**：精准识别同款商品
- **静默模式**：小差异自动处理，大差异才提示
- **数据积累**：扫描过的商品自动入库

### 使用方式

#### 1. 扫描包装（静默模式）
```bash
python3 scripts/food_analyzer.py --user <name> scan --image chips.jpg
```

**输出示例**：
```
✅ 条形码完全匹配
   数据库商品: 乐事原味薯片
   动作: use_existing (数据一致)
```

#### 2. 指定 OCR 引擎
```bash
# 使用 Kimi（默认）
python3 scripts/food_analyzer.py --user robert scan --image chips.jpg --engine kimi

# 使用 macOS Vision（本地免费）
python3 scripts/food_analyzer.py --user robert scan --image chips.jpg --engine macos
```

#### 3. 主动更新
```bash
python3 scripts/food_analyzer.py --user <name> update-by-barcode \
  --barcode 6941234567890 --calories 550 --protein 6.5
```

### 匹配结果类型
| 结果 | 说明 | 动作 |
|-----|------|------|
| ✅ **数据一致** | 条形码匹配，营养差异 <10% | 直接使用，无提示 |
| ⚠️ **建议更新** | 条形码匹配，营养差异 >10% | 提示更新命令 |
| ❌ **新商品** | 无条形码匹配 | 自动添加到数据库 |

### 注意事项
1. **拍照质量**：光线充足、文字清晰、避免反光
2. **角度**：尽量正对包装，避免倾斜
3. **完整性**：确保营养成分表完整入镜

### 配置
```bash
# 环境变量
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.moonshot.cn/v1"
```

---

## 7. 食材库存管理（Pantry）

### 功能
管理家中食材，追踪剩余量，过期提醒。

### 核心概念
| 概念 | 说明 |
|-----|------|
| 初始量 | 购买时的重量 |
| 剩余量 | 当前实际剩余（自动扣减） |
| 过期时间 | 到期自动提醒 |
| 使用记录 | 每次用量可追溯 |

### 使用
```bash
# 添加食材
python3 scripts/pantry_manager.py --user <name> add \
  --food "鸡胸肉" --quantity 500 --expiry 2026-04-05

# 记录使用（自动扣减剩余）
python3 scripts/pantry_manager.py --user <name> use \
  --item-id 1 --amount 200 --notes "做沙拉"

# 查看剩余
python3 scripts/pantry_manager.py --user <name> remaining

# 查看快过期
python3 scripts/pantry_manager.py --user <name> list --expiring 3
```

---

## 8. 智能菜谱推荐

### 功能
基于库存食材和营养缺口，推荐可做的菜。

### 推荐逻辑
1. **营养缺口分析**：对比近期摄入 vs 目标
2. **库存检查**：优先使用快过期食材
3. **动态阈值**：
   - 充足（≥3种 >50g）：正常推荐
   - 不足（<3种 >50g）：降级到>20g，提示补货
   - 极少（<3种 >0g）：包含所有，提示严重不足

### 使用
```bash
python3 scripts/smart_recipe.py --user <name> --count 3
```

### 输出示例
```
营养缺口：热量 2061kcal, 蛋白质 162g
库存状态：充足（14种食材）
快过期：菠菜(1天), 西兰花(2天), 米饭(3天)

推荐：
1. 豆腐 + 米饭 + 菠菜
   热量：402kcal, 蛋白质：26.4g
   ✅ 优先使用快过期食材
```

---

## 9. 数据导出与备份

### 导出
```bash
# JSON 格式
python3 scripts/export_data.py --user <name> --format json

# CSV 格式
python3 scripts/export_data.py --user <name> --format csv -o ./exports
```

### 备份
```bash
# 创建备份
python3 scripts/backup_db.py --user <name> backup

# 列出备份
python3 scripts/backup_db.py --user <name> list

# 恢复备份
python3 scripts/backup_db.py --user <name> restore --file <backup_file>
```

---

## 7. 食材库存管理（Pantry）

### 功能
管理家中食材，追踪剩余量，过期提醒，智能推荐菜谱。

### 核心概念
| 概念 | 说明 |
|-----|------|
| 储藏位置 | 冰箱/冷冻/干货区/台面 |
| 食材类别 | 蛋白质/蔬菜/碳水/水果/乳制品 |
| 剩余量 | 当前实际剩余（自动扣减） |
| 过期时间 | 到期自动提醒 |
| 使用记录 | 每次用量可追溯 |

### 储藏位置分类
| 位置 | 说明 | 典型食材 |
|-----|------|---------|
| **冰箱** ❄️ | 冷藏 | 鸡胸肉、蔬菜、鸡蛋、牛奶 |
| **冷冻** 🧊 | 冷冻保存 | 三文鱼、虾仁、冷冻肉类 |
| **干货区** 📦 | 常温干燥 | 燕麦、土豆、红薯、米面 |
| **台面** 🌡️ | 室温短期 | 香蕉、面包、当天食材 |

### 使用
```bash
# 添加食材（自动检测储藏方式）
python3 scripts/pantry_manager.py --user <name> add \
  --food "鸡胸肉" --quantity 500 --expiry 2026-04-05

# 记录使用（自动扣减剩余）
python3 scripts/pantry_manager.py --user <name> use \
  --item-id 1 --amount 200 --notes "做沙拉"

# 查看剩余
python3 scripts/pantry_manager.py --user <name> remaining

# 查看快过期
python3 scripts/pantry_manager.py --user <name> list --expiring 3
```

---

## 8. 智能菜谱推荐

### 功能
基于库存食材和营养缺口，推荐可做的菜。

### 推荐逻辑
1. **营养缺口分析**：对比近期摄入 vs 目标
2. **库存检查**：优先使用快过期食材
3. **动态阈值**：
   - 充足（≥3种 >50g）：正常推荐
   - 不足（<3种 >50g）：降级到>20g，提示补货
   - 极少（<3种 >0g）：包含所有，提示严重不足

### 使用
```bash
python3 scripts/smart_recipe.py --user <name> --count 3
```

### 输出示例
```
营养缺口：热量 2061kcal, 蛋白质 162g
库存状态：充足（14种食材）
快过期：菠菜(1天), 西兰花(2天), 米饭(3天)

推荐：
1. 豆腐 + 米饭 + 菠菜
   热量：402kcal, 蛋白质：26.4g
   ✅ 优先使用快过期食材
```

---

## 9. Web 评估面板（v2）

### 功能
可视化展示健康数据趋势，支持页签导航。

### 启动
```bash
# Maeve 触发
"打开健康评估面板"

# 或手动启动
python3 scripts/launch_dashboard.py --user <name>
```

### 访问
浏览器自动打开：http://127.0.0.1:5000

### 页签结构
| 页签 | 内容 |
|-----|------|
| 📊 **概览** | 今日数据、体重趋势、营养趋势、身体数据 |
| 🥬 **食材管理** | 按储藏位置分组的 pantry，支持使用/添加操作 |
| ⚖️ **体重记录** | 体重历史记录 |

### 食材管理页功能
- 按储藏位置分组（冰箱/冷冻/干货区/台面）
- 按食材类别筛选（蛋白质/蔬菜/碳水）
- 过期状态标签（🔴今天/🟡3天内/🟢新鲜）
- **使用按钮**：记录消耗，自动扣减剩余
- **添加按钮**：添加新食材，自动检测储藏方式
- **智能推荐**：根据库存推荐菜谱

---

## 10. 报告生成

---

## 11. 报告生成

### 功能
生成周期性营养分析报告。

### 使用
```bash
# 周报
python3 scripts/report_generator.py --user <name> weekly

# 营养分析
python3 scripts/report_generator.py --user <name> nutrition --days 30
```

---

## 快速参考：常用命令

| 场景 | 命令 |
|-----|------|
| 记录体重 | `body_metrics.py log-weight --weight 72.5` |
| 记录饮食 | `meal_logger.py log --meal-type lunch --foods "米饭:150g,鸡肉:100g"` |
| 查看今天吃了多少 | `meal_logger.py daily-summary` |
| 拍照加食物 | `food_analyzer.py scan --image food.jpg` |
| 查看冰箱有啥 | `pantry_manager.py remaining` |
| 记录使用食材 | `pantry_manager.py use --item-id 1 --amount 200` |
| 添加食材到 pantry | `pantry_manager.py add --food "鸡胸肉" --quantity 500` |
| 今晚吃啥 | `smart_recipe.py --count 3` |
| 打开面板 | `launch_dashboard.py` |
| 备份数据 | `backup_db.py backup` |

---

## 数据存储

- **位置**：`~/.openclaw/workspace/skills/health-coach/data/<username>.db`
- **格式**：SQLite
- **导出**：支持 JSON/CSV
- **备份**：自动保留最近10份

---

*最后更新：2026-03-27（v2：新增 Pantry 管理、智能菜谱、页签式 Web 面板）*

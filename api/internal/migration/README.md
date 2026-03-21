Single-database configuration for Flask.
# internal/migration/versions — 数据库迁移版本

## 概述

`versions/` 目录是 **Alembic 数据库迁移版本链**，每个 `.py` 文件记录一次数据库结构变更（建表、加字段、删索引等）。所有版本通过 `down_revision` 字段串联成一条有序的迁移链。

---

## 核心概念

### Alembic 版本文件结构

```python
revision = '4c31ff1b1fbd'      # 当前版本唯一 ID
down_revision = '26bd59f9789a' # 上一个版本 ID（形成链式依赖）
branch_labels = None
depends_on = None

def upgrade():
    """正向迁移：建表、加字段、建索引等"""
    op.create_table('api_key', ...)

def downgrade():
    """回滚迁移：删表、删字段等（与 upgrade 相反）"""
    op.drop_table('api_key')
```

### 迁移链示意

```
[初始] → 18b0d4977567 → 5053763c94fe → ... → 26bd59f9789a → 4c31ff1b1fbd → [最新]
```

每次 `flask db upgrade` 会从当前版本沿链向前执行所有未应用的 `upgrade()`；  
每次 `flask db downgrade` 会执行上一版本的 `downgrade()` 回滚。

---

## 版本文件清单

| 文件 | 版本 ID | 主要变更内容 |
|---|---|---|
| `18b0d4977567_.py` | 18b0d4977567 | 初始建表 |
| `5053763c94fe_.py` | 5053763c94fe | 早期表结构 |
| `e9355133b2f5_.py` | e9355133b2f5 | 表结构补充 |
| `ea2dc129853a_.py` | ea2dc129853a | 表结构补充 |
| `2204c3c0e4d4_.py` | 2204c3c0e4d4 | 字段/索引变更 |
| `36c79303c825_.py` | 36c79303c825 | 字段/索引变更 |
| `493395dc50b8_.py` | 493395dc50b8 | 字段/索引变更 |
| `6744f5ab8ea4_.py` | 6744f5ab8ea4 | 字段/索引变更 |
| `775e752e0220_.py` | 775e752e0220 | 字段/索引变更 |
| `826531831354_.py` | 826531831354 | 字段/索引变更 |
| `b017b44df199_.py` | b017b44df199 | 字段/索引变更 |
| `cadf5e2fe816_.py` | cadf5e2fe816 | 字段/索引变更 |
| `26bd59f9789a_.py` | 26bd59f9789a | 倒数第二版本 |
| `4c31ff1b1fbd_.py` | 4c31ff1b1fbd | 新增 `api_key` 表和 `end_user` 表 |
| `a5086d2a507c_.py` | a5086d2a507c | 最新版本 |

---

## 常用命令

```bash
# 在 api/ 目录下执行

# 升级到最新版本
flask db upgrade

# 升级到指定版本
flask db upgrade 4c31ff1b1fbd

# 回滚到上一个版本
flask db downgrade

# 回滚到指定版本
flask db downgrade 26bd59f9789a

# 回滚到初始状态
flask db downgrade base

# 查看当前数据库所在版本
flask db current

# 查看完整迁移历史链
flask db history

# 根据 Model 变化自动生成新迁移文件
flask db migrate -m "add xxx table"
```

---

## `4c31ff1b1fbd_.py` 详解（示例）

此版本新增两张表：

### `api_key` 表

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | UUID | 主键，自动生成 |
| `account_id` | UUID | 关联账号 |
| `api_key` | VARCHAR(255) | API 密钥值 |
| `is_active` | BOOLEAN | 是否启用，默认 false |
| `remark` | VARCHAR(255) | 备注 |
| `updated_at` | DATETIME | 更新时间 |
| `created_at` | DATETIME | 创建时间 |

### `end_user` 表

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | UUID | 主键，自动生成 |
| `tenant_id` | UUID | 租户 ID |
| `app_id` | UUID | 应用 ID |
| `updated_at` | DATETIME | 更新时间 |
| `created_at` | DATETIME | 创建时间 |

---

## 注意事项

- 迁移文件一旦提交**不要修改**，只能追加新版本
- `downgrade()` 必须与 `upgrade()` 完全对称，保证可回滚
- 生产环境执行迁移前务必**备份数据库**
- 数据库需安装 `uuid-ossp` 扩展（PostgreSQL），用于 `uuid_generate_v4()`
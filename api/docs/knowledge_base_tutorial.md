# 知识库模块使用教程

本文档覆盖 `知识库模块` 的主要接口，包括：知识库管理、文档管理、片段管理、召回测试。

## 1. 准备工作

### 1.1 启动服务

在 `api` 目录启动后端服务，并保证 PostgreSQL、Redis、向量数据库等依赖可用。

### 1.2 鉴权方式

知识库模块接口都需要登录态，请在请求头中携带：

```bash
Authorization: Bearer <access_token>
```

测试代码里默认使用了固定测试账号的 Token，实际联调时请替换成你自己的登录 Token。

---

## 2. 知识库接口

### 2.1 获取知识库分页列表

```bash
curl --location 'http://127.0.0.1:5001/datasets?current_page=1&page_size=20&search_word=客服' \
--header 'Authorization: Bearer <access_token>'
```

### 2.2 创建知识库

```bash
curl --location 'http://127.0.0.1:5001/datasets' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer <access_token>' \
--data '{
  "name": "客服知识库",
  "icon": "https://cdn.imooc.com/dataset.png",
  "description": "沉淀客服问答、售后流程和商品说明"
}'
```

说明：
- `name` 必填，最长 100 字符。
- `icon` 必填，必须是合法 URL。
- `description` 可为空；为空时后端会自动生成默认描述。

### 2.3 获取知识库详情

```bash
curl --location 'http://127.0.0.1:5001/datasets/<dataset_id>' \
--header 'Authorization: Bearer <access_token>'
```

### 2.4 更新知识库

```bash
curl --location 'http://127.0.0.1:5001/datasets/<dataset_id>' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer <access_token>' \
--data '{
  "name": "客服知识库-正式版",
  "icon": "https://cdn.imooc.com/dataset-new.png",
  "description": "更新后的知识库描述"
}'
```

### 2.5 删除知识库

```bash
curl --location --request POST 'http://127.0.0.1:5001/datasets/<dataset_id>/delete' \
--header 'Authorization: Bearer <access_token>'
```

### 2.6 查看最近查询记录

```bash
curl --location 'http://127.0.0.1:5001/datasets/<dataset_id>/queries' \
--header 'Authorization: Bearer <access_token>'
```

### 2.7 召回测试

```bash
curl --location 'http://127.0.0.1:5001/datasets/<dataset_id>/hit' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer <access_token>' \
--data '{
  "query": "退款规则是什么？",
  "retrieval_strategy": "semantic",
  "k": 3,
  "score": 0.5
}'
```

参数说明：
- `retrieval_strategy` 支持：`full_text`、`semantic`、`hybrid`
- `k` 范围：1-10
- `score` 范围：0-0.99

---

## 3. 文档接口

### 3.1 给知识库新增文档

先调用上传接口拿到 `upload_file_id`，再调用新增文档接口：

```bash
curl --location 'http://127.0.0.1:5001/datasets/<dataset_id>/documents' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer <access_token>' \
--data '{
  "upload_file_ids": [
    "<upload_file_id_1>",
    "<upload_file_id_2>"
  ],
  "process_type": "automatic"
}'
```

如果需要自定义处理规则，可以使用：

```bash
curl --location 'http://127.0.0.1:5001/datasets/<dataset_id>/documents' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer <access_token>' \
--data '{
  "upload_file_ids": ["<upload_file_id>"] ,
  "process_type": "custom",
  "rule": {
    "pre_process_rules": [
      {"id": "remove_extra_space", "enabled": true},
      {"id": "remove_url_and_email", "enabled": true}
    ],
    "segment": {
      "separators": ["\n\n", "\n", "。|！|？", " "],
      "chunk_size": 500,
      "chunk_overlap": 50
    }
  }
}'
```

### 3.2 获取文档分页列表

```bash
curl --location 'http://127.0.0.1:5001/datasets/<dataset_id>/documents?current_page=1&page_size=20&search_word=产品' \
--header 'Authorization: Bearer <access_token>'
```

### 3.3 获取文档详情

```bash
curl --location 'http://127.0.0.1:5001/datasets/<dataset_id>/documents/<document_id>' \
--header 'Authorization: Bearer <access_token>'
```

### 3.4 修改文档名称

```bash
curl --location 'http://127.0.0.1:5001/datasets/<dataset_id>/documents/<document_id>/name' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer <access_token>' \
--data '{
  "name": "新的文档名称.md"
}'
```

### 3.5 修改文档启用状态

```bash
curl --location 'http://127.0.0.1:5001/datasets/<dataset_id>/documents/<document_id>/enabled' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer <access_token>' \
--data '{
  "enabled": false
}'
```

注意：
- 只有 `completed` 状态的文档才允许切换启用状态。
- 重复设置相同状态会返回失败。

### 3.6 查询批次处理状态

```bash
curl --location 'http://127.0.0.1:5001/datasets/<dataset_id>/documents/batch/<batch>' \
--header 'Authorization: Bearer <access_token>'
```

### 3.7 删除文档

```bash
curl --location --request POST 'http://127.0.0.1:5001/datasets/<dataset_id>/documents/<document_id>/delete' \
--header 'Authorization: Bearer <access_token>'
```

---

## 4. 片段接口

### 4.1 获取片段分页列表

```bash
curl --location 'http://127.0.0.1:5001/datasets/<dataset_id>/documents/<document_id>/segments?current_page=1&page_size=20&search_word=退款' \
--header 'Authorization: Bearer <access_token>'
```

### 4.2 新增片段

```bash
curl --location 'http://127.0.0.1:5001/datasets/<dataset_id>/documents/<document_id>/segments' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer <access_token>' \
--data '{
  "content": "退款申请需要在订单支付后 7 天内提交。",
  "keywords": ["退款", "售后", "订单"]
}'
```

说明：
- `content` 必填。
- `keywords` 可为空数组；为空时后端会自动提取关键词。
- 片段内容 token 数不能超过 1000。

### 4.3 获取片段详情

```bash
curl --location 'http://127.0.0.1:5001/datasets/<dataset_id>/documents/<document_id>/segments/<segment_id>' \
--header 'Authorization: Bearer <access_token>'
```

### 4.4 更新片段

```bash
curl --location 'http://127.0.0.1:5001/datasets/<dataset_id>/documents/<document_id>/segments/<segment_id>' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer <access_token>' \
--data '{
  "content": "退款申请需要在订单支付后 15 天内提交。",
  "keywords": ["退款", "时效"]
}'
```

### 4.5 修改片段启用状态

```bash
curl --location 'http://127.0.0.1:5001/datasets/<dataset_id>/documents/<document_id>/segments/<segment_id>/enabled' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer <access_token>' \
--data '{
  "enabled": false
}'
```

### 4.6 删除片段

```bash
curl --location --request POST 'http://127.0.0.1:5001/datasets/<dataset_id>/documents/<document_id>/segments/<segment_id>/delete' \
--header 'Authorization: Bearer <access_token>'
```

---

## 5. 单元测试执行方式

本次补充的知识库模块测试文件位于：

- `api/test/internal/handler/test_dataset_handler.py`

执行命令：

```bash
pytest api/test/internal/handler/test_dataset_handler.py -q
```

如果你只想跑单个测试方法，例如：

```bash
pytest api/test/internal/handler/test_dataset_handler.py -k test_segment_endpoints -q
```

---

## 6. 常见问题

### 6.1 为什么创建文档后没有立刻完成解析？
因为文档构建是异步任务，接口返回成功只代表已成功入库并提交后台处理。

### 6.2 为什么文档/片段不能修改启用状态？
通常是因为当前状态不是 `completed`，或者本次设置值与当前状态一致。

### 6.3 为什么召回测试没有结果？
常见原因包括：
- 知识库下没有可用片段
- 文档或片段处于禁用状态
- `score` 过滤阈值设置过高
- 检索策略与数据特征不匹配

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""知识库模块接口测试"""
import os
from datetime import datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from internal.entity.dataset_entity import DocumentStatus, ProcessType, RetrievalStrategy, SegmentStatus
from internal.model import Account, Dataset, Document, ProcessRule, Segment, UploadFile
from internal.service.jwt_service import JwtService
from pkg.response import HttpCode

TEST_ACCOUNT_ID = UUID("46db30d1-3199-4e79-a0cd-abf12fa6858f")
TEST_ACCOUNT_EMAIL = os.getenv("TEST_EMAIL", "test@imooc.com")
TEST_ACCOUNT_PASSWORD = os.getenv("TEST_PASSWORD", "Test1234")
TEST_ACCOUNT_TOKEN = JwtService.generate_token({
    "sub": str(TEST_ACCOUNT_ID),
    "iss": "llmops",
    "exp": 4102444800,
})


class DummyLock:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class DummyRedis:
    def get(self, key):
        return None

    def setex(self, key, expire, value):
        return None

    def lock(self, key, expire):
        return DummyLock()


class DummyVectorData:
    def update(self, *args, **kwargs):
        return None

    def delete_by_id(self, *args, **kwargs):
        return None


class DummyVectorStore:
    def add_documents(self, *args, **kwargs):
        return None


class DummyVectorCollection:
    def __init__(self):
        self.data = DummyVectorData()


def ensure_test_account(db):
    account = db.session.query(Account).get(TEST_ACCOUNT_ID)
    if account is None:
        account = Account(id=TEST_ACCOUNT_ID, name="Test User", email=TEST_ACCOUNT_EMAIL, avatar="")
        db.session.add(account)
        db.session.commit()
    return account


def ensure_test_token(client):
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {TEST_ACCOUNT_TOKEN}"


def get_handler(app, endpoint):
    return app.view_functions[endpoint].__self__


def create_dataset(db, name="知识库测试"):
    dataset = Dataset(
        id=uuid4(),
        account_id=TEST_ACCOUNT_ID,
        name=name,
        icon="https://cdn.imooc.com/dataset.png",
        description="知识库描述",
    )
    db.session.add(dataset)
    db.session.commit()
    return dataset


def create_upload_file(db, name="需求文档.md"):
    upload_file = UploadFile(
        id=uuid4(),
        account_id=TEST_ACCOUNT_ID,
        name=name,
        key=f"uploads/{name}",
        size=1024,
        extension="md",
        mime_type="text/markdown",
        hash=str(uuid4()).replace("-", ""),
    )
    db.session.add(upload_file)
    db.session.commit()
    return upload_file


def create_process_rule(db, dataset_id):
    process_rule = ProcessRule(
        id=uuid4(),
        account_id=TEST_ACCOUNT_ID,
        dataset_id=dataset_id,
        mode=ProcessType.AUTOMATIC,
        rule={"pre_process_rules": [], "segment": {"separators": ["\n"], "chunk_size": 500, "chunk_overlap": 50}},
    )
    db.session.add(process_rule)
    db.session.commit()
    return process_rule


def create_document(db, dataset_id, name="产品说明书.md", enabled=True, batch="batch-001"):
    upload_file = create_upload_file(db, name)
    process_rule = create_process_rule(db, dataset_id)
    document = Document(
        id=uuid4(),
        account_id=TEST_ACCOUNT_ID,
        dataset_id=dataset_id,
        upload_file_id=upload_file.id,
        process_rule_id=process_rule.id,
        batch=batch,
        name=name,
        position=1,
        enabled=enabled,
        disabled_at=None if enabled else datetime.now(),
        status=DocumentStatus.COMPLETED,
    )
    db.session.add(document)
    db.session.commit()
    return document


def create_segment(db, dataset_id, document_id, content="这是知识库片段", enabled=True, position=1):
    segment = Segment(
        id=uuid4(),
        account_id=TEST_ACCOUNT_ID,
        dataset_id=dataset_id,
        document_id=document_id,
        node_id=uuid4(),
        position=position,
        content=content,
        character_count=len(content),
        token_count=max(1, len(content) // 2),
        keywords=["知识库", "测试"],
        hash=f"hash-{position}",
        hit_count=2,
        enabled=enabled,
        disabled_at=None if enabled else datetime.now(),
        status=SegmentStatus.COMPLETED,
    )
    db.session.add(segment)
    db.session.commit()
    return segment


class TestKnowledgeBaseHandler:
    def test_dataset_crud(self, client, db, monkeypatch):
        ensure_test_account(db)
        ensure_test_token(client)

        create_resp = client.post("/datasets", json={
            "name": "新建知识库",
            "icon": "https://cdn.imooc.com/new-dataset.png",
            "description": "",
        })
        assert create_resp.status_code == 200
        assert create_resp.json.get("code") == HttpCode.SUCCESS

        dataset = db.session.query(Dataset).filter_by(name="新建知识库").one()
        assert dataset.description == "当你需要回答管理《新建知识库》的时候可以引用该知识库。"

        list_resp = client.get("/datasets", query_string={"search_word": "新建"})
        assert list_resp.status_code == 200
        assert len(list_resp.json["data"]["list"]) == 1

        update_resp = client.post(f"/datasets/{dataset.id}", json={
            "name": "更新后的知识库",
            "icon": "https://cdn.imooc.com/dataset-updated.png",
            "description": "",
        })
        assert update_resp.json.get("code") == HttpCode.SUCCESS

        monkeypatch.setattr("internal.service.dataset_service.delete_dataset.delay", lambda dataset_id: None)
        delete_resp = client.post(f"/datasets/{dataset.id}/delete")
        assert delete_resp.json.get("code") == HttpCode.SUCCESS
        assert db.session.query(Dataset).get(dataset.id) is None

    def test_dataset_hit(self, client, app, db, monkeypatch):
        ensure_test_account(db)
        ensure_test_token(client)
        dataset = create_dataset(db)
        document = create_document(db, dataset.id)
        segment = create_segment(db, dataset.id, document.id)

        dataset_service = get_handler(app, "llmops.hit").dataset_service
        monkeypatch.setattr(
            dataset_service.retrieval_service,
            "search_in_datasets",
            lambda **kwargs: [SimpleNamespace(metadata={"segment_id": str(segment.id), "score": 0.91})],
        )

        resp = client.post(f"/datasets/{dataset.id}/hit", json={
            "query": "请介绍知识库",
            "retrieval_strategy": RetrievalStrategy.SEMANTIC.value,
            "k": 3,
            "score": 0.5,
        })
        assert resp.status_code == 200
        assert resp.json.get("code") == HttpCode.SUCCESS
        assert resp.json["data"][0]["id"] == str(segment.id)
        assert resp.json["data"][0]["document"]["id"] == str(document.id)

    def test_document_endpoints(self, client, app, db, monkeypatch):
        ensure_test_account(db)
        ensure_test_token(client)
        dataset = create_dataset(db)
        upload_file_1 = create_upload_file(db, "一号文档.md")
        upload_file_2 = create_upload_file(db, "二号文档.md")
        monkeypatch.setattr("internal.service.document_service.build_documents.delay", lambda document_ids: None)

        create_resp = client.post(f"/datasets/{dataset.id}/documents", json={
            "upload_file_ids": [str(upload_file_1.id), str(upload_file_2.id), str(upload_file_1.id)],
            "process_type": ProcessType.AUTOMATIC,
        })
        assert create_resp.status_code == 200
        assert create_resp.json.get("code") == HttpCode.SUCCESS
        assert len(create_resp.json["data"]["documents"]) == 2

        document = db.session.query(Document).filter(Document.dataset_id == dataset.id).order_by(Document.position.asc()).first()
        document.status = DocumentStatus.COMPLETED
        document.enabled = True
        document.disabled_at = None
        db.session.commit()

        list_resp = client.get(f"/datasets/{dataset.id}/documents", query_string={"search_word": "一号"})
        detail_resp = client.get(f"/datasets/{dataset.id}/documents/{document.id}")
        assert list_resp.json.get("code") == HttpCode.SUCCESS
        assert len(list_resp.json["data"]["list"]) == 1
        assert detail_resp.json.get("data")["id"] == str(document.id)

        monkeypatch.setattr("internal.service.document_service.update_document_enabled.delay", lambda document_id: None)
        document_service = get_handler(app, "llmops.update_document_enabled").document_service
        monkeypatch.setattr(document_service, "redis_client", DummyRedis())

        name_resp = client.post(f"/datasets/{dataset.id}/documents/{document.id}/name", json={"name": "重命名文档.md"})
        enabled_resp = client.post(f"/datasets/{dataset.id}/documents/{document.id}/enabled", json={"enabled": False})
        status_resp = client.get(f"/datasets/{dataset.id}/documents/batch/{document.batch}")
        assert name_resp.json.get("code") == HttpCode.SUCCESS
        assert enabled_resp.json.get("code") == HttpCode.SUCCESS
        assert status_resp.json.get("code") == HttpCode.SUCCESS

        monkeypatch.setattr("internal.service.document_service.delete_document.delay", lambda dataset_id, document_id: None)
        delete_resp = client.post(f"/datasets/{dataset.id}/documents/{document.id}/delete")
        assert delete_resp.json.get("code") == HttpCode.SUCCESS
        assert db.session.query(Document).get(document.id) is None

    def test_segment_endpoints(self, client, app, db, monkeypatch):
        ensure_test_account(db)
        ensure_test_token(client)
        dataset = create_dataset(db)
        document = create_document(db, dataset.id)

        segment_service = get_handler(app, "llmops.create_segment").segment_service
        monkeypatch.setattr(segment_service, "redis_client", DummyRedis())
        monkeypatch.setattr(segment_service, "jieba_service", SimpleNamespace(extract_keywords=lambda content, top_k: ["自动关键词"]))
        monkeypatch.setattr(
            segment_service,
            "embeddings_service",
            SimpleNamespace(calculate_token_count=lambda content: 8, embeddings=SimpleNamespace(embed_query=lambda content: [0.1, 0.2])),
        )
        monkeypatch.setattr(
            segment_service,
            "keyword_table_service",
            SimpleNamespace(add_keyword_table_from_ids=lambda dataset_id, ids: None, delete_keyword_table_from_ids=lambda dataset_id, ids: None),
        )
        monkeypatch.setattr(
            segment_service,
            "vector_database_service",
            SimpleNamespace(vector_store=DummyVectorStore(), collection=DummyVectorCollection()),
        )

        create_resp = client.post(f"/datasets/{dataset.id}/documents/{document.id}/segments", json={
            "content": "新建片段内容",
            "keywords": [],
        })
        assert create_resp.status_code == 200
        assert create_resp.json.get("code") == HttpCode.SUCCESS

        segment = db.session.query(Segment).filter_by(document_id=document.id).one()
        list_resp = client.get(f"/datasets/{dataset.id}/documents/{document.id}/segments")
        detail_resp = client.get(f"/datasets/{dataset.id}/documents/{document.id}/segments/{segment.id}")
        update_resp = client.post(f"/datasets/{dataset.id}/documents/{document.id}/segments/{segment.id}", json={
            "content": "更新后的片段内容",
            "keywords": [],
        })
        enabled_resp = client.post(f"/datasets/{dataset.id}/documents/{document.id}/segments/{segment.id}/enabled", json={"enabled": False})
        delete_resp = client.post(f"/datasets/{dataset.id}/documents/{document.id}/segments/{segment.id}/delete")

        assert list_resp.json.get("code") == HttpCode.SUCCESS
        assert detail_resp.json.get("data")["id"] == str(segment.id)
        assert update_resp.json.get("code") == HttpCode.SUCCESS
        assert enabled_resp.json.get("code") == HttpCode.SUCCESS
        assert delete_resp.json.get("code") == HttpCode.SUCCESS
        assert db.session.query(Segment).get(segment.id) is None

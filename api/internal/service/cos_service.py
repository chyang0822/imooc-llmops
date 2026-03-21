#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/8/12 10:50
@Author  : thezehui@gmail.com
@File    : cos_service.py
"""
import hashlib
import os
import uuid
from dataclasses import dataclass
from datetime import datetime

from injector import inject
from qcloud_cos import CosS3Client, CosConfig
from werkzeug.datastructures import FileStorage

from internal.entity.upload_file_entity import ALLOWED_IMAGE_EXTENSION, ALLOWED_DOCUMENT_EXTENSION
from internal.exception import FailException
from internal.model import UploadFile, Account
from .upload_file_service import UploadFileService


@inject
@dataclass
class CosService:
    """腾讯云cos对象存储服务"""
    upload_file_service: UploadFileService

    def upload_file(self, file: FileStorage, only_image: bool, account: Account) -> UploadFile:
        """上传文件，优先使用腾讯云COS，未配置时回退到本地存储"""
        # 1.提取文件扩展名并检测是否可以上传
        filename = file.filename
        extension = filename.rsplit(".", 1)[-1] if "." in filename else ""
        if extension.lower() not in (ALLOWED_IMAGE_EXTENSION + ALLOWED_DOCUMENT_EXTENSION):
            raise FailException(f"该.{extension}扩展的文件不允许上传")
        elif only_image and extension.lower() not in ALLOWED_IMAGE_EXTENSION:
            raise FailException(f"该.{extension}扩展的文件不支持上传，请上传正确的图片")

        # 2.生成随机文件名
        random_filename = str(uuid.uuid4()) + "." + extension
        now = datetime.now()
        upload_filename = f"{now.year}/{now.month:02d}/{now.day:02d}/{random_filename}"

        # 3.流式读取上传数据
        file_content = file.stream.read()

        # 4.判断是否配置了COS密钥，选择上传方式
        if os.getenv("COS_SECRET_ID") and os.getenv("COS_SECRET_KEY"):
            # 使用腾讯云COS上传
            try:
                client = self.get_client()
                bucket = self.get_bucket()
                client.put_object(bucket, file_content, upload_filename)
            except Exception as e:
                raise FailException("上传文件到COS失败，请稍后重试")
        else:
            # 回退到本地存储
            upload_filename = self._save_to_local(file_content, upload_filename)

        # 5.创建upload_file记录
        return self.upload_file_service.create_upload_file(
            account_id=account.id,
            name=filename,
            key=upload_filename,
            size=len(file_content),
            extension=extension,
            mime_type=file.mimetype,
            hash=hashlib.sha3_256(file_content).hexdigest(),
        )

    @classmethod
    def _save_to_local(cls, file_content: bytes, upload_filename: str) -> str:
        """将文件保存到本地 storage/uploads 目录"""
        # 以项目根目录下的 storage/uploads 为基础目录
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "storage", "uploads")
        full_path = os.path.join(base_dir, upload_filename)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(file_content)
        return upload_filename

    def download_file(self, key: str, target_file_path: str):
        """下载cos云端的文件到本地的指定路径"""
        client = self.get_client()
        bucket = self.get_bucket()

        client.download_file(bucket, key, target_file_path)

    @classmethod
    def get_file_url(cls, key: str) -> str:
        """根据传递的cos云端key获取图片的实际URL地址"""
        # 如果未配置COS密钥，返回本地文件访问URL
        if not os.getenv("COS_SECRET_ID") or not os.getenv("COS_SECRET_KEY"):
            return f"http://127.0.0.1:5001/static/uploads/{key}"

        cos_domain = os.getenv("COS_DOMAIN")

        if not cos_domain:
            bucket = os.getenv("COS_BUCKET")
            scheme = os.getenv("COS_SCHEME")
            region = os.getenv("COS_REGION")
            cos_domain = f"{scheme}://{bucket}.cos.{region}.myqcloud.com"

        return f"{cos_domain}/{key}"

    @classmethod
    def get_client(cls) -> CosS3Client:
        """获取腾讯云cos对象存储客户端"""
        conf = CosConfig(
            Region=os.getenv("COS_REGION"),
            SecretId=os.getenv("COS_SECRET_ID"),
            SecretKey=os.getenv("COS_SECRET_KEY"),
            Token=None,
            Scheme=os.getenv("COS_SCHEME", "https")
        )
        return CosS3Client(conf)

    @classmethod
    def get_bucket(cls) -> str:
        """获取存储桶的名字"""
        return os.getenv("COS_BUCKET")

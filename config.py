import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import re

load_dotenv()

class DomainInput(BaseModel):
    domain: str = Field(..., min_length=3, max_length=100, 
                       description="研究领域名称，如'量子计算'")
    years: str = Field("2020-2024", 
                      description="年份范围，如'2018-2023'")
    paper_count: int = Field(5, ge=1, le=20, 
                            description="检索论文数量")
    temperature: float = Field(0.7, ge=0.1, le=2.0, 
                             description="LLM温度参数")

    @field_validator('domain')
    def validate_domain(cls, v):
        if not re.match(r'^[\w\s\-\.\u4e00-\u9fa5]+$', v):
            raise ValueError('领域名称包含非法字符')
        return v.strip()

class Paper(BaseModel):
    title: str
    authors: List[str]
    year: int
    abstract: str
    url: str
    citations: int

class ReviewOutput(BaseModel):
    overview: str
    key_papers: List[Paper]
    trends: str
    challenges: str
    future_directions: str
    
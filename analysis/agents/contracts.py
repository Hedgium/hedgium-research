from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AnalystInput(BaseModel):
    symbol: str
    company_name: str
    as_of_date: str
    payload: dict[str, Any] = Field(default_factory=dict)


class AnalystOutput(BaseModel):
    stance: str = "neutral"
    confidence: float = 0.0
    bullets: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    raw_summary: str = ""


class MasterInput(BaseModel):
    symbol: str
    company_name: str
    as_of_date: str
    predictions: dict[str, Any] = Field(default_factory=dict)
    risk: dict[str, Any] = Field(default_factory=dict)
    technical: AnalystOutput = Field(default_factory=AnalystOutput)
    fundamental: AnalystOutput = Field(default_factory=AnalystOutput)
    news: AnalystOutput = Field(default_factory=AnalystOutput)
    governance: AnalystOutput = Field(default_factory=AnalystOutput)


class MasterOutput(BaseModel):
    key_positive_factors: list[str] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)
    holding_outlook: dict[str, Any] = Field(default_factory=dict)
    news_summary: dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""

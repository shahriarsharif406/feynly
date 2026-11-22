"""Pydantic models shared across the app."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Status = Literal["correct", "partial", "missing", "misconception"]
Confidence = Literal["low", "medium", "high"]
Mode = Literal["concept", "code"]
Lang = Literal["en", "bn"]


class LoopInput(BaseModel):
    mode: Mode
    topic: Optional[str] = None
    explanation: str
    error_text: Optional[str] = None
    code_snippet: Optional[str] = None
    output_lang: Lang = "en"


class Concept(BaseModel):
    id: str
    label: str
    expected_idea: str
    status: Status
    evidence_quote: str = ""
    reason: str = ""
    confidence: Confidence = "medium"
    gap_headline: str = ""


class AnalyzeResult(BaseModel):
    input_ok: bool = True
    input_issue: Optional[Literal["too_short", "off_topic", "not_an_explanation", "unsafe"]] = None
    topic_title: str = ""
    detected_language: Literal["en", "bn", "mixed"] = "en"
    praise: str = ""
    concepts: list[Concept] = Field(default_factory=list)


class GapRef(BaseModel):
    gap_id: str
    concept_id: str
    kind: Status


class CodeFix(BaseModel):
    before: str
    after: str
    explanation: str = ""


class Lesson(BaseModel):
    gap_id: str
    concept_id: str
    title: str
    core_idea: str
    example: str
    you_said: str
    actually: str
    code_fix: Optional[CodeFix] = None
    check_yourself: str = ""


class LessonResult(BaseModel):
    lessons: list[Lesson]
    estimated_read_seconds: int = 60


class Rubric(BaseModel):
    full_credit: str
    partial_credit: str = ""
    key_terms: list[str] = Field(default_factory=list)


class RetestQuestion(BaseModel):
    q_id: str
    concept_id: str
    type: Literal["mcq", "short"]
    prompt: str
    options: list[str] = Field(default_factory=list)
    correct_option_index: Optional[int] = None
    rubric: Rubric


class RetestSet(BaseModel):
    questions: list[RetestQuestion]


class AIGrade(BaseModel):
    """Schema used for the AI response (no graded_by)."""

    q_id: str
    points: int
    feedback: str = ""
    matched_ideas: list[str] = Field(default_factory=list)


class GradeResult(BaseModel):
    grades: list[AIGrade]


class QuestionGrade(BaseModel):
    q_id: str
    points: int
    feedback: str = ""
    matched_ideas: list[str] = Field(default_factory=list)
    graded_by: Literal["local_mcq", "ai", "offline", "demo"] = "ai"


class ScoreBreakdown(BaseModel):
    rows: list[tuple[str, str, str, int]]  # (concept_id, label, status, points)
    total_points: int
    max_points: int
    score: int


class ProofRow(BaseModel):
    concept_id: str
    label: str
    before_status: Status
    before_quote: str = ""
    after_points: Optional[int] = None
    after_status: Optional[Status] = None
    answer_snippet: str = ""
    feedback: str = ""
    still_gap: bool = False


class DemoCase(BaseModel):
    demo_id: str
    mode: Mode
    language: Lang
    topic: Optional[str] = None
    input: LoopInput
    analysis: AnalyzeResult
    lesson: LessonResult
    retest: RetestSet
    sample_answers: dict[str, str]
    grades: dict[str, AIGrade] = Field(default_factory=dict)

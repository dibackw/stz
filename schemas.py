from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional


# === Схемы для тестов ===
class TestBase(BaseModel):
    title: str
    subject: str
    description: Optional[str] = None
    time_limit_minutes: int = 30
    passing_score: int = 70


class TestCreate(TestBase):
    pass


class TestResponse(TestBase):
    id: int
    question_count: int

    model_config = ConfigDict(from_attributes=True)


# === Схемы для вопросов ===
class AnswerOptionBase(BaseModel):
    id: int
    text: str


class QuestionBase(BaseModel):
    id: int
    question_text: str
    question_type: str = "single_choice"


class QuestionResponse(QuestionBase):
    options: List[AnswerOptionBase]

    model_config = ConfigDict(from_attributes=True)


# === Схемы для отправки ответов ===
class UserAnswer(BaseModel):
    question_id: int
    selected_option_id: Optional[int] = None  # Для текстовых вопросов может быть None
    text_answer: Optional[str] = None


class AnswerSubmission(BaseModel):
    student_name: str = Field(..., min_length=2, max_length=100)
    test_id: int
    answers: List[UserAnswer]


# === Схемы для результатов ===
class TestResultResponse(BaseModel):
    id: int
    student_name: str
    test_title: str
    score: int
    max_score: int
    percentage: float
    passed: bool
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResultSummary(BaseModel):
    student_name: str
    test_title: str
    percentage: float
    passed: bool
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Test(Base):
    __tablename__ = "tests"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    description = Column(String, nullable=True)
    question_count = Column(Integer, default=0)
    time_limit_minutes = Column(Integer, default=30)
    passing_score = Column(Integer, default=70)  # Проходной балл в %
    
    questions = relationship("Question", back_populates="test", cascade="all, delete-orphan")
    results = relationship("TestResult", back_populates="test")


class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    question_text = Column(String, nullable=False)
    question_type = Column(String, default="single_choice")  # single_choice, multiple_choice, text
    
    test = relationship("Test", back_populates="questions")
    options = relationship("AnswerOption", back_populates="question", cascade="all, delete-orphan")


class AnswerOption(Base):
    __tablename__ = "answer_options"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    option_text = Column(String, nullable=False)
    is_correct = Column(Boolean, default=False)
    
    question = relationship("Question", back_populates="options")


class TestResult(Base):
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String, nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    score = Column(Integer, nullable=False)  # Количество правильных ответов
    max_score = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)  # Результат в процентах
    passed = Column(Boolean, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    
    test = relationship("Test", back_populates="results")

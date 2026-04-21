from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

import database
import models
import schemas

# Создание таблиц при запуске
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="Система тестирования знаний",
    description="API для управления тестами и фиксации результатов",
    version="1.0.0"
)


# === Эндпоинты для работы с тестами ===

@app.get("/api/tests", response_model=List[schemas.TestResponse])
def get_tests(
    subject: Optional[str] = Query(None, description="Фильтр по предмету"),
    db: Session = Depends(database.get_db)
):
    """Получить список доступных тестов"""
    query = db.query(models.Test)
    if subject:
        query = query.filter(models.Test.subject.ilike(f"%{subject}%"))
    return query.all()


@app.get("/api/tests/{test_id}", response_model=schemas.TestResponse)
def get_test(test_id: int, db: Session = Depends(database.get_db)):
    """Получить информацию о конкретном тесте"""
    test = db.query(models.Test).filter(models.Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    return test


@app.get("/api/tests/{test_id}/questions", response_model=List[schemas.QuestionResponse])
def get_questions(test_id: int, db: Session = Depends(database.get_db)):
    """Получить вопросы теста (без указания правильных ответов)"""
    test = db.query(models.Test).filter(models.Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    
    questions = db.query(models.Question).filter(
        models.Question.test_id == test_id
    ).all()
    
    result = []
    for q in questions:
        options = db.query(models.AnswerOption).filter(
            models.AnswerOption.question_id == q.id
        ).all()
        result.append({
            "id": q.id,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "options": [{"id": opt.id, "text": opt.option_text} for opt in options]
        })
    return result


# === Эндпоинт для отправки ответов ===

@app.post("/api/submit", response_model=schemas.TestResultResponse)
def submit_answers(
    submission: schemas.AnswerSubmission,
    db: Session = Depends(database.get_db)
):
    """Принять ответы студента, проверить и сохранить результат"""
    
    # Проверка существования теста
    test = db.query(models.Test).filter(models.Test.id == submission.test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    
    # Проверка количества вопросов
    questions = db.query(models.Question).filter(
        models.Question.test_id == submission.test_id
    ).all()
    
    if len(questions) != len(submission.answers):
        raise HTTPException(
            status_code=400, 
            detail="Количество ответов не соответствует количеству вопросов"
        )
    
    # Подсчёт правильных ответов
    score = 0
    for user_answer in submission.answers:
        question = db.query(models.Question).filter(
            models.Question.id == user_answer.question_id
        ).first()
        
        if not question:
            continue
            
        if question.question_type == "single_choice":
            # Проверка выбора одного варианта
            correct_option = db.query(models.AnswerOption).filter(
                models.AnswerOption.question_id == user_answer.question_id,
                models.AnswerOption.is_correct == True
            ).first()
            
            if correct_option and user_answer.selected_option_id == correct_option.id:
                score += 1
                
        elif question.question_type == "multiple_choice":
            # Для множественного выбора нужна более сложная логика
            # (упрощённо: считаем правильным, если выбран хотя бы один верный)
            correct_options = db.query(models.AnswerOption).filter(
                models.AnswerOption.question_id == user_answer.question_id,
                models.AnswerOption.is_correct == True
            ).all()
            if user_answer.selected_option_id in [opt.id for opt in correct_options]:
                score += 1
    
    max_score = len(questions)
    percentage = round((score / max_score) * 100, 2) if max_score > 0 else 0
    passed = percentage >= test.passing_score
    
    # Сохранение результата
    result = models.TestResult(
        student_name=submission.student_name,
        test_id=submission.test_id,
        score=score,
        max_score=max_score,
        percentage=percentage,
        passed=passed
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    
    return {
        "id": result.id,
        "student_name": result.student_name,
        "test_title": test.title,
        "score": result.score,
        "max_score": result.max_score,
        "percentage": result.percentage,
        "passed": result.passed,
        "submitted_at": result.submitted_at
    }


# === Эндпоинты для просмотра результатов ===

@app.get("/api/results", response_model=List[schemas.ResultSummary])
def get_results(
    student_name: Optional[str] = Query(None, description="Фильтр по имени студента"),
    db: Session = Depends(database.get_db)
):
    """Получить историю результатов тестирования"""
    query = db.query(models.TestResult).join(models.Test)
    
    if student_name:
        query = query.filter(models.TestResult.student_name.ilike(f"%{student_name}%"))
    
    query = query.order_by(models.TestResult.submitted_at.desc())
    
    results = query.all()
    return [
        {
            "student_name": r.student_name,
            "test_title": r.test.title,
            "percentage": r.percentage,
            "passed": r.passed,
            "submitted_at": r.submitted_at
        }
        for r in results
    ]


@app.get("/api/results/{student_name}", response_model=List[schemas.TestResultResponse])
def get_student_results(student_name: str, db: Session = Depends(database.get_db)):
    """Получить детальные результаты конкретного студента"""
    results = db.query(models.TestResult).join(models.Test).filter(
        models.TestResult.student_name.ilike(f"%{student_name}%")
    ).order_by(models.TestResult.submitted_at.desc()).all()
    
    return [
        {
            "id": r.id,
            "student_name": r.student_name,
            "test_title": r.test.title,
            "score": r.score,
            "max_score": r.max_score,
            "percentage": r.percentage,
            "passed": r.passed,
            "submitted_at": r.submitted_at
        }
        for r in results
    ]


# === Корневой эндпоинт ===

@app.get("/")
def root():
    """Информация о сервисе"""
    return {
        "service": "Система тестирования знаний",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "tests": "/api/tests",
            "questions": "/api/tests/{id}/questions",
            "submit": "/api/submit (POST)",
            "results": "/api/results"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

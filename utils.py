"""Вспомогательные функции для бизнес-логики."""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


def parse_date(d_str):
    """Безопасный парсинг даты из строки."""
    if not d_str:
        return datetime.now().date()
    
    # Пробуем несколько форматов
    for fmt in ('%Y-%m-%d', '%d.%m.%Y'):
        try:
            return datetime.strptime(str(d_str), fmt).date()
        except (ValueError, TypeError):
            continue
    
    # Если ничего не подошло, возвращаем сегодняшнюю дату
    return datetime.now().date()


def calculate_max_grade(student_marks_dict, target_lesson, all_lessons):
    """Рассчитывает максимально возможный балл с учетом просрочек.
    
    Args:
        student_marks_dict: словарь {lesson_id: Mark} для студента
        target_lesson: урок, для которого считаем макс. балл
        all_lessons: список всех уроков группы (отсортированный по дате)
    
    Returns:
        int: максимальный балл (5, 4 или 3)
    """
    try:
        target_idx = all_lessons.index(target_lesson)
    except ValueError:
        return 5
    
    today = datetime.now().date()
    target_date = parse_date(str(target_lesson.date))
    
    # Если урок еще не прошел, макс. балл = 5
    if target_date > today:
        return 5
    
    # Считаем количество "пропущенных шансов" (уроков после целевого)
    passed_chances = 0
    for i in range(target_idx + 1, len(all_lessons)):
        next_lesson = all_lessons[i]
        next_date = parse_date(str(next_lesson.date))
        
        # Если следующий урок еще не прошел, останавливаемся
        if next_date > today:
            break
        
        # Проверяем, была ли оценка или справка на этом уроке
        mark = student_marks_dict.get(next_lesson.id)
        if mark and mark.status == 'sick':
            continue  # Справка не считается пропуском
        
        passed_chances += 1
    
    # Логика снижения балла
    if passed_chances <= 1:
        return 5
    elif passed_chances == 2:
        return 4
    else:
        return 3


def get_real_subgroup(student, lesson_date_str):
    """Определяет подгруппу студента на конкретную дату с учетом истории переводов.
    
    Args:
        student: объект Student
        lesson_date_str: дата урока в формате строки
    
    Returns:
        int: номер подгруппы (1 или 2)
    """
    hist = getattr(student, 'history', [])
    if not hist:
        return student.subgroup
    
    # Сортируем историю по дате (от новых к старым)
    hist = sorted(hist, key=lambda x: x['date'], reverse=True)
    
    # Ищем последнюю запись ПЕРЕД или РАВНУЮ дате урока
    for record in hist:
        if record['date'] <= str(lesson_date_str):
            return record['val']
    
    # Если записей до этой даты нет, берем самую старую
    return hist[-1]['val'] if hist else student.subgroup


def hash_password(password):
    """Хеширует пароль."""
    return generate_password_hash(password)


def verify_password(password_hash, password):
    """Проверяет пароль."""
    return check_password_hash(password_hash, password)

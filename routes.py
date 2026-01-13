from flask import Blueprint, render_template, redirect, url_for, request, jsonify, make_response
from flask_login import login_user, login_required, logout_user, current_user
from database import db
from models import User, Group, Student, Lesson, Mark, Plan, Announcement
import json
from datetime import datetime

main_bp = Blueprint('main', __name__)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def render_app(content_html, is_admin=False):
    js_flag = "true" if is_admin else "false"
    return render_template('base.html', content=content_html, js_flag=js_flag)

def parse_date(d_str):
    try: return datetime.strptime(d_str, '%Y-%m-%d').date()
    except: 
        try: return datetime.strptime(d_str, '%d.%m.%Y').date()
        except: return datetime.now().date()

def calculate_max_grade(student, target_lesson, all_lessons):
    try: target_idx = all_lessons.index(target_lesson)
    except ValueError: return 5
    today = datetime.now().date()
    if parse_date(target_lesson.date) > today: return 5
    passed_chances = 0
    for i in range(target_idx + 1, len(all_lessons)):
        next_l = all_lessons[i]
        if parse_date(next_l.date) > today: break
        mark = next((m for m in student.marks if m.lesson_id == next_l.id), None)
        if mark and mark.status == 'sick': continue 
        passed_chances += 1
    if passed_chances <= 1: return 5
    elif passed_chances == 2: return 4
    else: return 3

# --- МАРШРУТЫ ---

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin': return redirect(url_for('main.admin_panel'))
        else: return redirect(url_for('main.group_view', group_id=current_user.access_group))
    return redirect(url_for('main.login'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.get(request.form.get('id'))
        if user and user.password == request.form.get('password'):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            return render_app("""
                <div style="display:flex; justify-content:center; align-items:center; height:80vh;">
                    <div style="width:100%; max-width:400px; text-align:center;">
                        <h1 style="color:var(--primary); margin-bottom:30px;">Вход в систему</h1>
                        <form method="POST" style="background:white; padding:40px; border-radius:24px; box-shadow:var(--shadow);">
                            <input class="inp" name="id" placeholder="Логин" required>
                            <input class="inp" type="password" name="password" placeholder="Пароль" required>
                            <button class="btn btn-prim" style="width:100%; justify-content:center;">Войти</button>
                        </form>
                    </div>
                </div>
            """)
    return render_app("""
        <div style="display:flex; justify-content:center; align-items:center; height:80vh;">
            <div style="width:100%; max-width:400px; text-align:center;">
                <h1 style="color:var(--primary); margin-bottom:30px;">Вход в систему</h1>
                <form method="POST" style="background:white; padding:40px; border-radius:24px; box-shadow:var(--shadow);">
                    <input class="inp" name="id" placeholder="Логин" required>
                    <input class="inp" type="password" name="password" placeholder="Пароль" required>
                    <button class="btn btn-prim" style="width:100%; justify-content:center;">Войти</button>
                </form>
            </div>
        </div>
    """)

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main_bp.route('/admin')
@login_required
def admin_panel():
    if current_user.role != 'admin': return "Access denied"
    
    groups = Group.query.all()
    total_students = Student.query.count()
    total_marks = Mark.query.filter(Mark.grade != None).count()
    avg_score = round(sum([m.grade for m in Mark.query.filter(Mark.grade != None).all()]) / total_marks, 2) if total_marks > 0 else 0

    # Стили для KPI карточек в стиле Lavender
    kpi_style = "background:white; padding:25px; border-radius:24px; box-shadow:var(--shadow); display:flex; flex-direction:column; justify-content:space-between; min-height:120px;"

    html = f"""
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:20px; margin-bottom:40px;">
        <div style="{kpi_style}">
            <div style="opacity:0.6; font-size:0.85rem; font-weight:700; text-transform:uppercase;">Группы</div>
            <div style="font-size:3.5rem; font-weight:800; color:var(--primary);">{len(groups)}</div>
        </div>
        <div style="{kpi_style}">
            <div style="opacity:0.6; font-size:0.85rem; font-weight:700; text-transform:uppercase;">Студенты</div>
            <div style="font-size:3.5rem; font-weight:800; color:var(--green-text);">{total_students}</div>
        </div>
        <div style="{kpi_style}">
            <div style="opacity:0.6; font-size:0.85rem; font-weight:700; text-transform:uppercase;">Средний балл</div>
            <div style="font-size:3.5rem; font-weight:800; color:var(--yellow-text);">{avg_score}</div>
        </div>
    </div>

    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
        <h2 style="margin:0; color:var(--text-main);">Учебные группы</h2>
        <button class="btn btn-prim" onclick="openNG()">+ Новая группа</button>
    </div>
    
    <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap:25px;">
    """
    
    for g in groups:
        user_info = User.query.get(g.id)
        pwd = user_info.password if user_info else ""
        total_h = sum(int(x['hours']) for p in g.plans for x in p.get_data())
        passed_h = sum(l.hours for l in g.lessons if parse_date(l.date) <= datetime.now().date())
        perc = int(passed_h / total_h * 100) if total_h > 0 else 0
        
        html += f"""
        <div class="group-card" style="min-height:280px;">
            <button onclick="openGSet('{g.id}', '{g.subject}', '{pwd}')" class="btn" style="position:absolute; top:15px; right:15px; width:36px; height:36px; padding:0; justify-content:center; border-radius:50%; background:#F1F5F9; color:var(--text-muted);">⚙️</button>
            <div>
                <div style="margin-bottom:20px;">
                    <h3 style="margin:0; font-size:1.6rem; color:var(--text-main);">{g.id}</h3>
                    <div style="color:var(--text-muted); font-weight:600;">{g.subject}</div>
                </div>
                <div style="margin-bottom:25px;">
                    <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:var(--text-muted); margin-bottom:8px; font-weight:700;">
                        <span>Прогресс</span>
                        <span>{perc}%</span>
                    </div>
                    <div style="height:8px; width:100%; background:var(--bg-body); border-radius:4px; overflow:hidden;">
                        <div style="height:100%; width:{perc}%; background:var(--primary); border-radius:4px;"></div>
                    </div>
                </div>
            </div>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                <a href="{url_for('main.stats_view', group_id=g.id)}" class="btn" style="justify-content:center; text-decoration:none;">📊 Инфо</a>
                <a href="{url_for('main.group_view', group_id=g.id)}" class="btn btn-prim" style="justify-content:center; text-decoration:none;">Журнал →</a>
            </div>
        </div>
        """
    html += "</div>"
    return render_app(html, is_admin=True)

@main_bp.route('/group/<group_id>/stats')
@login_required
def stats_view(group_id):
    group = Group.query.get_or_404(group_id)
    students = group.students
    lessons = sorted(group.lessons, key=lambda l: parse_date(l.date))
    
    # Сбор данных
    grades_count = {5:0, 4:0, 3:0, 2:0}
    status_count = {'present':0, 'absent':0, 'sick':0}
    total_marks_count = 0
    student_ratings = []
    dates_labels = []
    dates_avg_values = []
    types_stats = {} 
    
    for s in students:
        s_grades = []
        s_presents = 0
        s_total_lessons = 0
        for m in s.marks:
            if m.grade: 
                grades_count[m.grade] = grades_count.get(m.grade, 0) + 1
                total_marks_count += 1
                s_grades.append(m.grade)
            if m.status: status_count[m.status] = status_count.get(m.status, 0) + 1
            if m.lesson_id: 
                s_total_lessons += 1
                if m.status in ['present', 'sick']: s_presents += 1
        s_avg = round(sum(s_grades)/len(s_grades), 2) if s_grades else 0
        s_att_perc = int(s_presents/s_total_lessons*100) if s_total_lessons > 0 else 0
        student_ratings.append({'name': s.name, 'avg': s_avg, 'att': s_att_perc})

    top_students = sorted(student_ratings, key=lambda x: x['avg'], reverse=True)[:5]
    
    for l in lessons:
        l_grades = [m.grade for m in l.marks if m.grade]
        if l_grades:
            l_avg = round(sum(l_grades) / len(l_grades), 2)
            dates_labels.append(l.date[5:]) 
            dates_avg_values.append(l_avg)
            if l.type not in types_stats: types_stats[l.type] = []
            types_stats[l.type].extend(l_grades)

    types_labels = list(types_stats.keys())
    types_values = []
    for t in types_labels:
        vals = types_stats[t]
        types_values.append(round(sum(vals)/len(vals), 2) if vals else 0)

    avg_total = round(sum([k*v for k,v in grades_count.items()]) / total_marks_count, 2) if total_marks_count > 0 else 0
    total_att_events = sum(status_count.values())
    att_perc_total = int((status_count['present'] + status_count['sick']) / total_att_events * 100) if total_att_events > 0 else 0

    html = f"""
    <style>
        .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: white; border-radius: 24px; padding: 25px; box-shadow: var(--shadow); display: flex; flex-direction: column; justify-content: space-between; }}
        .stat-val {{ font-size: 2.5rem; font-weight: 800; color: var(--text-main); margin: 10px 0; }}
        .stat-label {{ color: var(--text-muted); font-size: 0.9rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }}
        
        .charts-row {{ display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 20px; }}
        .chart-box {{ background: white; border-radius: 24px; padding: 25px; box-shadow: var(--shadow); }}
        
        .top-list {{ list-style: none; padding: 0; margin: 0; }}
        .top-item {{ display: flex; justify-content: space-between; align-items: center; padding: 15px 0; border-bottom: 1px solid var(--bg-body); }}
        .top-item:last-child {{ border-bottom: none; }}
        .top-name {{ font-weight: 700; color: var(--text-main); display: flex; align-items: center; gap: 12px; }}
        .top-score {{ background: var(--primary-bg); color: var(--primary); padding: 5px 12px; border-radius: 12px; font-weight: 800; }}
        .medal {{ width:30px; height:30px; display:flex; align-items:center; justify-content:center; background:var(--bg-body); border-radius:50%; font-size:1.2rem; }}
    </style>

    <div style="margin-bottom:20px;">
        <a href="{url_for('main.group_view', group_id=group_id)}" class="btn" style="display:inline-flex; text-decoration:none;">← Вернуться к журналу</a>
    </div>

    <div style="margin-bottom:40px;">
        <h1 style="margin:0; font-size: 2rem; color: var(--primary);">{group.id} <span style="color:var(--text-muted); font-weight:400;">/ Статистика</span></h1>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-label">Средний балл</div>
            <div class="stat-val" style="color:var(--primary);">{avg_total}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Посещаемость</div>
            <div class="stat-val" style="color:var(--green-text);">{att_perc_total}%</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Оценок</div>
            <div class="stat-val" style="color:var(--yellow-text);">{total_marks_count}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Студентов</div>
            <div class="stat-val" style="color:var(--purple-text);">{len(students)}</div>
        </div>
    </div>

    <div class="charts-row">
        <div class="chart-box">
            <h3 style="margin-top:0; color:var(--text-main);">📈 Динамика успеваемости</h3>
            <div style="height: 300px;"><canvas id="dynamicChart"></canvas></div>
        </div>
        <div class="chart-box">
            <h3 style="margin-top:0; color:var(--text-main);">🏆 Лидеры группы</h3>
            <ul class="top-list">
    """
    for idx, s in enumerate(top_students):
        medal = ["🥇", "🥈", "🥉", str(idx+1), str(idx+1)][idx]
        html += f"""<li class="top-item"><div class="top-name"><div class="medal">{medal}</div> {s['name']}</div><div class="top-score">{s['avg']}</div></li>"""
    
    html += f"""
            </ul>
        </div>
    </div>

    <div class="charts-row" style="grid-template-columns: 1fr 1fr 1fr;">
        <div class="chart-box">
            <h3 style="margin-top:0; font-size:1rem;">Распределение</h3>
            <div style="height: 200px; display:flex; justify-content:center;"><canvas id="gradesChart"></canvas></div>
        </div>
        <div class="chart-box">
            <h3 style="margin-top:0; font-size:1rem;">Посещения</h3>
            <div style="height: 200px; display:flex; justify-content:center;"><canvas id="statusChart"></canvas></div>
        </div>
        <div class="chart-box">
            <h3 style="margin-top:0; font-size:1rem;">По типам работ</h3>
            <div style="height: 200px; display:flex; justify-content:center;"><canvas id="typesChart"></canvas></div>
        </div>
    </div>
    
    <script>
        Chart.defaults.font.family = "'Nunito', sans-serif";
        Chart.defaults.color = '#94A3B8';

        new Chart(document.getElementById('dynamicChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps(dates_labels)},
                datasets: [{{
                    label: 'Ср. балл',
                    data: {json.dumps(dates_avg_values)},
                    borderColor: '#8B5C96',
                    backgroundColor: 'rgba(139, 92, 150, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: 'white',
                    pointBorderColor: '#8B5C96',
                    pointRadius: 6
                }}]
            }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{ y: {{ min: 2, max: 5, grid: {{ borderDash: [5, 5] }} }}, x: {{ grid: {{ display: false }} }} }}
            }}
        }});

        new Chart(document.getElementById('gradesChart'), {{
            type: 'bar',
            data: {{
                labels: ['5', '4', '3', '2'],
                datasets: [{{
                    data: [{grades_count[5]}, {grades_count[4]}, {grades_count[3]}, {grades_count[2]}],
                    backgroundColor: ['#4ADE80', '#8B5C96', '#FBBF24', '#F87171'],
                    borderRadius: 8
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ display: false }}, x: {{ grid: {{ display: false }} }} }} }}
        }});

        new Chart(document.getElementById('statusChart'), {{
            type: 'doughnut',
            data: {{
                labels: ['Был', 'Н', 'Спр'],
                datasets: [{{
                    data: [{status_count['present']}, {status_count['absent']}, {status_count['sick']}],
                    backgroundColor: ['#4ADE80', '#F87171', '#C084FC'],
                    borderWidth: 0
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, cutout: '70%', plugins: {{ legend: {{ position: 'right', labels: {{ usePointStyle: true, boxWidth: 8 }} }} }} }}
        }});

        new Chart(document.getElementById('typesChart'), {{
            type: 'radar',
            data: {{
                labels: {json.dumps(types_labels)},
                datasets: [{{
                    data: {json.dumps(types_values)},
                    backgroundColor: 'rgba(139, 92, 150, 0.2)',
                    borderColor: '#8B5C96',
                    pointBackgroundColor: '#8B5C96',
                    borderWidth: 2
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, scales: {{ r: {{ suggestMin: 2, suggestMax: 5, ticks: {{ display: false }} }} }}, plugins: {{ legend: {{ display: false }} }} }}
        }});
    </script>
    """
    return render_app(html, is_admin=(current_user.role=='admin'))

@main_bp.route('/group/<group_id>/board')
@login_required
def board_view(group_id):
    group = Group.query.get_or_404(group_id)
    annos = Announcement.query.filter_by(group_id=group_id).order_by(Announcement.is_important.desc(), Announcement.created_at.desc()).all()
    is_adm = (current_user.role == 'admin')
    
    html  ="""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:30px;">
        <div>
            <h1 style="margin:0; color:var(--text-main);">Доска объявлений</h1>
            <p style="color:var(--text-muted); margin:5px 0 0;">Группа {group.id}</p>
        </div>
        <div style="display:flex; gap:10px;">
            {'<button class="btn btn-prim" onclick="openAnno(\''+group.id+'\')">+ Новое</button>' if is_adm else ''}
            <a href="{url_for('main.group_view', group_id=group_id)}" class="btn" style="text-decoration:none;">← Журнал</a>
        </div>
    </div>
    
    <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap:20px;">
    """
    if not annos: html += "<p style='color:var(--text-muted);'>Объявлений пока нет.</p>"
    for a in annos:
        style = "background:#FFF1F2; border-left:5px solid var(--red);" if a.is_important else "background:white; border-left:5px solid var(--primary);"
        html += f"""
        <div style="{style} padding:20px; border-radius:16px; box-shadow:var(--shadow); position:relative;">
            <div style="font-size:0.8rem; color:var(--text-muted); margin-bottom:10px;">{a.created_at.strftime('%d.%m.%Y')}</div>
            <div style="white-space:pre-wrap; line-height:1.5; color:var(--text-main); font-weight:600;">{a.text}</div>
            {f'<button onclick="delAnno({a.id})" style="position:absolute; bottom:15px; right:15px; color:var(--red); border:none; background:transparent; cursor:pointer;">Удалить</button>' if is_adm else ''}
        </div>
        """
    html += "</div>"
    return render_app(html, is_admin=is_adm)

@main_bp.route('/group/<path:group_id>')
@login_required
def group_view(group_id):
    if current_user.role != 'admin' and current_user.access_group != group_id: return "Access denied"
    raw_sem = request.args.get('sem') or request.cookies.get(f'sem_{group_id}', '1')
    group = Group.query.get_or_404(group_id)
    students = sorted(group.students, key=lambda s: s.name)
    all_lessons = sorted(group.lessons, key=lambda l: parse_date(l.date))
    
    if raw_sem == 'all': lessons = all_lessons; sem_active = 'all'
    else: sem_active = int(raw_sem); lessons = [l for l in all_lessons if l.semester == sem_active]
    
    plan_data = []
    if sem_active == 'all': [plan_data.extend(p.get_data()) for p in group.plans]
    else: 
        p = Plan.query.filter_by(group_id=group_id, semester=sem_active).first()
        if p: plan_data = p.get_data()
    
    passed_hours = sum(l.hours for l in lessons if parse_date(l.date) <= datetime.now().date())
    total_h = sum(int(x['hours']) for x in plan_data)
    prog = int((passed_hours / total_h * 100)) if total_h > 0 else 0
    is_adm = (current_user.role == 'admin')
    
    # JSON плана для редактирования
    plan_edit = Plan.query.filter_by(group_id=group_id, semester=(1 if sem_active=='all' else sem_active)).first()
    plan_js = json.dumps(plan_edit.get_data() if plan_edit else []).replace('"', '&quot;')
    
    nav = f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:30px; flex-wrap:wrap; gap:15px;">
        <div style="display:flex; align-items:center; gap:20px; flex-wrap:wrap;">
            <div>
                <h1 style="margin:0; font-size:2rem; color:var(--text-main);">Группа {group.id}</h1>
                <div style="font-size:1rem; color:var(--text-muted);">{group.subject}</div>
            </div>
            
            <div class="sem-toggle">
                <a href="?sem=1" class="sem-btn {'active' if sem_active==1 else ''}" style="text-decoration:none;">1 Сем</a>
                <a href="?sem=2" class="sem-btn {'active' if sem_active==2 else ''}" style="text-decoration:none;">2 Сем</a>
                <a href="?sem=all" class="sem-btn {'active' if sem_active=='all' else ''}" style="text-decoration:none;">Весь год</a>
            </div>
        </div>
        
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
            <a href="{url_for('main.stats_view', group_id=group.id)}" class="btn" style="text-decoration:none; white-space:nowrap;">📊 Статистика</a>
            <a href="{url_for('main.board_view', group_id=group.id)}" class="btn" style="text-decoration:none; white-space:nowrap;">📋 Объявления</a>
            <a href="{url_for('main.index')}" class="btn" style="text-decoration:none; white-space:nowrap;">Назад</a>
            {f'''<button class="btn" onclick="openP('{group.id}', '{plan_js}')">План</button><button class="btn" onclick="openS('{group.id}')">+ Студент</button><button class="btn btn-prim" onclick="openL('{group.id}')">+ Занятие</button>''' if is_adm else ''}
        </div>
    </div>
    """


    prog_bar = f"""
    <div style="background:white; padding:20px; border-radius:24px; box-shadow:var(--shadow); margin-bottom:30px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:10px; font-weight:700; color:var(--text-muted);">
            <span>Прогресс курса: {passed_hours} / {total_h} ч.</span>
            <span style="color:var(--primary);">{prog}%</span>
        </div>
        <div style="height:10px; width:100%; background:var(--bg-body); border-radius:5px; overflow:hidden;">
            <div style="width:{prog}%; background:var(--primary); height:100%;"></div>
        </div>
    </div>
    """
    
    filters = """<div style="display:flex; gap:10px; margin-bottom:20px;">
        <button class="btn sg-o active" id="sgall" onclick="filterSG('all')" style="background:var(--primary); color:white;">Все</button>
        <button class="btn sg-o" id="sg1" onclick="filterSG('1')">Подгруппа 1</button>
        <button class="btn sg-o" id="sg2" onclick="filterSG('2')">Подгруппа 2</button>
    </div>"""

    tbl = """<div class="table-wrap"><table><thead><tr><th class="fixed-c" style="min-width:200px; z-index:30;">ФИО Студента</th>"""
    for l in lessons:
        title = l.type[:3] + (f" №{l.number}" if l.number else "")
        del_b = f'<div onclick="delCol(\'{group.id}\',\'{l.id}\')" style="position:absolute; top:2px; right:2px; color:var(--red); cursor:pointer; font-size:14px; font-weight:bold;">×</div>' if is_adm else ''
        tbl += f"<th class='col-c' data-sg='{l.subgroup_target}' style='text-align:center; min-width:70px; position:relative; cursor:pointer;' title='{l.type}'><div style='font-size:0.75rem; opacity:0.7;'>{l.date[5:]}</div><div style='font-size:0.85rem; color:var(--text-main);'>{title}</div>{del_b}</th>"
    tbl += "<th class='fixed-c' style='text-align:center; min-width:70px; background:#F9FAFB;'>Итог</th></tr></thead><tbody>"

    for s in students:
        del_s = f"<span onclick='delSt(\"{group.id}\",\"{s.id}\")' style='color:var(--red); cursor:pointer; margin-left:10px; font-weight:bold;'>×</span>" if is_adm else ""
        tbl += f"<tr class='st-row' data-sg='{s.subgroup}'><td class='fixed-c' style='font-weight:700; color:var(--text-main);'>{s.name} {del_s}</td>"
        
        sum_grades = 0; count_grades = 0
        for l in lessons:
            m = next((x for x in s.marks if x.lesson_id==l.id), None)
            is_bl = (l.subgroup_target!=0 and l.subgroup_target!=s.subgroup)
            
            bg_cls = ""; html_mk = ""
            if not is_bl:
                status = m.status if m else 'present'
                if status == 'sick': bg_cls = "cell-sick"
                elif status == 'absent': bg_cls = "cell-absent"
                else: bg_cls = "cell-present"

                if m and m.grade:
                    old_html = f"<div class='old-g'>{m.old_grade}</div>" if m.old_grade else ""
                    html_mk = f"<div class='mark-circle v{m.grade}'>{m.grade}{old_html}</div>"
                    sum_grades += m.grade; count_grades += 1
                elif m and m.status == 'sick': html_mk = "<span style='font-size:0.8rem; font-weight:800; color:var(--purple-text);'>Спр</span>"
                elif m and m.status == 'absent': html_mk = "<span style='font-size:0.8rem; font-weight:800; color:var(--red-text);'>Н</span>"
                else: html_mk = "<span style='color:var(--green-text); font-size:1.5rem;'>•</span>"
                
                safe_json = json.dumps({'status': status, 'grade': m.grade if m else None}).replace('"', '&quot;')
                max_g = calculate_max_grade(s, l, lessons)
                clk = f"onclick=\"openGrade('{group.id}', '{s.id}', '{l.id}', '{s.name}', '{l.date}', '{l.type}', '{safe_json}', {str(is_bl).lower()}, {max_g})\""
            else: clk = ""; bg_cls="background:var(--bg-body);"
            
            tbl += f"<td class='{bg_cls}' data-sg='{l.subgroup_target}' style='text-align:center; cursor:pointer;' {clk}>{html_mk}</td>"
        
        final_html = f"<div style='background:var(--primary-bg); color:var(--primary); padding:4px 8px; border-radius:8px; font-weight:800; display:inline-block;'>{int(sum_grades/count_grades+0.5)} <span style='font-size:0.7em; opacity:0.8;'>({sum_grades/count_grades:.1f})</span></div>" if count_grades>0 else "-"
        tbl += f"<td class='fixed-c' style='text-align:center; background:white;'>{final_html}</td></tr>"
    tbl += "</tbody></table></div>"

    resp = make_response(render_app(nav + prog_bar + filters + tbl, is_admin=is_adm))
    resp.set_cookie(f'sem_{group_id}', str(raw_sem))
    return resp

# --- API ---

@main_bp.route('/api/add_anno', methods=['POST'])
@login_required
def add_anno():
    gid = request.form.get('gid'); text = request.form.get('text')
    if gid and text: db.session.add(Announcement(group_id=gid, text=text, is_important=(True if request.form.get('is_important') else False))); db.session.commit(); return redirect(url_for('main.board_view', group_id=gid))
    return "Err"

@main_bp.route('/api/delete_anno', methods=['POST'])
@login_required
def delete_anno():
    if current_user.role!='admin': return "Deny", 403
    a = Announcement.query.get(request.json['aid'])
    if a: db.session.delete(a); db.session.commit()
    return jsonify({'ok':True})

@main_bp.route('/api/save', methods=['POST'])
@login_required
def save_grade():
    if current_user.role != 'admin': return jsonify({'error':'denied'}), 403
    data = request.json
    m = Mark.query.filter_by(student_id=data['sid'], lesson_id=data['cid']).first()
    if not m: m = Mark(student_id=data['sid'], lesson_id=data['cid']); db.session.add(m)
    
    if data['gr'] is not None and m.grade is not None and m.grade != data['gr']: m.old_grade = m.grade
    if data['gr'] is None: m.old_grade = None

    m.status = data['st']; m.grade = data['gr']; db.session.commit()
    return jsonify({'ok':True})

@main_bp.route('/api/add_group', methods=['POST'])
@login_required
def add_group():
    n = request.form.get('name'); s = request.form.get('subject')
    if n and not Group.query.get(n):
        db.session.add(Group(id=n, subject=s))
        db.session.add(User(id=n, password=request.form.get('password'), role='user', access_group=n))
        db.session.add(Plan(group_id=n, semester=1)); db.session.add(Plan(group_id=n, semester=2))
        db.session.commit()
    return redirect(url_for('main.admin_panel'))

@main_bp.route('/api/update_group', methods=['POST'])
@login_required
def update_group():
    if current_user.role!='admin': return "Deny", 403
    g = Group.query.get(request.form.get('gid')); u = User.query.get(request.form.get('gid'))
    if g and u: g.subject = request.form.get('subject'); u.password = request.form.get('password'); db.session.commit()
    return redirect(url_for('main.admin_panel'))

@main_bp.route('/api/delete_group', methods=['POST'])
@login_required
def delete_group():
    if current_user.role!='admin': return "Deny", 403
    gid = request.form.get('gid')
    g = Group.query.get(gid); u = User.query.get(gid)
    if g: db.session.delete(g)
    if u: db.session.delete(u)
    db.session.commit()
    return redirect(url_for('main.admin_panel'))

@main_bp.route('/api/add_student', methods=['POST'])
@login_required
def add_student():
    gid = request.form.get('gid'); name = request.form.get('name')
    if gid and name: db.session.add(Student(name=name, subgroup=int(request.form.get('subgroup')), group_id=gid)); db.session.commit(); return redirect(url_for('main.group_view', group_id=gid))
    return "Err"

@main_bp.route('/api/add_column', methods=['POST'])
@login_required
def add_column():
    gid = request.form.get('gid'); raw_sem = request.cookies.get(f'sem_{gid}', '1')
    sem = 1 if raw_sem == 'all' else int(raw_sem)
    if gid:
        num = request.form.get('number')
        db.session.add(Lesson(group_id=gid, date=request.form.get('date'), type=request.form.get('type'), hours=int(request.form.get('hours')), subgroup_target=int(request.form.get('subgroup_target')), semester=sem, number=int(num) if num else None))
        db.session.commit()
        return redirect(url_for('main.group_view', group_id=gid))
    return "Err"

@main_bp.route('/api/update_plan', methods=['POST'])
@login_required
def update_plan():
    gid = request.form.get('gid'); raw_sem = request.cookies.get(f'sem_{gid}', '1')
    sem = 1 if raw_sem == 'all' else int(raw_sem)
    p = Plan.query.filter_by(group_id=gid, semester=sem).first()
    if not p: p = Plan(group_id=gid, semester=sem); db.session.add(p)
    p.data = request.form.get('plan_data'); db.session.commit()
    return redirect(url_for('main.group_view', group_id=gid))

@main_bp.route('/api/delete_column', methods=['POST'])
@login_required
def delete_column():
    if current_user.role!='admin': return "Deny", 403
    l = Lesson.query.get(request.json['cid'])
    if l: db.session.delete(l); db.session.commit()
    return jsonify({'ok':True})

@main_bp.route('/api/delete_student', methods=['POST'])
@login_required
def delete_student():
    if current_user.role!='admin': return "Deny", 403
    s = Student.query.get(request.json['sid'])
    if s: db.session.delete(s); db.session.commit()
    return jsonify({'ok':True})

import os, json, markdown
from datetime import date, datetime, timedelta, time
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Exercise, WorkoutLog, MoodEntry, JournalEntry, SymptomEntry, \
    ProgramProgress, Article, CommunityPost, CommunityComment, SYMPTOM_TYPES, SYMPTOM_LABELS, \
    IsochronicTone, ToneSession, License, check_user_has_active_license, Subscriber, SleepLog
from seed_data import seed_database
import gumroad_utils
import decoder_data
import breathing_data

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'menopause-wellness-secret-key-2025')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///menopause_wellness.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create database tables and seed on startup
with app.app_context():
    db.create_all()
    seed_database(db)

# ─── Article & Exercise Migration (add missing items without clearing DB) ─
def migrate_missing_articles():
    """Check each article in seed data by slug — insert any that are missing.
    This handles the case where new articles were added to seed_data.py
    after the database was already seeded (seed_database skips if count > 0)."""
    from seed_data import ARTICLES
    added = 0
    for art_data in ARTICLES:
        slug = art_data.get('slug')
        if slug and not Article.query.filter_by(slug=slug).first():
            article = Article(**art_data)
            db.session.add(article)
            added += 1
    if added:
        db.session.commit()
        print(f'Migrated {added} missing article(s) into the database.')

def migrate_missing_exercises():
    """Check each exercise in seed data by order — insert any that are missing.
    Same logic as articles: keeps old data, only adds new exercises."""
    from seed_data import EXERCISES
    added = 0
    for ex_data in EXERCISES:
        order = ex_data.get('order')
        if order and not Exercise.query.filter_by(order=order).first():
            exercise = Exercise(**ex_data)
            db.session.add(exercise)
            added += 1
    if added:
        db.session.commit()
        print(f'Migrated {added} missing exercise(s) into the database.')

def migrate_missing_tones():
    """Check each tone preset — insert any that are not in the DB yet."""
    from models import TONES_PRESETS, TONES_LABELS, TONES_FREQUENCIES
    added = 0
    colors = ['#7c6ff7', '#d4436b', '#2ecc71', '#f1c40f',
              '#e67e22', '#9b59b6', '#1abc9c', '#3498db',
              '#2ecc71', '#e91e63', '#ff6f61', '#00bcd4', '#ffd54f']
    icons = ['💤', '🧘', '🌊', '🧠', '⚡', '🌤️', '🕯️', '🌅',
             '🌿', '☕', '🌸', '🩹', '✨']
    for i, preset_id in enumerate(TONES_PRESETS):
        if not IsochronicTone.query.filter_by(preset_id=preset_id).first():
            freq = TONES_FREQUENCIES[preset_id]
            tone = IsochronicTone(
                preset_id=preset_id,
                name=TONES_LABELS[preset_id],
                description=freq['description'],
                carrier_freq=freq['carrier'],
                beat_freq=freq['beat'],
                brainwave_label=freq['brainwave'],
                icon=icons[i] if i < len(icons) else '🎵',
                color=colors[i] if i < len(colors) else '#d4436b',
                duration_min=15
            )
            db.session.add(tone)
            added += 1
    if added:
        db.session.commit()
        print(f'Migrated {added} missing tone(s) into the database.')

with app.app_context():
    migrate_missing_articles()
    migrate_missing_exercises()
    migrate_missing_tones()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─── Context Processor ────────────────────────────────────────────────
@app.context_processor
def inject_globals():
    return {
        'now': datetime.utcnow(),
        'today': date.today(),
        'symptom_types': SYMPTOM_TYPES,
        'symptom_labels': SYMPTOM_LABELS,
    }


# ─── Auth Routes ──────────────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        license_key = request.form.get('license_key', '').strip()
        if not username or not email or not password or not license_key:
            flash('All fields are required, including your license key.', 'danger')
            return render_template('register.html')
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html')

        # Verify Gumroad license key (skip for admin email)
        admin_emails = os.environ.get('ADMIN_EMAILS', '').lower().split(',')
        is_admin = email.lower() in [e.strip() for e in admin_emails if e.strip()]
        if not is_admin:
            gumroad_resp = gumroad_utils.verify_license(license_key)
            if not gumroad_resp['success']:
                flash(f'License key invalid: {gumroad_resp.get("error", "Unknown error")}', 'danger')
                return render_template('register.html')
        else:
            gumroad_resp = {'success': True, 'purchase': {}, 'email': email, 'product_name': 'Admin'}

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # get user.id

        # Store the license
        purchase = gumroad_resp.get('purchase', {})
        lic = License(
            user_id=user.id,
            license_key=license_key,
            gumroad_email=gumroad_resp.get('email', email),
            product_name=gumroad_resp.get('product_name', ''),
            sale_id=purchase.get('sale_id', ''),
            subscription_id=purchase.get('subscription_id', ''),
            is_active=True
        )
        db.session.add(lic)
        db.session.commit()

        login_user(user)
        flash('Welcome to Menopause Wellness!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('register.html')


@app.route('/activate', methods=['GET', 'POST'])
def activate():
    """Page for existing users to enter/update their license key."""
    if request.method == 'POST':
        license_key = request.form.get('license_key', '').strip()
        if not license_key:
            flash('License key is required.', 'danger')
            return render_template('activate.html')

        # Verify the key
        gumroad_resp = gumroad_utils.verify_license(license_key)
        if not gumroad_resp['success']:
            flash(f'License key invalid: {gumroad_resp.get("error", "Unknown error")}', 'danger')
            return render_template('activate.html')

        # Store or update license
        purchase = gumroad_resp.get('purchase', {})
        if current_user.is_authenticated:
            lic = License.query.filter_by(user_id=current_user.id).first()
            if lic:
                lic.license_key = license_key
                lic.gumroad_email = gumroad_resp.get('email', current_user.email)
                lic.product_name = gumroad_resp.get('product_name', '')
                lic.sale_id = purchase.get('sale_id', '')
                lic.subscription_id = purchase.get('subscription_id', '')
                lic.is_active = True
                lic.last_verified = datetime.utcnow()
                flash('License updated successfully!', 'success')
            else:
                lic = License(
                    user_id=current_user.id,
                    license_key=license_key,
                    gumroad_email=gumroad_resp.get('email', current_user.email),
                    product_name=gumroad_resp.get('product_name', ''),
                    sale_id=purchase.get('sale_id', ''),
                    subscription_id=purchase.get('subscription_id', ''),
                    is_active=True
                )
                db.session.add(lic)
                flash('License activated successfully!', 'success')
            db.session.commit()
            return redirect(url_for('dashboard'))
        else:
            # Not logged in — redirect to register with a prefill hint
            flash('License is valid! Now create your account.', 'success')
            return redirect(url_for('register'))
    return render_template('activate.html')


@app.route('/purchase')
def purchase():
    """Redirect users to Gumroad to buy a license."""
    product_id = gumroad_utils.get_product_id()
    if product_id:
        return redirect(f'https://gumroad.com/l/{product_id}?offer_code=MENO3')
    flash('Purchase link not configured.', 'danger')
    return redirect(url_for('index'))


@app.route('/start')
def start():
    """Landing page for the $3 first month offer."""
    return render_template('start.html')


@app.route('/free-guide', methods=['GET', 'POST'])
def free_guide():
    """Lead magnet landing page — 5 exercises for menopause belly."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        name = request.form.get('name', '').strip()
        if not email or '@' not in email:
            flash('Please enter a valid email address.', 'danger')
            return render_template('free_guide.html')
        existing = Subscriber.query.filter_by(email=email).first()
        if not existing:
            sub = Subscriber(email=email, name=name or None, source='lead-magnet')
            db.session.add(sub)
            db.session.commit()
        flash('Your free guide is ready below! 📖', 'success')
        return render_template('free_guide.html', show_guide=True, email=email, name=name)
    return render_template('free_guide.html', show_guide=False)


@app.route('/printable-exercises')
def printable_exercises():
    """Printable 5-exercise guide — no email required, linked from free guide."""
    exercises = Exercise.query.order_by(Exercise.order).limit(5).all()
    return render_template('printable_exercises.html', exercises=exercises)


@app.before_request
def check_license():
    """Check that authenticated users have an active license on every page."""
    if current_user.is_authenticated:
        # Skip check for these pages
        exempt_endpoints = ['activate', 'purchase', 'start', 'free_guide', 'printable_exercises', 'logout', 'login', 'register', 'static']
        if request.endpoint in exempt_endpoints:
            return
        if not check_user_has_active_license(current_user):
            flash('Your license is inactive. Please activate to continue.', 'warning')
            return redirect(url_for('activate'))
        # Re-verify license periodically (every 24h)
        lic = License.query.filter_by(user_id=current_user.id, is_active=True).first()
        if lic:
            hours_since = (datetime.utcnow() - lic.last_verified).total_seconds() / 3600
            if hours_since > 24:
                resp = gumroad_utils.check_subscription_active(lic.license_key)
                if resp[0]:
                    lic.last_verified = datetime.utcnow()
                    db.session.commit()
                else:
                    lic.is_active = False
                    db.session.commit()
                    flash('Your subscription has ended. Please renew to continue.', 'warning')
                    return redirect(url_for('activate'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash('Invalid username or password.', 'danger')
            return render_template('login.html')
        login_user(user)
        next_page = request.args.get('next')
        flash('Welcome back!', 'success')
        # Redirect to disclaimer if not yet accepted
        if not user.disclaimer_accepted:
            return redirect(url_for('disclaimer'))
        return redirect(next_page or url_for('dashboard'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# ─── Legal Disclaimer ─────────────────────────────────────────────────
@app.route('/disclaimer', methods=['GET', 'POST'])
@login_required
def disclaimer():
    """Show legal disclaimer — user must accept before using the app."""
    if request.method == 'POST':
        current_user.disclaimer_accepted = True
        current_user.disclaimer_accepted_at = datetime.utcnow()
        db.session.commit()
        flash('Thank you. You can now access the app.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('disclaimer.html')


# ─── Public Routes ────────────────────────────────────────────────────
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


# ─── Dashboard ────────────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    # Redirect to disclaimer if not accepted
    if not current_user.disclaimer_accepted:
        return redirect(url_for('disclaimer'))

    # Latest stats
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    # Workout stats
    workouts_this_week = WorkoutLog.query.filter(
        WorkoutLog.user_id == current_user.id,
        WorkoutLog.workout_date >= week_start
    ).count()

    # Mood stats (last 7 days)
    mood_data = MoodEntry.query.filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.entry_date >= today - timedelta(days=7)
    ).order_by(MoodEntry.entry_date).all()

    # Symptom summary (last 7 days)
    recent_symptoms = SymptomEntry.query.filter(
        SymptomEntry.user_id == current_user.id,
        SymptomEntry.entry_date >= today - timedelta(days=7)
    ).order_by(SymptomEntry.entry_date.desc()).all()

    # Program progress
    current_week = ProgramProgress.query.filter(
        ProgramProgress.user_id == current_user.id,
        ProgramProgress.week >= 1
    ).order_by(ProgramProgress.week.desc()).first()

    program_week = current_week.week if current_week else 1
    days_completed = ProgramProgress.query.filter(
        ProgramProgress.user_id == current_user.id,
        ProgramProgress.week == program_week,
        ProgramProgress.completed == True
    ).count()

    # Journal streak
    last_7 = [today - timedelta(days=i) for i in range(7)]
    journal_days = set(
        r[0] for r in JournalEntry.query
        .with_entities(JournalEntry.entry_date)
        .filter(
            JournalEntry.user_id == current_user.id,
            JournalEntry.entry_date >= today - timedelta(days=7)
        ).all()
    )

    return render_template('dashboard.html',
        workouts_this_week=workouts_this_week,
        mood_data=mood_data,
        recent_symptoms=recent_symptoms,
        program_week=program_week,
        days_completed=days_completed,
        journal_days=journal_days,
        last_7=last_7
    )


# ─── Exercise Routes ──────────────────────────────────────────────────
@app.route('/exercises')
@login_required
def exercises():
    all_exercises = Exercise.query.order_by(Exercise.order).all()
    # Parse target_times JSON for cleaner display
    for ex in all_exercises:
        if ex.target_times:
            try:
                times_dict = json.loads(ex.target_times)
                # Get the first week's value
                first_key = sorted(times_dict.keys())[0] if times_dict else None
                ex.first_target = times_dict.get(first_key, '') if first_key else ''
            except (json.JSONDecodeError, KeyError):
                ex.first_target = ''
        else:
            ex.first_target = ''
    return render_template('exercises.html', exercises=all_exercises)


@app.route('/exercises/<int:exercise_id>')
@login_required
def exercise_detail(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    # User's recent logs for this exercise
    logs = WorkoutLog.query.filter_by(
        user_id=current_user.id,
        exercise_id=exercise_id
    ).order_by(WorkoutLog.workout_date.desc()).limit(20).all()
    return render_template('exercise_detail.html', exercise=exercise, logs=logs)


@app.route('/api/log_workout', methods=['POST'])
@login_required
def log_workout():
    data = request.get_json()
    log = WorkoutLog(
        user_id=current_user.id,
        exercise_id=data['exercise_id'],
        hold_time=data.get('hold_time'),
        sets=data.get('sets', 1),
        notes=data.get('notes', ''),
        workout_date=date.fromisoformat(data.get('date', str(date.today())))
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({'status': 'ok'})


# ─── Workout Timer ────────────────────────────────────────────────────
@app.route('/workout')
@login_required
def workout():
    exercises = Exercise.query.order_by(Exercise.order).all()
    return render_template('workout.html', exercises=exercises)


@app.route('/workout/<int:exercise_id>')
@login_required
def workout_exercise(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    return render_template('workout_timer.html', exercise=exercise)


# ─── Program ──────────────────────────────────────────────────────────
@app.route('/program')
@login_required
def program():
    # Get user's current week and day
    latest = ProgramProgress.query.filter_by(
        user_id=current_user.id
    ).order_by(ProgramProgress.week.desc(), ProgramProgress.day.desc()).first()

    if latest:
        current_week = latest.week
        current_day = latest.day
        # If completed day 7 of current week, move to next
        if current_day >= 7:
            current_week += 1
            current_day = 1
        else:
            current_day += 1
    else:
        current_week = 1
        current_day = 1

    week_schedule = {
        1: 'Core Focus', 2: 'Full Body', 3: 'Core Focus',
        4: 'Active Recovery', 5: 'Full Body', 6: 'Core Focus', 7: 'Rest'
    }

    # Get all progress for this user
    progress_records = ProgramProgress.query.filter_by(
        user_id=current_user.id
    ).all()
    progress_map = {(p.week, p.day): p for p in progress_records}

    return render_template('program.html',
        current_week=current_week,
        current_day=current_day,
        week_schedule=week_schedule,
        progress_map=progress_map
    )


@app.route('/api/program/complete', methods=['POST'])
@login_required
def complete_day():
    data = request.get_json()
    week = data.get('week', 1)
    day = data.get('day', 1)
    workout_type = data.get('workout_type', '')

    existing = ProgramProgress.query.filter_by(
        user_id=current_user.id, week=week, day=day
    ).first()

    if existing:
        existing.completed = True
        existing.notes = data.get('notes', existing.notes)
    else:
        entry = ProgramProgress(
            user_id=current_user.id,
            week=week, day=day,
            completed=True,
            workout_type=workout_type,
            notes=data.get('notes', '')
        )
        db.session.add(entry)
    db.session.commit()
    return jsonify({'status': 'ok'})


# ─── Symptoms ─────────────────────────────────────────────────────────
@app.route('/symptoms')
@login_required
def symptoms():
    entries = SymptomEntry.query.filter_by(
        user_id=current_user.id
    ).order_by(SymptomEntry.entry_date.desc()).limit(50).all()

    # Group by date for chart
    chart_data = {}
    for entry in entries:
        d = str(entry.entry_date)
        if d not in chart_data:
            chart_data[d] = {}
        chart_data[d][entry.symptom_type] = entry.severity

    return render_template('symptoms.html', recent_symptoms=entries, chart_data=json.dumps(chart_data))


@app.route('/api/symptoms/add', methods=['POST'])
@login_required
def add_symptom():
    data = request.get_json()
    entry = SymptomEntry(
        user_id=current_user.id,
        symptom_type=data['symptom_type'],
        severity=data['severity'],
        notes=data.get('notes', ''),
        entry_date=date.fromisoformat(data.get('entry_date', str(date.today())))
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({'status': 'ok'})


# ─── Mood / Journal ───────────────────────────────────────────────────
@app.route('/mood')
@login_required
def mood():
    entries = MoodEntry.query.filter_by(
        user_id=current_user.id
    ).order_by(MoodEntry.entry_date.desc()).limit(30).all()

    chart_labels = [str(e.entry_date) for e in reversed(entries)]
    chart_scores = [e.mood_score for e in reversed(entries)]
    chart_energy = [e.energy_level or 0 for e in reversed(entries)]
    chart_sleep = [e.sleep_quality or 0 for e in reversed(entries)]

    return render_template('mood.html',
        recent_moods=entries,
        chart_labels=json.dumps(chart_labels),
        chart_scores=json.dumps(chart_scores),
        chart_energy=json.dumps(chart_energy),
        chart_sleep=json.dumps(chart_sleep)
    )


@app.route('/api/mood/add', methods=['POST'])
@login_required
def add_mood():
    data = request.get_json()
    entry = MoodEntry(
        user_id=current_user.id,
        mood_score=data['mood_score'],
        energy_level=data.get('energy_level'),
        sleep_quality=data.get('sleep_quality'),
        notes=data.get('notes', ''),
        entry_date=date.fromisoformat(data.get('entry_date', str(date.today())))
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({'status': 'ok'})


@app.route('/journal')
@login_required
def journal():
    entries = JournalEntry.query.filter_by(
        user_id=current_user.id
    ).order_by(JournalEntry.entry_date.desc()).all()
    return render_template('journal.html', entries=entries)


@app.route('/journal/new', methods=['GET', 'POST'])
@login_required
def journal_new():
    if request.method == 'POST':
        entry = JournalEntry(
            user_id=current_user.id,
            title=request.form.get('title', ''),
            content=request.form.get('content', ''),
            is_private=request.form.get('is_private', 'on') == 'on',
            entry_date=date.today()
        )
        db.session.add(entry)
        db.session.commit()
        flash('Journal entry saved!', 'success')
        return redirect(url_for('journal'))
    return render_template('journal_form.html')


@app.route('/journal/<int:entry_id>')
@login_required
def journal_view(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('journal'))
    return render_template('journal_view.html', entry=entry)


# ─── Stage Tracker ────────────────────────────────────────────────────
@app.route('/stages')
@login_required
def stages():
    return render_template('stages.html')


@app.route('/api/stages/update', methods=['POST'])
@login_required
def update_stages():
    data = request.get_json()
    current_user.menopause_stage = data.get('stage')
    current_user.birth_year = data.get('birth_year')
    current_user.last_period_year = data.get('last_period_year')
    db.session.commit()
    return jsonify({'status': 'ok'})


# ─── Articles ─────────────────────────────────────────────────────────
@app.route('/articles')
@login_required
def articles():
    all_articles = Article.query.filter_by(published=True).order_by(Article.created_at.desc()).all()
    return render_template('articles.html', articles=all_articles)


@app.route('/articles/<slug>')
@login_required
def article_view(slug):
    article = Article.query.filter_by(slug=slug).first_or_404()
    # Render markdown to HTML with code blocks and tables
    article.rendered_content = markdown.markdown(
        article.content_md,
        extensions=['extra', 'codehilite', 'tables', 'sane_lists']
    )
    return render_template('article_view.html', article=article)


# ─── Infographic Appendix ─────────────────────────────────────────────
@app.route('/infographic')
@login_required
def infographic():
    return render_template('infographic.html')


# ─── Symptom Decoder ───────────────────────────────────────────────────
@app.route('/decoder')
@login_required
def decoder():
    # Query all exercises, tones, and articles for the template
    exercises_list = Exercise.query.order_by(Exercise.order).all()
    tones_list = IsochronicTone.query.all()
    articles_list = Article.query.filter_by(published=True).order_by(Article.created_at.desc()).all()

    # Convert to dicts for JSON serialization in template
    exercises_data = [{'id': e.id, 'order': e.order, 'name': e.name,
                       'icon': e.icon, 'target_muscles': e.target_muscles,
                       'category': e.category} for e in exercises_list]

    tones_data = [{'id': t.id, 'preset_id': t.preset_id, 'name': t.name,
                   'icon': t.icon, 'description': t.description[:100] if t.description else '',
                   'brainwave_label': t.brainwave_label} for t in tones_list]

    articles_data = [{'id': a.id, 'slug': a.slug, 'title': a.title,
                      'category': a.category, 'summary': a.summary[:100] if a.summary else ''}
                     for a in articles_list]

    return render_template('decoder.html',
        decoder_data=decoder_data,
        exercises=exercises_data,
        tones=tones_data,
        articles=articles_data,
        symptoms_types=SYMPTOM_TYPES,
        symptoms_labels=SYMPTOM_LABELS
    )


# ─── Breathing Exercises ───────────────────────────────────────────────
@app.route('/breathing')
@login_required
def breathing():
    return render_template('breathing.html',
        patterns=breathing_data.BREATHING_PATTERNS,
        emergency_calm=breathing_data.EMERGENCY_CALM
    )


# ─── Perimenopause Hub ────────────────────────────────────────────────
@app.route('/perimenopause')
@login_required
def perimenopause():
    # Curated exercises ideal for perimenopause (core strength, pelvic floor, posture)
    peri_exercises = Exercise.query.filter(Exercise.order.in_([1, 3, 5, 6, 12, 13, 14])).order_by(Exercise.order).all()
    # Curated tones
    peri_tones = IsochronicTone.query.filter(IsochronicTone.preset_id.in_([
        'anxiety_relief', 'hot_flash_calm', 'mood_lift', 'sleep', 'brain_focus', 'stress_resilience'
    ])).all()
    # Relevant articles
    peri_articles = Article.query.filter(Article.slug.in_([
        'understanding-belly-fat', 'why-isometric-exercise', 'nutrition-menopause', 'tracking-progress'
    ])).all()

    return render_template('perimenopause.html',
        exercises=peri_exercises,
        tones=peri_tones,
        articles=peri_articles
    )


# ─── Sleep Log ────────────────────────────────────────────────────────
@app.route('/sleep', methods=['GET', 'POST'])
@login_required
def sleep_log():
    """Sleep tracking with pattern insights."""
    sleep_tones = IsochronicTone.query.filter(
        IsochronicTone.preset_id.in_(['sleep', 'deep_relaxation', 'anxiety_relief'])
    ).all()

    if request.method == 'POST':
        try:
            log_date = date.fromisoformat(request.form.get('log_date', str(date.today())))
        except:
            log_date = date.today()

        bed_str = request.form.get('bedtime', '23:00')
        wake_str = request.form.get('wake_time', '07:00')

        def parse_time(t_str):
            parts = t_str.split(':')
            return time(int(parts[0]) % 24, int(parts[1]) % 60)

        # Calculate sleep duration
        bed_h, bed_m = int(bed_str.split(':')[0]) % 24, int(bed_str.split(':')[1]) % 60
        wake_h, wake_m = int(wake_str.split(':')[0]) % 24, int(wake_str.split(':')[1]) % 60
        total_minutes = (wake_h * 60 + wake_m - bed_h * 60 - bed_m) % (24 * 60)
        if total_minutes < 60:
            total_minutes += 24 * 60  # crossed midnight

        quality = int(request.form.get('sleep_quality', 3))
        interruptions = int(request.form.get('hot_flash_interruptions', 0))

        entry = SleepLog(
            user_id=current_user.id,
            log_date=log_date,
            bedtime=parse_time(bed_str),
            wake_time=parse_time(wake_str),
            sleep_quality=quality,
            hot_flash_interruptions=interruptions,
            total_minutes_asleep=total_minutes,
            had_alcohol=bool(request.form.get('had_alcohol')),
            caffeine_after_4pm=bool(request.form.get('caffeine_after_4pm')),
            exercised=bool(request.form.get('exercised')),
            used_sleep_tone=bool(request.form.get('used_sleep_tone')),
            tone_id=request.form.get('tone_id', type=int) or None,
            notes=request.form.get('notes', '')
        )
        db.session.add(entry)
        db.session.commit()
        flash('Sleep logged!', 'success')
        return redirect(url_for('sleep_log'))

    # Get history (last 30 days)
    history = SleepLog.query.filter_by(user_id=current_user.id).order_by(
        SleepLog.log_date.desc()
    ).limit(30).all()

    # Generate insights if 5+ entries exist
    insights = []
    if len(history) >= 5:
        entries = list(history)
        avg_quality = sum(e.sleep_quality for e in entries) / len(entries)
        avg_hours = sum(e.total_minutes_asleep or 0 for e in entries) / len(entries) / 60
        avg_interruptions = sum(e.hot_flash_interruptions for e in entries) / len(entries)

        insights.append({
            'icon': '📊',
            'title': 'Your Sleep Average',
            'text': f'{avg_hours:.1f} hours, {avg_quality:.1f}/5 quality, {avg_interruptions:.1f} hot flash wake-ups per night'
        })

        # Alcohol correlation
        alc_entries = [e for e in entries if e.had_alcohol]
        no_alc = [e for e in entries if not e.had_alcohol]
        if alc_entries and no_alc:
            alc_q = sum(e.sleep_quality for e in alc_entries) / len(alc_entries)
            no_alc_q = sum(e.sleep_quality for e in no_alc) / len(no_alc)
            if no_alc_q > alc_q:
                insights.append({
                    'icon': '🍷',
                    'title': 'Alcohol & Sleep Quality',
                    'text': f'Nights without alcohol: {no_alc_q:.1f}/5 vs with alcohol: {alc_q:.1f}/5. A difference of {no_alc_q - alc_q:.1f} points.'
                })

        # Exercise correlation
        ex_entries = [e for e in entries if e.exercised]
        no_ex = [e for e in entries if not e.exercised]
        if ex_entries and no_ex:
            ex_q = sum(e.sleep_quality for e in ex_entries) / len(ex_entries)
            no_ex_q = sum(e.sleep_quality for e in no_ex) / len(no_ex)
            if ex_q > no_ex_q:
                insights.append({
                    'icon': '🏋️',
                    'title': 'Exercise Helps You Sleep Better',
                    'text': f'Sleep quality on exercise days: {ex_q:.1f}/5 vs rest days: {no_ex_q:.1f}/5.'
                })

        # Tone correlation
        tone_entries = [e for e in entries if e.used_sleep_tone]
        if tone_entries:
            tone_q = sum(e.sleep_quality for e in tone_entries) / len(tone_entries)
            insights.append({
                'icon': '🎵',
                'title': 'Brainwave Tones & Sleep',
                'text': f'Sleep quality on nights you used a tone: {tone_q:.1f}/5. Keep it up!'
            })

    return render_template('sleep.html',
        history=history,
        insights=insights,
        sleep_tones=sleep_tones,
        today=date.today()
    )


# ─── Pelvic Floor & Sexual Health ────────────────────────────────────
PELVIC_EXERCISES = [14, 5, 3, 12, 2]  # Clamshell, Glute Bridge, Dead Bug, Single-Leg Balance, Side Plank

@app.route('/pelvic-health')
@login_required
def pelvic_health():
    """Pelvic floor and sexual health resource page."""
    exercises = Exercise.query.filter(Exercise.order.in_(PELVIC_EXERCISES)).order_by(Exercise.order).all()
    tones = IsochronicTone.query.filter(
        IsochronicTone.preset_id.in_(['libido_sensuality', 'pain_comfort', 'stress_resilience', 'mood_lift'])
    ).all()
    return render_template('pelvic_health.html', exercises=exercises, tones=tones)


# ─── Doctor Visit Prep Tool ──────────────────────────────────────────
DOCTOR_QUESTIONS = [
    {'id': 'hrt', 'question': 'Am I a candidate for body-identical hormone therapy (HRT)?'},
    {'id': 'thyroid', 'question': 'Should I check my thyroid function (TSH, T3, T4)?'},
    {'id': 'sleep', 'question': 'What can I do about my sleep disruption? Is there anything medical that can help?'},
    {'id': 'weight', 'question': 'Is this weight gain hormonal, or is something else going on?'},
    {'id': 'bone_density', 'question': 'Do I need a bone density scan (DEXA)?'},
    {'id': 'vitamins', 'question': 'Should I check my vitamin D, iron, and B12 levels?'},
    {'id': 'libido', 'question': 'What can help with vaginal dryness and low libido?'},
    {'id': 'mood', 'question': 'Are these mood swings menopause or something else? Should I consider medication?'},
    {'id': 'specialist', 'question': 'Can you recommend a certified menopause specialist?'},
    {'id': 'exercise', 'question': 'Is isometric exercise safe for me given my current health?'},
]

LAB_TESTS = [
    {'id': 'estradiol', 'label': 'Estradiol (E2)', 'unit': 'pg/mL', 'normal_range': 'Varies by stage — post-meno: <20'},
    {'id': 'fsh', 'label': 'FSH', 'unit': 'mIU/mL', 'normal_range': 'Post-menopausal: 25–135'},
    {'id': 'tsh', 'label': 'TSH', 'unit': 'mIU/L', 'normal_range': '0.5–4.5'},
    {'id': 'vitamin_d', 'label': 'Vitamin D', 'unit': 'ng/mL', 'normal_range': '30–80'},
    {'id': 'ferritin', 'label': 'Ferritin (Iron)', 'unit': 'ng/mL', 'normal_range': '20–150'},
    {'id': 'vitamin_b12', 'label': 'Vitamin B12', 'unit': 'pg/mL', 'normal_range': '200–900'},
    {'id': 'hba1c', 'label': 'HbA1c', 'unit': '%', 'normal_range': '<5.7'},
    {'id': 'cholesterol', 'label': 'Total Cholesterol', 'unit': 'mg/dL', 'normal_range': '<200'},
]


@app.route('/doctor-prep', methods=['GET', 'POST'])
@login_required
def doctor_prep():
    # Pre-fill from user's existing data
    existing_symptoms = {}
    entries = SymptomEntry.query.filter_by(user_id=current_user.id).order_by(SymptomEntry.entry_date.desc()).all()
    for e in entries:
        key = e.symptom_type
        if key not in existing_symptoms:
            existing_symptoms[key] = {'severity': e.severity, 'notes': e.notes or ''}

    # Pre-fill stage info
    stage_info = {
        'stage': current_user.menopause_stage or '',
        'birth_year': current_user.birth_year or '',
        'last_period_year': current_user.last_period_year or ''
    }

    if request.method == 'POST':
        # Process form data and show summary
        selected_symptoms = {}
        for sym in SYMPTOM_TYPES:
            severity = request.form.get(f'sev_{sym}')
            if severity and int(severity) > 0:
                selected_symptoms[sym] = {
                    'severity': int(severity),
                    'notes': request.form.get(f'notes_{sym}', '')
                }

        # Lab values
        lab_values = {}
        for lab in LAB_TESTS:
            val = request.form.get(f'lab_{lab["id"]}')
            if val:
                lab_values[lab['id']] = {
                    'value': val,
                    'label': lab['label'],
                    'unit': lab['unit'],
                    'normal_range': lab['normal_range']
                }

        # Selected questions
        selected_questions = [q['question'] for q in DOCTOR_QUESTIONS if request.form.get(f'q_{q["id"]}')]
        custom_question = request.form.get('custom_question', '').strip()
        if custom_question:
            selected_questions.append(custom_question)

        # User info
        user_info = {
            'age': request.form.get('age', ''),
            'stage': request.form.get('stage', ''),
            'last_period': request.form.get('last_period', ''),
            'name': current_user.display_name or current_user.username
        }

        return render_template('doctor_prep.html',
            mode='summary',
            symptoms_types=SYMPTOM_TYPES,
            symptoms_labels=SYMPTOM_LABELS,
            existing_symptoms=existing_symptoms,
            stage_info=stage_info,
            doctor_questions=DOCTOR_QUESTIONS,
            lab_tests=LAB_TESTS,
            selected_symptoms=selected_symptoms,
            lab_values=lab_values,
            selected_questions=selected_questions,
            user_info=user_info,
            now=datetime.now
        )

    return render_template('doctor_prep.html',
        mode='form',
        symptoms_types=SYMPTOM_TYPES,
        symptoms_labels=SYMPTOM_LABELS,
        existing_symptoms=existing_symptoms,
        stage_info=stage_info,
        doctor_questions=DOCTOR_QUESTIONS,
        lab_tests=LAB_TESTS
    )


# ─── Community ────────────────────────────────────────────────────────
@app.route('/community')
@login_required
def community():
    posts = CommunityPost.query.order_by(
        CommunityPost.pinned.desc(),
        CommunityPost.updated_at.desc()
    ).all()
    return render_template('community.html', posts=posts)


@app.route('/community/new', methods=['GET', 'POST'])
@login_required
def community_new():
    if request.method == 'POST':
        post = CommunityPost(
            user_id=current_user.id,
            title=request.form.get('title', ''),
            content=request.form.get('content', ''),
            category=request.form.get('category', 'general')
        )
        db.session.add(post)
        db.session.commit()
        flash('Post created!', 'success')
        return redirect(url_for('community'))
    return render_template('community_form.html')


@app.route('/community/<int:post_id>')
@login_required
def community_view(post_id):
    post = CommunityPost.query.get_or_404(post_id)
    return render_template('community_view.html', post=post)


@app.route('/community/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = CommunityPost.query.get_or_404(post_id)
    content = request.form.get('content', '').strip()
    if content:
        comment = CommunityComment(
            post_id=post_id,
            user_id=current_user.id,
            content=content
        )
        db.session.add(comment)
        post.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Comment added!', 'success')
    return redirect(url_for('community_view', post_id=post_id))


# ─── Profile ──────────────────────────────────────────────────────────
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.display_name = request.form.get('display_name', current_user.username)
        current_user.bio = request.form.get('bio', '')
        current_user.menopause_stage = request.form.get('menopause_stage')
        by = request.form.get('birth_year')
        lpy = request.form.get('last_period_year')
        if by: current_user.birth_year = int(by)
        if lpy: current_user.last_period_year = int(lpy)
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html')


# ─── Isochronic Tones ─────────────────────────────────────────────────
@app.route('/tones')
@login_required
def tones():
    """Isochronic tone player page with all presets."""
    all_tones = IsochronicTone.query.order_by(IsochronicTone.id).all()
    # Recent sessions for this user
    recent = ToneSession.query.filter_by(
        user_id=current_user.id
    ).order_by(ToneSession.created_at.desc()).limit(20).all()
    return render_template('tones.html', tones=all_tones, recent=recent)


@app.route('/api/tones/list')
@login_required
def tones_list():
    """Return all tone presets as JSON."""
    tones = IsochronicTone.query.order_by(IsochronicTone.id).all()
    return jsonify([{
        'id': t.id,
        'preset_id': t.preset_id,
        'name': t.name,
        'description': t.description,
        'carrier_freq': t.carrier_freq,
        'beat_freq': t.beat_freq,
        'brainwave_label': t.brainwave_label,
        'icon': t.icon,
        'color': t.color,
        'duration_min': t.duration_min
    } for t in tones])


@app.route('/api/tones/log', methods=['POST'])
@login_required
def log_tone_session():
    """Log a completed tone listening session."""
    data = request.get_json()
    session = ToneSession(
        user_id=current_user.id,
        tone_id=data['tone_id'],
        duration_seconds=data.get('duration_seconds', 0),
        completed=data.get('completed', False),
        mood_before=data.get('mood_before'),
        mood_after=data.get('mood_after'),
        notes=data.get('notes', '')
    )
    db.session.add(session)
    db.session.commit()
    return jsonify({'status': 'ok', 'session_id': session.id})


# ─── Initialize ───────────────────────────────────────────────────────
@app.cli.command('init-db')
def init_db():
    """Initialize the database and seed with data."""
    db.create_all()
    seed_database(db)
    print('Database initialized and seeded.')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database(db)
    app.run(host='0.0.0.0', port=5053, debug=True)

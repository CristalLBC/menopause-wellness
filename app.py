import os, json
from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Exercise, WorkoutLog, MoodEntry, JournalEntry, SymptomEntry, \
    ProgramProgress, Article, CommunityPost, CommunityComment, SYMPTOM_TYPES, SYMPTOM_LABELS, \
    IsochronicTone, ToneSession, License, check_user_has_active_license, Subscriber
from seed_data import seed_database
import gumroad_utils

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'menopause-wellness-secret-key-2025')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///menopause_wellness.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


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

        # Verify Gumroad license key
        gumroad_resp = gumroad_utils.verify_license(license_key)
        if not gumroad_resp['success']:
            flash(f'License key invalid: {gumroad_resp.get("error", "Unknown error")}', 'danger')
            return render_template('register.html')

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
        return redirect(f'https://gumroad.com/l/{product_id}')
    flash('Purchase link not configured.', 'danger')
    return redirect(url_for('index'))


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
        exempt_endpoints = ['activate', 'purchase', 'free_guide', 'printable_exercises', 'logout', 'login', 'register', 'static']
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
        return redirect(next_page or url_for('dashboard'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


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
    return render_template('article_view.html', article=article)


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
    app.run(host='0.0.0.0', port=5052, debug=True)

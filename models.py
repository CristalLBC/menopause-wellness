from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    display_name = db.Column(db.String(80))
    bio = db.Column(db.Text)
    avatar = db.Column(db.String(256))

    # Menopause stage info
    menopause_stage = db.Column(db.String(40))  # perimenopause, menopause, post_menopause
    birth_year = db.Column(db.Integer)
    last_period_year = db.Column(db.Integer)

    # Relationships
    workout_logs = db.relationship('WorkoutLog', backref='user', lazy='dynamic')
    mood_entries = db.relationship('MoodEntry', backref='user', lazy='dynamic')
    journal_entries = db.relationship('JournalEntry', backref='user', lazy='dynamic')
    symptom_entries = db.relationship('SymptomEntry', backref='user', lazy='dynamic')
    program_progress = db.relationship('ProgramProgress', backref='user', lazy='dynamic')
    posts = db.relationship('CommunityPost', backref='author', lazy='dynamic')
    comments = db.relationship('CommunityComment', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Exercise(db.Model):
    __tablename__ = 'exercises'
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer, default=0)
    name = db.Column(db.String(200), nullable=False)
    target_muscles = db.Column(db.String(300))
    why_it_works = db.Column(db.Text)
    instructions = db.Column(db.Text)
    modifications = db.Column(db.Text)
    easier_options = db.Column(db.Text)
    harder_options = db.Column(db.Text)
    target_times = db.Column(db.Text)  # JSON: {"week1": "20-30s", "week2": "35-45s", ...}
    common_mistakes = db.Column(db.Text)
    icon = db.Column(db.String(50), default='🏋️')
    category = db.Column(db.String(50))  # core, full_body, legs

    def __repr__(self):
        return f'<Exercise {self.name}>'


class WorkoutLog(db.Model):
    __tablename__ = 'workout_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    hold_time = db.Column(db.Float)  # seconds
    sets = db.Column(db.Integer, default=1)
    notes = db.Column(db.Text)
    workout_date = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    exercise = db.relationship('Exercise', backref='logs')


class MoodEntry(db.Model):
    __tablename__ = 'mood_entries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mood_score = db.Column(db.Integer)  # 1-10
    energy_level = db.Column(db.Integer)  # 1-10
    sleep_quality = db.Column(db.Integer)  # 1-10
    notes = db.Column(db.Text)
    entry_date = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    is_private = db.Column(db.Boolean, default=True)
    entry_date = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


SYMPTOM_TYPES = [
    'hot_flashes', 'night_sweats', 'mood_swings', 'fatigue',
    'brain_fog', 'sleep_issues', 'joint_pain', 'headaches',
    'anxiety', 'bloating', 'weight_gain', 'low_libido'
]

SYMPTOM_LABELS = {
    'hot_flashes': 'Hot Flashes', 'night_sweats': 'Night Sweats',
    'mood_swings': 'Mood Swings', 'fatigue': 'Fatigue',
    'brain_fog': 'Brain Fog', 'sleep_issues': 'Sleep Issues',
    'joint_pain': 'Joint Pain', 'headaches': 'Headaches',
    'anxiety': 'Anxiety', 'bloating': 'Bloating',
    'weight_gain': 'Weight Gain', 'low_libido': 'Low Libido'
}

class SymptomEntry(db.Model):
    __tablename__ = 'symptom_entries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symptom_type = db.Column(db.String(40), nullable=False)
    severity = db.Column(db.Integer)  # 1-5
    notes = db.Column(db.Text)
    entry_date = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ProgramProgress(db.Model):
    __tablename__ = 'program_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    week = db.Column(db.Integer, nullable=False)
    day = db.Column(db.Integer, nullable=False)  # 1-7
    completed = db.Column(db.Boolean, default=False)
    workout_type = db.Column(db.String(40))  # core_focus, full_body, active_recovery, rest
    notes = db.Column(db.Text)
    entry_date = db.Column(db.Date, default=date.today)


class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True)
    category = db.Column(db.String(50))
    content_md = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text)
    author = db.Column(db.String(100), default='Fitness Guide')
    published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Article {self.title}>'


class CommunityPost(db.Model):
    __tablename__ = 'community_posts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    comments = db.relationship('CommunityComment', backref='post', lazy='dynamic',
                               order_by='CommunityComment.created_at')


class CommunityComment(db.Model):
    __tablename__ = 'community_comments'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('community_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─── Isochronic Tones ───────────────────────────────────────────────

TONES_PRESETS = [
    'sleep', 'anxiety_relief', 'hot_flash_calm', 'brain_focus',
    'energy_boost', 'mood_lift', 'deep_relaxation', 'morning_wakeup',
    'stress_resilience', 'afternoon_recharge', 'libido_sensuality',
    'pain_comfort', 'confidence_clarity'
]

TONES_LABELS = {
    'sleep': '💤 Deep Sleep',
    'anxiety_relief': '🧘 Anxiety Relief',
    'hot_flash_calm': '🌊 Hot Flash Calm',
    'brain_focus': '🧠 Brain Focus',
    'energy_boost': '⚡ Energy Boost',
    'mood_lift': '🌤️ Mood Lift',
    'deep_relaxation': '🕯️ Deep Relaxation',
    'morning_wakeup': '🌅 Morning Wake Up',
    'stress_resilience': '🌿 Stress Resilience',
    'afternoon_recharge': '☕ Afternoon Recharge',
    'libido_sensuality': '🌸 Libido & Sensuality',
    'pain_comfort': '🩹 Pain & Comfort',
    'confidence_clarity': '✨ Confidence & Clarity'
}

TONES_FREQUENCIES = {
    # Isochronic tones: carrier_freq (Hz) and beat_freq (Hz)
    # Carrier is the audible tone, beat is the pulsing rate that entrains brainwaves
    'sleep':          {'carrier': 220, 'beat': 2.5,   'brainwave': 'Delta (2.5 Hz)',       'description': 'Slow delta pulsing to promote deep, restorative sleep. Best used at bedtime with headphones.'},
    'anxiety_relief': {'carrier': 264, 'beat': 6.0,   'brainwave': 'Theta (6.0 Hz)',        'description': 'Gentle theta pulsing to quiet racing thoughts and lower cortisol. Great for afternoon overwhelm.'},
    'hot_flash_calm': {'carrier': 180, 'beat': 5.5,   'brainwave': 'Theta (5.5 Hz)',        'description': 'Cooling theta rhythm to help your nervous system regulate temperature during hot flash episodes.'},
    'brain_focus':    {'carrier': 300, 'beat': 10.0,  'brainwave': 'Alpha (10.0 Hz)',       'description': 'Steady alpha pulsing to cut through brain fog and sharpen concentration for work or reading.'},
    'energy_boost':   {'carrier': 400, 'beat': 15.0,  'brainwave': 'Low Beta (15.0 Hz)',    'description': 'Energising beta rhythm to replace that second cup of coffee. Use mid-morning or early afternoon.'},
    'mood_lift':      {'carrier': 250, 'beat': 7.83,  'brainwave': 'Theta/Alpha (7.83 Hz — Schumann resonance)', 'description': 'The Earth\'s natural resonance frequency — 7.83 Hz — known to promote emotional balance and wellbeing.'},
    'deep_relaxation':{'carrier': 200, 'beat': 4.0,   'brainwave': 'Theta/Delta (4.0 Hz)',   'description': 'Borderline theta-delta pulsing for profound relaxation without drowsiness. Perfect after a workout.'},
    'morning_wakeup': {'carrier': 350, 'beat': 12.0,  'brainwave': 'Alpha/Low Beta (12.0 Hz)', 'description': 'A gentle alpha-to-beta transition to wake up your brain naturally, without caffeine jitters.'},
    'stress_resilience':  {'carrier': 280, 'beat': 8.0,   'brainwave': 'Alpha (8.0 Hz)',             'description': 'Steady alpha pulsing to build your daily stress buffer. Lowers baseline cortisol and creates a centred, grounded mental state. Use during work hours or before stressful situations.'},
    'afternoon_recharge': {'carrier': 210, 'beat': 4.5,   'brainwave': 'Theta (4.5 Hz)',            'description': 'A quick afternoon reset that replaces the 3pm slump without caffeine. Theta pulsing at 4.5 Hz mimics the brain state of a power nap — refreshing without grogginess. 10–15 minutes is all you need.'},
    'libido_sensuality':  {'carrier': 190, 'beat': 7.0,   'brainwave': 'Theta (7.0 Hz)',            'description': 'Warm theta rhythm to reconnect with your body and sensual self. Helps release tension stored in the pelvic region and quiets mental chatter. Best used in a relaxed, private setting.'},
    'pain_comfort':       {'carrier': 170, 'beat': 2.5,   'brainwave': 'Delta (2.5 Hz)',            'description': 'Deep delta pulsing to activate your body\'s natural pain-gating mechanisms. Particularly effective for joint pain and menopausal aches. Use during flare-ups or as a daily preventative.'},
    'confidence_clarity': {'carrier': 380, 'beat': 14.0,  'brainwave': 'Low Beta (14.0 Hz)',         'description': 'Focused low-beta rhythm to sharpen self-expression and decision-making. Counteracts the self-doubt that can accompany menopause. Use before meetings, presentations, or important conversations.'}
}


class IsochronicTone(db.Model):
    """Predefined isochronic tone preset with frequency data."""
    __tablename__ = 'isochronic_tones'
    id = db.Column(db.Integer, primary_key=True)
    preset_id = db.Column(db.String(40), unique=True, nullable=False)  # matches TONES_PRESETS keys
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    carrier_freq = db.Column(db.Float, nullable=False)   # audible carrier (Hz)
    beat_freq = db.Column(db.Float, nullable=False)      # pulsing rate = brainwave entrainment (Hz)
    brainwave_label = db.Column(db.String(80))
    icon = db.Column(db.String(10), default='🎵')
    color = db.Column(db.String(20), default='#d4436b')
    duration_min = db.Column(db.Integer, default=15)     # recommended session length (minutes)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sessions = db.relationship('ToneSession', backref='tone', lazy='dynamic')

    def __repr__(self):
        return f'<IsochronicTone {self.name}>'


class ToneSession(db.Model):
    """Records a user's listening session."""
    __tablename__ = 'tone_sessions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tone_id = db.Column(db.Integer, db.ForeignKey('isochronic_tones.id'), nullable=False)
    duration_seconds = db.Column(db.Integer)               # how long they actually listened
    completed = db.Column(db.Boolean, default=False)        # did they finish the full session
    mood_before = db.Column(db.Integer)                    # 1-10 self-rating before
    mood_after = db.Column(db.Integer)                     # 1-10 self-rating after
    notes = db.Column(db.Text)
    session_date = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─── License Keys ─────────────────────────────────────────────────────

class SleepLog(db.Model):
    """Tracks a user's nightly sleep — bedtime, quality, interruptions, and lifestyle factors."""
    __tablename__ = 'sleep_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    log_date = db.Column(db.Date, default=date.today, nullable=False)

    # Core sleep data
    bedtime = db.Column(db.Time, nullable=False)           # When they went to bed
    wake_time = db.Column(db.Time, nullable=False)          # When they woke up
    sleep_quality = db.Column(db.Integer, default=3)        # 1-5 scale
    hot_flash_interruptions = db.Column(db.Integer, default=0)  # Number of wake-ups
    total_minutes_asleep = db.Column(db.Integer)            # Computed estimate

    # Lifestyle factors
    had_alcohol = db.Column(db.Boolean, default=False)
    caffeine_after_4pm = db.Column(db.Boolean, default=False)
    exercised = db.Column(db.Boolean, default=False)
    used_sleep_tone = db.Column(db.Boolean, default=False)
    tone_id = db.Column(db.Integer, db.ForeignKey('isochronic_tones.id'), nullable=True)

    # Notes
    notes = db.Column(db.Text, default='')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('sleep_logs', lazy='dynamic'))
    tone = db.relationship('IsochronicTone', backref='sleep_logs')

    def __repr__(self):
        return f'<SleepLog {self.log_date} by user {self.user_id}>'


class License(db.Model):
    """Stores a user's Gumroad license key for access control."""
    __tablename__ = 'licenses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    license_key = db.Column(db.String(100), nullable=False)
    gumroad_email = db.Column(db.String(200))
    product_name = db.Column(db.String(200))
    sale_id = db.Column(db.String(100))
    subscription_id = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    last_verified = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('license', uselist=False))

    def __repr__(self):
        return f'<License {self.license_key[:12]}...>'


def check_user_has_active_license(user):
    """Check if a user has a valid, active license."""
    if not user or not user.is_authenticated:
        return False
    # Admin bypass via env var
    import os
    admin_emails = os.environ.get('ADMIN_EMAILS', '').lower().split(',')
    if user.email and user.email.lower() in [e.strip() for e in admin_emails if e.strip()]:
        return True
    lic = License.query.filter_by(user_id=user.id, is_active=True).first()
    return lic is not None


# ─── Email Subscribers (Lead Magnet) ──────────────────────────────────

class Subscriber(db.Model):
    """Captured emails from the free lead magnet."""
    __tablename__ = 'subscribers'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    name = db.Column(db.String(100))
    source = db.Column(db.String(50), default='lead-magnet')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Subscriber {self.email}>'

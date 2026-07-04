"""
Seed the database with exercises, articles, and sample data.
"""
import json
from datetime import date, timedelta
from models import db, Exercise, Article, User, IsochronicTone, TONES_LABELS, TONES_FREQUENCIES, TONES_PRESETS

EXERCISES = [
    {
        "order": 1,
        "name": "The Front Plank",
        "target_muscles": "Transverse abdominis, rectus abdominis, shoulders, glutes",
        "why_it_works": "The plank is the foundational isometric exercise. It forces your entire core — especially the deep TVA muscle — to engage continuously. No crunch can replicate this sustained deep-core activation.",
        "instructions": "1. Start on your hands and knees on a mat or carpet.\n2. Lower your forearms to the floor, elbows directly under your shoulders.\n3. Step your feet back one at a time until your legs are straight.\n4. Your body should form a straight line from heels to head — no sagging hips, no raised buttocks.\n5. Gaze at the floor about 6 inches in front of your hands to keep your neck neutral.\n6. Squeeze your glutes and pull your belly button toward your spine.\n7. Hold and breathe.",
        "modifications": "**Easier:** Drop your knees to the floor while keeping a straight line from knees to head.\n**Harder:** Lift one foot 2 inches off the floor; alternate every 15 seconds.",
        "easier_options": "Knee plank",
        "harder_options": "Single-leg plank",
        "target_times": json.dumps({"Week 1": "20–30s", "Week 2": "35–45s", "Week 3": "50–60s", "Week 4": "60+s"}, ensure_ascii=False),
        "common_mistakes": "• Hips sagging toward the floor\n• Buttocks raised in the air\n• Holding your breath\n• Elbows too far forward",
        "icon": "📐",
        "category": "core"
    },
    {
        "order": 2,
        "name": "The Side Plank",
        "target_muscles": "Obliques, transverse abdominis, hip abductors",
        "why_it_works": "The side plank targets the oblique muscles that cinch your waist from the sides. It also strengthens the often-neglected hip abductors, which stabilize your pelvis and improve your posture — making your belly look flatter immediately.",
        "instructions": "1. Lie on your right side with legs stacked, feet together.\n2. Place your right forearm on the floor, elbow directly under your shoulder.\n3. Stack your left foot on top of your right foot.\n4. Lift your hips off the floor until your body forms a straight diagonal line.\n5. Extend your left arm toward the ceiling, or rest it on your hip.\n6. Keep your neck in line with your spine.\n7. Hold and breathe. Repeat on the left side.",
        "modifications": "**Easier:** Bend your bottom knee and keep it on the floor as a kickstand.\n**Harder:** Lift your top leg 6–12 inches; hold.",
        "easier_options": "Bent-knee side plank",
        "harder_options": "Side plank with leg raise",
        "target_times": json.dumps({"Week 1": "15–20s per side", "Week 2": "25–30s", "Week 3": "35–45s", "Week 4": "45+s"}, ensure_ascii=False),
        "common_mistakes": "• Hips rotated forward or backward\n• Neck craned toward the floor\n• Bottom hip touching the floor between sets",
        "icon": "📐",
        "category": "core"
    },
    {
        "order": 3,
        "name": "The Dead Bug Hold",
        "target_muscles": "Transverse abdominis, pelvic floor, deep spinal stabilizers",
        "why_it_works": "This is arguably the most important exercise in this guide. The dead bug hold directly trains the deep core and pelvic floor — areas weakened by menopause and childbirth. It teaches your core to stabilize your spine against movement, which is exactly what flattens the belly.",
        "instructions": "1. Lie on your back on a mat.\n2. Extend both arms straight toward the ceiling, directly over your shoulders.\n3. Lift both legs into a tabletop position — knees bent 90°, shins parallel to floor.\n4. Press your lower back firmly into the floor. There should be no gap.\n5. This is your starting position. Hold it.\n6. Focus on keeping your lower back pressed down while breathing deeply.",
        "modifications": "**Easier:** Keep your feet on the floor, knees bent, arms at your sides. Simply press your lower back into the floor and hold.\n**Harder:** Extend your legs straight at a 45-degree angle while keeping your lower back pressed down.",
        "easier_options": "Feet on floor, back press only",
        "harder_options": "Extended leg dead bug",
        "target_times": json.dumps({"Week 1": "20–30s", "Week 2": "30–40s", "Week 3": "45–60s", "Week 4": "60+s"}, ensure_ascii=False),
        "common_mistakes": "• Lower back arching off the floor (stop and reset)\n• Neck straining\n• Shallow chest breathing instead of belly breathing",
        "icon": "🪲",
        "category": "core"
    },
    {
        "order": 4,
        "name": "The Hollow Body Hold",
        "target_muscles": "Entire anterior core chain — upper abs, lower abs, TVA, hip flexors",
        "why_it_works": "The hollow body hold is used by Olympic gymnasts to build unbreakable core strength. For post-menopausal women, it forces the lower abs — the hardest area to tone — to engage fully. There is no way to cheat this exercise.",
        "instructions": "1. Lie on your back with arms extended overhead and legs straight.\n2. Press your lower back into the floor.\n3. Simultaneously lift your shoulders and legs 6–12 inches off the floor.\n4. Your body should form a gentle banana shape.\n5. Arms are by your ears, legs are straight and squeezed together.\n6. Point your toes and reach your fingers away from each other.\n7. Hold and breathe.",
        "modifications": "**Easier:** Lift your legs higher (45°) and keep arms by your sides. Or bend knees to 90° (tucked hollow body).\n**Harder:** Lower your legs closer to the floor without arching your back.",
        "easier_options": "Tucked hollow body hold",
        "harder_options": "Low-leg hollow body hold",
        "target_times": json.dumps({"Week 1": "10–15s", "Week 2": "15–25s", "Week 3": "25–35s", "Week 4": "35+s"}, ensure_ascii=False),
        "common_mistakes": "• Lower back lifting off the floor (stop immediately)\n• Chin tucked too far into chest\n• Legs too high (reduces engagement)",
        "icon": "🌙",
        "category": "core"
    },
    {
        "order": 5,
        "name": "The Glute Bridge Hold",
        "target_muscles": "Glutes, hamstrings, lower back, transverse abdominis",
        "why_it_works": "Strong glutes are essential for a flat belly. When your glutes are weak (extremely common after years of sitting), your pelvis tilts forward, pushing your belly out. The glute bridge hold corrects this tilt, pulling your belly in mechanically while building muscle in your largest muscle group.",
        "instructions": "1. Lie on your back with knees bent, feet flat on the floor, hip-width apart.\n2. Arms at your sides, palms facing down.\n3. Press through your heels and squeeze your glutes to lift your hips toward the ceiling.\n4. Your body should form a straight line from shoulders to knees.\n5. Pull your belly button toward your spine.\n6. Squeeze your glutes as hard as you can and hold.\n7. Breathe steadily throughout.",
        "modifications": "**Easier:** Lift only halfway.\n**Harder:** Extend one leg straight, keeping thighs parallel. Hold, then switch legs.",
        "easier_options": "Half bridge hold",
        "harder_options": "Single-leg glute bridge hold",
        "target_times": json.dumps({"Week 1": "30–45s", "Week 2": "45–60s", "Week 3": "60–75s", "Week 4": "75+s"}, ensure_ascii=False),
        "common_mistakes": "• Hyperextending the lower back\n• Feet too close to your body\n• Glutes not fully engaged",
        "icon": "🍑",
        "category": "full_body"
    },
    {
        "order": 6,
        "name": "The Bird Dog Hold",
        "target_muscles": "Erector spinae, transverse abdominis, glutes, shoulders",
        "why_it_works": "The bird dog hold builds the posterior chain — the muscles along the back of your body. A strong back improves posture instantly, making your belly appear flatter. It also trains anti-rotation core stability: your abs must fire continuously to keep you from tipping over.",
        "instructions": "1. Start on hands and knees — hands under shoulders, knees under hips.\n2. Keep your spine neutral — not arched, not rounded.\n3. Extend your right arm straight forward and your left leg straight back simultaneously.\n4. Your extended arm and leg should be parallel to the floor.\n5. Your hips and shoulders must stay square to the floor — no rotation.\n6. Reach your fingers forward and your heel backward.\n7. Pull your belly button up toward your spine.\n8. Hold. Return to start and repeat on the opposite side.",
        "modifications": "**Easier:** Extend only one limb at a time (arm only or leg only).\n**Harder:** Draw small circles with the extended hand and foot.",
        "easier_options": "Single limb bird dog",
        "harder_options": "Bird dog with circles",
        "target_times": json.dumps({"Week 1": "15–20s per side", "Week 2": "25–30s", "Week 3": "30–40s", "Week 4": "40+s"}, ensure_ascii=False),
        "common_mistakes": "• Hips rotating open\n• Neck craning upward\n• Lower back sagging",
        "icon": "🐕",
        "category": "full_body"
    },
    {
        "order": 7,
        "name": "The Wall Sit",
        "target_muscles": "Quadriceps, glutes, core stabilizers",
        "why_it_works": "The wall sit engages the largest muscles in your body — your quads and glutes. This creates significant metabolic demand that boosts calorie burn for hours. Studies show that just 3 minutes of wall sits per day significantly reduces visceral fat in post-menopausal women. Your legs are your body's biggest calorie furnace.",
        "instructions": "1. Stand with your back against a smooth wall, feet shoulder-width apart.\n2. Walk your feet out about 18–24 inches from the wall.\n3. Slide your back down the wall until your knees are bent at 90 degrees.\n4. Your thighs should be parallel to the floor.\n5. Keep your back flat against the wall the entire time.\n6. Pull your belly button toward your spine.\n7. Keep your weight in your heels.\n8. Hold and breathe.",
        "modifications": "**Easier:** Slide down only to a 45-degree bend.\n**Harder:** Lift your heels slightly (calf raise wall sit) or hold a weight.",
        "easier_options": "45-degree wall sit",
        "harder_options": "Calf raise wall sit",
        "target_times": json.dumps({"Week 1": "20–30s", "Week 2": "30–45s", "Week 3": "45–60s", "Week 4": "60+s"}, ensure_ascii=False),
        "common_mistakes": "• Knees extending past your toes\n• Lower back separating from the wall\n• Holding your breath",
        "icon": "🧱",
        "category": "full_body"
    },
    {
        "order": 8,
        "name": "The Pallof Press Hold",
        "target_muscles": "Transverse abdominis, obliques, deep spinal stabilizers",
        "why_it_works": "The Pallof press is the gold standard for anti-rotation core strength. It forces your deep core to resist a rotational force — exactly what your body needs to keep your waist tight and stable. This exercise directly translates to a flatter belly in daily life.",
        "instructions": "1. Stand sideways to a wall, about arm's length away.\n2. Hold a towel or small weight against the wall with both hands at chest height.\n3. Walk your feet out until you feel tension in your core.\n4. Press the towel/weight straight out from your chest, arms extended.\n5. Your core must fight to keep your body from rotating toward the wall.\n6. Hold this extended position.\n7. Breathe steadily. Repeat on the other side.\n\n*No wall? Use a resistance band anchored to a door handle or heavy furniture.*",
        "modifications": "**Easier:** Stand closer to the wall (less leverage).\n**Harder:** Stand farther from the wall (more leverage). Hold for longer.",
        "easier_options": "Closer to wall, shorter hold",
        "harder_options": "Farther from wall, longer hold",
        "target_times": json.dumps({"Week 1": "15–20s per side", "Week 2": "20–30s", "Week 3": "30–40s", "Week 4": "40+s"}, ensure_ascii=False),
        "common_mistakes": "• Letting your shoulders round forward\n• Breathing shallow or holding breath\n• Using momentum instead of core control",
        "icon": "🔄",
        "category": "core"
    },
    {
        "order": 9,
        "name": "The Leg Raise Hold",
        "target_muscles": "Lower rectus abdominis, hip flexors, transverse abdominis",
        "why_it_works": "The lower belly is typically the most stubborn area for post-menopausal women. The leg raise hold isolates the lower rectus abdominis and forces the TVA to stabilize your pelvis. This is the most direct way to target the pooch below the belly button.",
        "instructions": "1. Lie on your back with legs straight, arms at your sides (palms down).\n2. Press your lower back firmly into the floor.\n3. Keeping legs straight, lift both legs to 90 degrees (perpendicular to floor).\n4. Your lower back must stay pressed into the floor.\n5. Hold this position.\n6. If your back arches, lift your legs higher until it flattens again.\n7. Breathe steadily — exhale as you lift, inhale as you hold.",
        "modifications": "**Easier:** Lift legs to 90° with knees slightly bent.\n**Harder:** Lower legs to 45° (harder on lower abs) while keeping back flat.",
        "easier_options": "90-degree with slight bend",
        "harder_options": "45-degree leg hold",
        "target_times": json.dumps({"Week 1": "15–25s", "Week 2": "25–35s", "Week 3": "35–45s", "Week 4": "45+s"}, ensure_ascii=False),
        "common_mistakes": "• Lower back arching off the floor\n• Using momentum instead of core control\n• Neck straining",
        "icon": "🦵",
        "category": "core"
    },
    {
        "order": 10,
        "name": "The Bear Crawl Hold",
        "target_muscles": "Full body — shoulders, core, glutes, quads",
        "why_it_works": "The bear crawl hold is the ultimate full-body isometric exercise. It requires simultaneous engagement of your shoulders, core, glutes, and legs. When you can hold this for 30 seconds, you have genuine full-body tension and core stability. This is the graduation exercise.",
        "instructions": "1. Start on your hands and knees.\n2. Tuck your toes under.\n3. Lift your knees 1–2 inches off the floor.\n4. Keep your back completely flat — like a table.\n5. Your knees should hover just above the ground.\n6. Pull your belly button toward your spine.\n7. Gaze at the floor between your hands.\n8. Hold. Your entire body should be shaking by the end.",
        "modifications": "**Easier:** Lift knees only ½ inch off the floor, or hold for shorter intervals.\n**Harder:** Crawl forward slowly while keeping your back flat (bear crawl walk).",
        "easier_options": "Lower knee lift, shorter holds",
        "harder_options": "Bear crawl walk",
        "target_times": json.dumps({"Week 1": "10–15s", "Week 2": "15–25s", "Week 3": "25–35s", "Week 4": "35+s"}, ensure_ascii=False),
        "common_mistakes": "• Back sagging or rounding (keep it flat like a table)\n• Knees touching the floor\n• Looking up (strains neck)",
        "icon": "🐻",
        "category": "full_body"
    }
]

ARTICLES = [
    {
        "title": "Understanding Post-Menopausal Belly Fat",
        "slug": "understanding-belly-fat",
        "category": "science",
        "summary": "Why your body stores fat differently after menopause and what you can do about it.",
        "content_md": """# Understanding Post-Menopausal Belly Fat

## What's Actually Happening to Your Body

Menopause isn't just the end of your menstrual cycle. It's a fundamental rewiring of your endocrine system, and it affects fat storage in three major ways:

### Estrogen Decline
Estrogen helps regulate where fat is stored. Before menopause, women tend to store fat in the hips, thighs, and buttocks (subcutaneous fat). After menopause, falling estrogen levels shift fat storage toward the abdomen (visceral fat). This isn't about calories alone — it's about hormonal signaling.

### Cortisol and Insulin Resistance
Post-menopausal women are more sensitive to cortisol (the stress hormone). Higher cortisol directly promotes belly fat storage, especially when combined with the insulin resistance that often accompanies menopause.

### Loss of Muscle Mass (Sarcopenia)
After age 50, women lose roughly 1–2% of muscle mass per year. Muscle is metabolically active tissue — it burns calories even at rest. Less muscle means a slower resting metabolism, which means more fat accumulation.

## Why Traditional Cardio and Crunches Don't Work

The standard advice — "do more cardio, eat less" — often backfires for post-menopausal women. Excessive cardio can spike cortisol, which triggers belly fat storage. Crunches build the "six-pack" muscle but do almost nothing for the deep core muscles that actually flatten the belly.

## What Works Instead

The right approach:
1. **Builds and preserves lean muscle** to raise your resting metabolism
2. **Targets the deep core** (transverse abdominis) to tighten from the inside out
3. **Keeps cortisol low** by avoiding high-intensity stress
4. **Is joint-friendly** and sustainable for decades

Isometric exercise checks every one of these boxes.
"""
    },
    {
        "title": "Why Isometric Exercise Is Your Secret Weapon",
        "slug": "why-isometric-exercise",
        "category": "science",
        "summary": "The science behind isometric holds and why they're perfect for post-menopausal women.",
        "content_md": """# Why Isometric Exercise Is Your Secret Weapon

## What Isometric Exercise Is

An isometric exercise is a muscle contraction **without movement**. You hold a position and maintain tension. Think of a plank: your muscles are working hard, but nothing is moving.

## The Science: Why It Works for Belly Fat

### 1. Deep Core Activation
Isometric holds force your transverse abdominis (TVA) — the deep corset muscle that wraps around your waist — to engage and stay engaged. This is the muscle that literally pulls your belly in. Traditional crunches barely touch it.

### 2. Hormonal Advantage
Isometric exercise produces a lower cortisol spike than high-intensity cardio or heavy lifting. For post-menopausal women already dealing with elevated cortisol, this matters enormously. Lower cortisol = less belly fat storage signaling.

### 3. Muscle Preservation Without Joint Stress
Isometric holds build muscular endurance and strength without pounding your joints. You can push to fatigue without impact, making this sustainable for women with knee, hip, or back concerns.

### 4. Afterburn Effect (EPOC)
Holding a muscle to failure creates significant metabolic stress. Your body continues burning calories at an elevated rate for hours after a session.

### 5. Time Efficiency
A complete isometric workout takes 15–25 minutes. No equipment, no gym, no changing clothes.

## The Research
A 2023 study in the *Journal of Strength and Conditioning Research* found that isometric training reduced waist circumference by an average of 2.8 cm over 8 weeks in post-menopausal women — significantly more than aerobic training alone.
"""
    },
    {
        "title": "The 4-Week Isometric Program",
        "slug": "4-week-program",
        "category": "program",
        "summary": "Your complete 4-week isometric exercise plan for a flatter belly and stronger core.",
        "content_md": """# The 4-Week Isometric Program

## The Commitment
- **Duration:** 4 weeks to see visible change; 12 weeks for dramatic results
- **Frequency:** 5 days per week, 15–25 minutes per session
- **Equipment:** None required. A yoga mat or carpeted floor, a wall, and a towel

## The Weekly Rhythm

 Day | Type | Purpose |
-----|------|---------|
 Monday | Core Focus | Deep abdominal activation |
 Tuesday | Full Body | Total muscle engagement |
 Wednesday | Core Focus | Deep abdominal activation |
 Thursday | Active Recovery | Gentle holds + walking |
 Friday | Full Body | Total muscle engagement |
 Saturday | Core Focus | Deep abdominal activation |
 Sunday | Rest | Complete rest |

## How to Perform Isometric Holds

1. **Get into position** with proper form (form always beats duration)
2. **Breathe steadily** — never hold your breath
3. **Hold until you feel the muscle burning**, then hold 5 more seconds
4. **Stop when form breaks down**, not when you're in pain
5. **Rest 30–60 seconds** between sets
6. **Track your time** — seeing your hold times increase is deeply motivating

## A Note on Breathing
This is the #1 mistake. **Breathe normally throughout every hold.** Holding your breath spikes blood pressure and reduces oxygen to your muscles. If you can't breathe while holding, you're either in the wrong position or pushing too hard.
"""
    },
    {
        "title": "Nutrition for Menopause: The 20% That Makes the 80% Difference",
        "slug": "nutrition-menopause",
        "category": "nutrition",
        "summary": "Simple, science-backed nutrition strategies that support your isometric training.",
        "content_md": """# Nutrition for Menopause

You can do every exercise in this guide perfectly, but if your nutrition isn't supporting you, results will be slower. Here's the 20% effort that delivers 80% of the results.

## 1. Protein at Every Meal
After menopause, your body is less efficient at using protein for muscle repair. Aim for 25–35g of protein per meal. This preserves muscle mass (which keeps your metabolism high) and keeps you full longer.

**Good sources:** Eggs, Greek yogurt, chicken, fish, tofu, lentils, protein shakes.

## 2. Cut Liquid Calories
Sugary coffee drinks, soda, juice, and alcohol are the fastest way to add calories without satiety. One fancy coffee drink can contain 300–500 calories — that's 20% of your daily needs in one drink.

## 3. Eat Within a 10-Hour Window
Time-restricted eating (e.g., eating between 10am and 8pm) helps regulate insulin sensitivity, which is often impaired after menopause. This alone can reduce belly fat storage signaling.

## 4. Prioritize Fiber
Fiber feeds your gut microbiome, stabilizes blood sugar, and keeps you full. Aim for 25–30g per day.

**Good sources:** Vegetables, berries, oats, chia seeds, flax seeds, legumes.

## 5. Hydrate
Dehydration is often mistaken for hunger. Aim for 8+ cups of water per day. Herbal tea counts. If you're feeling hungry between meals, drink a glass of water first and wait 10 minutes.
"""
    },
    {
        "title": "Tracking Your Progress Beyond the Scale",
        "slug": "tracking-progress",
        "category": "motivation",
        "summary": "The scale doesn't tell the full story. Here's what to track instead.",
        "content_md": """# Tracking Your Progress Beyond the Scale

The scale can be misleading, especially during menopause when water retention and hormonal fluctuations cause daily weight swings. Here's what actually matters:

## Weekly Measurements
Measure your waist at belly-button height once per week, first thing in the morning. This is the single most relevant metric for belly fat loss. A 1-inch loss over 4 weeks is excellent progress.

## Performance Tracking
Track your hold times. When you can hold a plank for 60 seconds (up from 20), that's real progress. Your workout logs will show strength gains long before the scale moves.

## Non-Scale Victories
- Jeans fit better
- Better sleep quality
- More energy during the day
- Less back pain
- Improved posture
- Feeling stronger in daily activities (carrying groceries, climbing stairs)
- Better mood and reduced anxiety

These matter more than any number on a scale. Celebrate them.
"""
    },
    {
        "title": "Frequently Asked Questions About Isometric Exercise",
        "slug": "isometric-faq",
        "category": "basics",
        "summary": "Common questions about isometric training for post-menopausal women.",
        "content_md": """# Frequently Asked Questions

**Q: How long until I see results?**
A: Most women notice their clothes fitting better within 2–3 weeks. Visible changes in belly firmness typically appear at 4 weeks. Significant waist reduction takes 8–12 weeks of consistent practice.

**Q: Can I do these exercises every day?**
A: The program calls for 5 days per week. Your muscles need recovery time to rebuild. Rest days are not optional — they're when your body adapts and gets stronger.

**Q: Do I need to diet too?**
A: Exercise and nutrition work together. The exercise builds muscle and burns calories; good nutrition ensures your body has the fuel it needs and doesn't store extra fat. They're a team.

**Q: I have lower back pain. Can I still do these?**
A: Most of these exercises strengthen the back when performed correctly. Start with the easier modifications, focus on perfect form, and stop if you feel sharp pain. The dead bug hold and glute bridge are especially good for back health.

**Q: Will this help with hot flashes?**
A: While isometric exercise doesn't directly treat hot flashes, regular exercise helps regulate your stress response and improve sleep quality — both of which can reduce the frequency and severity of hot flashes for many women.

**Q: What if I miss a day?**
A: Just pick up where you left off. Don't try to "make up" missed days by doubling up. Consistency over perfection is the goal. One missed day doesn't matter; a missed week does.
"""
    }
]


def seed_database(db):
    """Seed the database with initial data."""
    # Seed exercises if empty
    if Exercise.query.count() == 0:
        for ex_data in EXERCISES:
            exercise = Exercise(**ex_data)
            db.session.add(exercise)
        db.session.commit()
        print(f"Seeded {len(EXERCISES)} exercises")

    # Seed articles if empty
    if Article.query.count() == 0:
        for art_data in ARTICLES:
            article = Article(**art_data)
            db.session.add(article)
        db.session.commit()
        print(f"Seeded {len(ARTICLES)} articles")

    # Seed isochronic tones if empty
    if IsochronicTone.query.count() == 0:
        colors = ['#7c6ff7', '#d4436b', '#2ecc71', '#f1c40f',
                  '#e67e22', '#9b59b6', '#1abc9c', '#3498db']
        icons = ['💤', '🧘', '🌊', '🧠', '⚡', '🌤️', '🕯️', '🌅']
        for i, preset_id in enumerate(TONES_PRESETS):
            freq = TONES_FREQUENCIES[preset_id]
            tone = IsochronicTone(
                preset_id=preset_id,
                name=TONES_LABELS[preset_id],
                description=freq['description'],
                carrier_freq=freq['carrier'],
                beat_freq=freq['beat'],
                brainwave_label=freq['brainwave'],
                icon=icons[i],
                color=colors[i],
                duration_min=15
            )
            db.session.add(tone)
        db.session.commit()
        print(f"Seeded {len(TONES_PRESETS)} isochronic tones")

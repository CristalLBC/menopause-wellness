"""
Symptom Decoder — maps menopause symptoms to recommendations.

Each symptom maps to:
- exercises: list of exercise IDs that target that symptom
- tones: list of tone preset_ids that help that symptom
- stages: menopause stages where this symptom is most common (for stage inference)
- articles: list of article slugs
- explanation: simple physiology explanation (for the "why" popup)
"""

# Stage definitions for inference
STAGES = {
    'early_perimenopause': {
        'label': 'Early Perimenopause (approx. 35–45)',
        'description': 'Cycles may start changing — shorter, longer, heavier, lighter. Occasional hot flashes, mood shifts, and sleep disruptions begin. Fertility declines but is still possible.',
        'color': 'amber',
        'emoji': '🌱'
    },
    'late_perimenopause': {
        'label': 'Late Perimenopause (approx. 45–51)',
        'description': 'The most symptomatic phase. Cycles are 60+ days apart or skipping entirely. Hot flashes, night sweats, brain fog, and mood swings intensify. This is the "rollercoaster" stage.',
        'color': 'rose',
        'emoji': '🎢'
    },
    'menopause': {
        'label': 'Menopause (12 months without a period)',
        'description': 'You have officially reached menopause after one full year with no period. Symptoms like hot flashes may still be intense but are beginning to stabilise.',
        'color': 'pink',
        'emoji': '🔄'
    },
    'post_menopause': {
        'label': 'Post-Menopause (Ages 51+)',
        'description': 'The dust has settled hormonally. Hot flashes often ease, but bone density, joint health, vaginal changes, and metabolic shifts become the main focus areas.',
        'color': 'emerald',
        'emoji': '🌿'
    }
}

# Symptom-to-stage weights (how strongly each symptom indicates a stage)
# Higher number = stronger indicator
SYMPTOM_STAGE_WEIGHTS = {
    'hot_flashes':  {'early_perimenopause': 2, 'late_perimenopause': 5, 'menopause': 4, 'post_menopause': 2},
    'night_sweats': {'early_perimenopause': 2, 'late_perimenopause': 5, 'menopause': 4, 'post_menopause': 2},
    'mood_swings':  {'early_perimenopause': 3, 'late_perimenopause': 5, 'menopause': 3, 'post_menopause': 1},
    'fatigue':      {'early_perimenopause': 1, 'late_perimenopause': 4, 'menopause': 3, 'post_menopause': 3},
    'brain_fog':    {'early_perimenopause': 2, 'late_perimenopause': 5, 'menopause': 3, 'post_menopause': 2},
    'sleep_issues': {'early_perimenopause': 2, 'late_perimenopause': 5, 'menopause': 4, 'post_menopause': 2},
    'joint_pain':   {'early_perimenopause': 1, 'late_perimenopause': 2, 'menopause': 3, 'post_menopause': 5},
    'headaches':    {'early_perimenopause': 3, 'late_perimenopause': 4, 'menopause': 2, 'post_menopause': 1},
    'anxiety':      {'early_perimenopause': 3, 'late_perimenopause': 5, 'menopause': 3, 'post_menopause': 2},
    'bloating':     {'early_perimenopause': 2, 'late_perimenopause': 3, 'menopause': 2, 'post_menopause': 2},
    'weight_gain':  {'early_perimenopause': 1, 'late_perimenopause': 2, 'menopause': 4, 'post_menopause': 5},
    'low_libido':   {'early_perimenopause': 1, 'late_perimenopause': 3, 'menopause': 4, 'post_menopause': 4}
}

# Extended descriptions for each symptom (for the "why" explainer)
SYMPTOM_EXPLANATIONS = {
    'hot_flashes': 'Your brain\'s thermostat (hypothalamus) becomes hypersensitive when estrogen drops. It misreads normal body temperature as overheating and triggers emergency cooling — dilating blood vessels and activating sweat glands.',
    'night_sweats': 'The same thermostat misfire as hot flashes, but happening during sleep. Your body dumps heat while you\'re unconscious, often waking you drenched. The drop in core temperature can also trigger an adrenaline surge at 3–4 AM.',
    'mood_swings': 'Estrogen and progesterone modulate serotonin and dopamine — your "feel-good" neurotransmitters. When these hormones fluctuate wildly, your brain chemistry goes on a rollercoaster, causing irritability, weepiness, and emotional sensitivity.',
    'fatigue': 'Your mitochondria (cellular energy factories) depend on estrogen for efficient function. When estrogen declines, every cell has to work harder to produce energy. This is physical, not mental — no amount of coffee fixes low cellular energy.',
    'brain_fog': 'Estrogen is a direct fuel for brain cells. It increases glucose uptake in the hippocampus and prefrontal cortex — areas responsible for memory and focus. When estrogen drops, those brain regions experience an energy shortage, slowing recall.',
    'sleep_issues': 'Progesterone is a natural sedative. When it declines, falling and staying asleep becomes harder. Combined with night sweats and midnight adrenaline surges, menopause creates the perfect storm for broken sleep.',
    'joint_pain': 'Estrogen keeps joint tissues hydrated and lubricated. Without it, cartilage dries out and becomes less flexible, tendons lose elasticity, and inflammation markers rise. The result: achy, stiff joints that feel 20 years older.',
    'headaches': 'Estrogen influences blood vessel dilation in the brain. The rapid drops and spikes during perimenopause can trigger vascular headaches and migraines, especially around what used to be your menstrual cycle.',
    'anxiety': 'The same hormonal fluctuations that affect serotonin also affect GABA — your brain\'s natural "brake pedal." When GABA is low, your nervous system stays in a heightened state of arousal, producing that wired-but-tired anxious feeling.',
    'bloating': 'Hormonal shifts alter gut motility and the balance of gut bacteria. Digestion slows, gas builds up, and your body retains more water. What feels like weight gain is often just your digestive system moving at half speed.',
    'weight_gain': 'Lower estrogen shifts fat storage from hips/thighs (subcutaneous) to the belly (visceral). Combined with muscle loss (sarcopenia) starting around age 50, your resting metabolism slows, making it easier to gain weight even eating the same calories.',
    'low_libido': 'Estrogen drives vaginal blood flow and lubrication; testosterone (present in smaller amounts in women) drives desire. Both decline after menopause. Add in sleep deprivation, body image changes, and vaginal dryness, and libido naturally drops.'
}

# Recommended exercises by symptom (exercise order numbers, 1-15)
SYMPTOM_EXERCISES = {
    'hot_flashes':  [7, 11, 6],   # Wall Sit, Heel Raise, Bird Dog
    'night_sweats': [7, 11, 9],   # Wall Sit, Heel Raise, Leg Raise
    'mood_swings':  [6, 12, 10],  # Bird Dog, Single-Leg Balance, Bear Crawl
    'fatigue':      [7, 10, 1],   # Wall Sit, Bear Crawl, Front Plank
    'brain_fog':    [6, 12, 8],   # Bird Dog, Single-Leg Balance, Pallof Press
    'sleep_issues': [3, 13],      # Dead Bug, Wall Angel
    'joint_pain':   [14, 13, 11], # Clamshell, Wall Angel, Heel Raise
    'headaches':    [13, 15, 13], # Wall Angel, Prone Back Extension
    'anxiety':      [3, 6, 5],    # Dead Bug, Bird Dog, Glute Bridge
    'bloating':     [1, 2, 3, 9, 4],  # Front Plank, Side Plank, Dead Bug, Leg Raise, Hollow Body
    'weight_gain':  [7, 10, 1, 4],    # Wall Sit, Bear Crawl, Front Plank, Hollow Body
    'low_libido':   [14, 5, 3]    # Clamshell, Glute Bridge, Dead Bug
}

# Recommended tones by symptom (preset_ids)
SYMPTOM_TONES = {
    'hot_flashes':  ['hot_flash_calm', 'deep_relaxation'],
    'night_sweats': ['hot_flash_calm', 'sleep', 'deep_relaxation'],
    'mood_swings':  ['mood_lift', 'stress_resilience', 'anxiety_relief'],
    'fatigue':      ['energy_boost', 'afternoon_recharge', 'morning_wakeup'],
    'brain_fog':    ['brain_focus', 'confidence_clarity', 'morning_wakeup'],
    'sleep_issues': ['sleep', 'deep_relaxation', 'anxiety_relief'],
    'joint_pain':   ['pain_comfort', 'deep_relaxation', 'stress_resilience'],
    'headaches':    ['pain_comfort', 'anxiety_relief', 'deep_relaxation'],
    'anxiety':      ['anxiety_relief', 'stress_resilience', 'deep_relaxation'],
    'bloating':     ['deep_relaxation', 'stress_resilience', 'mood_lift'],
    'weight_gain':  ['energy_boost', 'morning_wakeup', 'confidence_clarity'],
    'low_libido':   ['libido_sensuality', 'confidence_clarity', 'mood_lift']
}

# Recommended articles by symptom (slugs)
SYMPTOM_ARTICLES = {
    'hot_flashes':  ['why-isometric-exercise', 'understanding-belly-fat'],
    'night_sweats': ['why-isometric-exercise', 'nutrition-menopause'],
    'mood_swings':  ['why-isometric-exercise', 'tracking-progress'],
    'fatigue':      ['why-isometric-exercise', 'nutrition-menopause'],
    'brain_fog':    ['why-isometric-exercise', '4-week-program'],
    'sleep_issues': ['why-isometric-exercise', 'tracking-progress'],
    'joint_pain':   ['why-isometric-exercise', 'nutrition-menopause'],
    'headaches':    ['why-isometric-exercise', 'tracking-progress'],
    'anxiety':      ['why-isometric-exercise', 'tracking-progress'],
    'bloating':     ['understanding-belly-fat', 'nutrition-menopause'],
    'weight_gain':  ['understanding-belly-fat', 'nutrition-menopause', '4-week-program'],
    'low_libido':   ['why-isometric-exercise', 'nutrition-menopause', '4-week-program']
}

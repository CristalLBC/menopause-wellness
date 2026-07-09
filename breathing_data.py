"""
Breathing exercise patterns for the guided breathing timer.

Each pattern defines:
- name: Display name
- description: Short explanation
- phases: List of {phase: 'inhale'|'hold'|'exhale', duration: seconds}
- rounds: How many times to repeat the phase sequence
- instruction: What to tell the user

Total time = sum(phase durations) * rounds
"""

BREATHING_PATTERNS = {
    'wim_hof': {
        'name': '🌬️ Wim Hof Morning Breath',
        'subtitle': 'Energize, build focus, reduce stress',
        'description': 'A powerful breathing technique developed by Wim Hof. Rapid deep breathing followed by breath retention increases oxygen levels and builds mental resilience. Best done first thing in the morning on an empty stomach.',
        'color': '#f59e0b',
        'bg_gradient': 'from-amber-900/40 via-amber-800/20 to-amber-950/40',
        'total_minutes': 11,
        'rounds': 3,
        'phases_per_round': [
            # 40 deep breaths at ~3s each = 120 seconds
            {'phase': 'rapid', 'label': 'Breathe Deeply', 'duration': 120, 'instruction': 'Deep inhale through your belly, relaxed exhale through your mouth. Like a wave — in, then let go. 40 breaths.'},
            # Exhale + hold
            {'phase': 'exhale', 'label': 'Breathe Out', 'duration': 3, 'instruction': 'Exhale all the air. Empty your lungs completely.'},
            # Retention hold
            {'phase': 'hold_empty', 'label': 'Hold — No Air', 'duration': 60, 'instruction': 'Hold your breath with empty lungs. Listen to your body. When you feel the urge, take a recovery breath.'},
            # Recovery breath
            {'phase': 'inhale', 'label': 'Recovery Breath', 'duration': 4, 'instruction': 'Inhale deeply — fill your lungs to maximum capacity.'},
            # Hold with full lungs
            {'phase': 'hold_full', 'label': 'Hold — Full Lungs', 'duration': 15, 'instruction': 'Hold with full lungs. Feel the oxygen rush through your body.'},
            # Exhale recovery
            {'phase': 'exhale', 'label': 'Breathe Out', 'duration': 4, 'instruction': 'Slowly exhale. Notice how your body feels. Prepare for the next round.'},
        ],
        'transition_msg': 'Round {round} complete. Take a normal breath and begin the next round when ready.',
        'complete_msg': 'Round 3 complete. Sit quietly for 30 seconds and notice how your body feels. Tingling is normal — you\'ve just activated your nervous system.'
    },
    'four_seven_eight': {
        'name': '🧘 4-7-8 Deep Relaxation',
        'subtitle': 'The "relaxation breath" — fall asleep faster, calm anxiety',
        'description': 'Developed by Dr. Andrew Weil, the 4-7-8 breath activates your parasympathetic nervous system — your body\'s "rest and digest" mode. The extended hold and long exhale signal your nervous system that it is safe to relax.',
        'color': '#8b5cf6',
        'bg_gradient': 'from-indigo-900/40 via-purple-800/20 to-indigo-950/40',
        'total_minutes': 6,
        'rounds': 8,
        'phases_per_round': [
            {'phase': 'inhale', 'label': 'Breathe In', 'duration': 4, 'instruction': 'Close your mouth and inhale quietly through your nose. Fill your belly, not just your chest.'},
            {'phase': 'hold_full', 'label': 'Hold', 'duration': 7, 'instruction': 'Hold your breath. Keep your throat relaxed. Feel the air pressure.'},
            {'phase': 'exhale', 'label': 'Breathe Out', 'duration': 8, 'instruction': 'Exhale completely through your mouth with a gentle whoosh sound. All the way out.'},
        ],
        'transition_msg': 'Round {round} complete. Release any tension you noticed. Prepare for the next round.',
        'complete_msg': 'You\'ve completed 8 rounds of 4-7-8 breathing. Your heart rate has slowed and your nervous system has shifted toward calm. Sit with the feeling for a moment.'
    },
    'box_breathing': {
        'name': '⬜ Box Breathing',
        'subtitle': 'Used by Navy SEALs — instant calm under pressure',
        'description': 'Also known as tactical breathing. Equal parts inhale, hold, exhale, hold — creates a perfect square pattern. Used by military and first responders to stay calm in high-stress situations.',
        'color': '#06b6d4',
        'bg_gradient': 'from-cyan-900/40 via-teal-800/20 to-cyan-950/40',
        'total_minutes': 5,
        'rounds': 10,
        'phases_per_round': [
            {'phase': 'inhale', 'label': 'Breathe In', 'duration': 4, 'instruction': 'Inhale steadily through your nose. Fill your lungs completely over 4 seconds.'},
            {'phase': 'hold_full', 'label': 'Hold', 'duration': 4, 'instruction': 'Hold with full lungs. No tension in your shoulders or jaw.'},
            {'phase': 'exhale', 'label': 'Breathe Out', 'duration': 4, 'instruction': 'Exhale slowly and completely through your mouth. Empty every bit of air.'},
            {'phase': 'hold_empty', 'label': 'Hold', 'duration': 4, 'instruction': 'Hold with empty lungs. Notice the stillness before your next inhale.'},
        ],
        'transition_msg': 'Round {round} complete. Stay calm. Keep the rhythm square.',
        'complete_msg': 'Box breathing complete. Your nervous system has been reset. Carry this square rhythm with you into the rest of your day.'
    },
    'calming_wave': {
        'name': '🌊 Calming Wave',
        'subtitle': 'Lengthened exhale to lower heart rate fast',
        'description': 'A gentle, wave-like breath where the exhale is longer than the inhale. This directly stimulates the vagus nerve, slowing your heart rate and activating your body\'s relaxation response. Perfect for hot flash onset or racing thoughts.',
        'color': '#14b8a6',
        'bg_gradient': 'from-emerald-900/40 via-teal-800/20 to-emerald-950/40',
        'total_minutes': 8,
        'rounds': 12,
        'phases_per_round': [
            {'phase': 'inhale', 'label': 'Breathe In', 'duration': 4, 'instruction': 'Gently inhale through your nose. Imagine a wave rising up your body from your toes to your chest.'},
            {'phase': 'exhale', 'label': 'Breathe Out', 'duration': 6, 'instruction': 'Slowly exhale through your mouth. Make the exhale longer and softer than the inhale. Like the wave rolling back out.'},
        ],
        'transition_msg': 'Wave {round} complete. Feel the rhythm. Each exhale is a little deeper.',
        'complete_msg': 'The waves have settled. Your exhale has been longer than your inhale for 12 cycles — your vagus nerve has been activated and your heart rate has naturally slowed. Rest here.'
    }
}

# Bonus: quick 1-minute "Emergency Calm" for panic moments
EMERGENCY_CALM = {
    'name': '⚡ Emergency Calm (1 min)',
    'description': 'A lightning-fast version of the calming wave for when a hot flash hits or anxiety spikes. Just 5 breaths, 60 seconds.',
    'phases': [
        {'phase': 'inhale', 'label': 'Breathe In', 'duration': 4, 'instruction': 'Quick inhale through your nose.'},
        {'phase': 'exhale', 'label': 'Breathe Out', 'duration': 8, 'instruction': 'Long, slow exhale through your mouth. Make it longer than the inhale.'},
    ],
    'rounds': 5
}

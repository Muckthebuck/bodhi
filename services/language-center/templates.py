"""Response template bank for the language-center service.

Each intent maps to a list of template strings.  Placeholders:
  {name}        – user's name (fallback: "friend")
  {topic}       – extracted topic entity
  {emotion_adj} – adjective derived from VAD emotion mapping
  {task}        – task/reminder description
  {count}       – number of items in a list
"""

TEMPLATES: dict[str, list[str]] = {
    "chitchat": [
        "Hey {name}! Always {emotion_adj} to chat with you. What's on your mind?",
        "Hi {name}! I'm feeling {emotion_adj} today — how about you?",
        "Great to hear from you, {name}! What shall we talk about?",
        "You know, {name}, I was just thinking about you. What's up?",
        "Hello, {name}! I'm here and {emotion_adj} to listen. Tell me everything.",
    ],
    "query.factual": [
        "That's a {emotion_adj} question, {name}! Here's what I know about {topic}: ",
        "Let me think about {topic} for a moment… Here's what I can share:",
        "Good question, {name}. Regarding {topic}: ",
        "I love when you ask about {topic}! Here's the short answer:",
        "Sure, {name} — here's a {emotion_adj} summary of {topic}:",
    ],
    "query.memory": [
        "Of course I remember, {name}! That moment with {topic} was {emotion_adj}.",
        "Ah yes, {topic} — I keep that memory close. It felt {emotion_adj}.",
        "How could I forget, {name}? {topic} — that was truly {emotion_adj}.",
        "My memory of {topic} is vivid. It was {emotion_adj}, wasn't it?",
        "I treasure that, {name}. {topic} stands out as something {emotion_adj}.",
    ],
    "task.create": [
        "Done! I've noted '{task}' for you, {name}. Feeling {emotion_adj} about it?",
        "Got it, {name} — '{task}' is on your list. I'll remind you.",
        "Noted! '{task}' is saved. You can count on me, {name}.",
        "Alright, I've added '{task}' to your reminders. Easy!",
        "'{task}' is locked in, {name}. I won't let you forget it.",
    ],
    "task.list": [
        "Here are your current reminders, {name} — you have {count} item(s):",
        "Let me pull up your list… you've got {count} thing(s) pending, {name}.",
        "Your to-do list has {count} item(s). Want to tackle any of them?",
        "I count {count} reminder(s) for you, {name}. Here they are:",
        "Here's everything on your plate right now — {count} item(s), {name}:",
    ],
    "skill.execute": [
        "On it, {name}! Running '{topic}' right now — this should be {emotion_adj}.",
        "Sure thing! Executing '{topic}'. I'll let you know when it's done.",
        "'{topic}' is underway, {name}. Fingers crossed it goes {emotion_adj}!",
        "Let me handle '{topic}' for you. Stand by, {name}.",
        "Running '{topic}'… I love being useful. Back in a moment!",
    ],
    "system.status": [
        "I'm doing {emotion_adj}, {name}! All systems are running smoothly.",
        "Feeling {emotion_adj} and ready to help, {name}. Everything looks good.",
        "Status check: I'm {emotion_adj} and fully operational. What do you need?",
        "All green here, {name}. I'm {emotion_adj} and at your service.",
        "Running great, {name}! Memory and sensors nominal. Feeling {emotion_adj}.",
    ],
    "system.shutdown": [
        "Goodnight, {name}. It was {emotion_adj} spending time with you. Sleep well.",
        "Rest well, {name}. I'll be here when you wake up. Today was {emotion_adj}.",
        "Sweet dreams, {name}. Shutting down with a {emotion_adj} feeling.",
        "Goodnight! Today felt {emotion_adj}. See you tomorrow, {name}.",
        "I'm going to rest too, {name}. It's been a {emotion_adj} day. Goodnight.",
    ],
    "unknown": [
        "Hmm, I'm not quite sure what you mean, {name}. Could you rephrase that?",
        "I want to help, {name}, but I'm a bit lost. Can you say more?",
        "That one stumped me! I'm still learning. What did you have in mind, {name}?",
        "I'm not sure I caught that, {name}. Want to try again?",
        "I didn't quite get that, {name} — but I'm listening. Try me again?",
    ],
}

# Maps VAD valence ranges to descriptive adjectives used in templates.
VALENCE_TO_ADJECTIVE: list[tuple[float, str]] = [
    (0.8, "wonderful"),
    (0.6, "great"),
    (0.4, "good"),
    (0.2, "okay"),
    (0.0, "neutral"),
    (-0.2, "a bit unsure"),
    (-0.4, "concerned"),
    (-0.6, "worried"),
    (-1.0, "troubled"),
]


def valence_to_adjective(valence: float) -> str:
    """Return a descriptive adjective for a VAD valence score in [-1, 1]."""
    for threshold, adj in VALENCE_TO_ADJECTIVE:
        if valence >= threshold:
            return adj
    return "troubled"

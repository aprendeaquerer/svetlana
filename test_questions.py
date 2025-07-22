# Test questions and scoring system
TEST_QUESTIONS = {
    "es": [
        {
            "question": "¿Cómo te sientes cuando tu pareja no responde a tus mensajes inmediatamente?",
            "options": [
                {"text": "Me preocupo y pienso que algo está mal", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "Me enfado y me distancio", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "Entiendo que puede estar ocupada", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Me siento confundido y no sé qué hacer", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "¿Qué haces cuando tienes un problema importante?",
            "options": [
                {"text": "Busco apoyo y lo comparto con mi pareja", "scores": {"anxious": 1, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Prefiero resolverlo solo/a", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "Me siento abrumado y no sé a quién acudir", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}},
                {"text": "Me preocupo por cómo afectará a la relación", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}}
            ]
        },
        {
            "question": "¿Cómo reaccionas ante una discusión de pareja?",
            "options": [
                {"text": "Intento hablar y resolverlo pronto", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Me alejo y necesito espacio", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "Me angustio y temo que la relación termine", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "No sé cómo actuar y cambio de actitud", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "¿Qué piensas sobre la independencia en la pareja?",
            "options": [
                {"text": "Es importante, pero también la cercanía", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Prefiero mantener mi espacio personal", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "Me da miedo que la distancia signifique desinterés", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "A veces quiero estar cerca y otras lejos", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "¿Cómo te sientes cuando tu pareja expresa emociones fuertes?",
            "options": [
                {"text": "Puedo escuchar y acompañar", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Me incomoda y prefiero evitar el tema", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "Me preocupo y siento que debo calmarla", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "No sé cómo reaccionar y a veces cambio de tema", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "¿Qué haces si tu pareja necesita tiempo a solas?",
            "options": [
                {"text": "Lo respeto y aprovecho para hacer mis cosas", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Me siento rechazado/a o inseguro/a", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "Me molesta y me distancio también", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "No sé si acercarme o alejarme", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "¿Cómo te sientes cuando tu pareja te hace una crítica?",
            "options": [
                {"text": "Escucho y trato de mejorar", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Me siento herido/a y temo perder su amor", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "Me cierro y evito hablar del tema", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "Reacciono de forma impredecible", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "¿Qué piensas sobre pedir ayuda a tu pareja?",
            "options": [
                {"text": "Es natural y fortalece la relación", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Prefiero no depender de nadie", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "Me da miedo que me juzgue o rechace", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "A veces pido ayuda y otras no sé cómo hacerlo", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "¿Cómo reaccionas si tu pareja se muestra distante?",
            "options": [
                {"text": "Le pregunto si todo está bien y espero su respuesta", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Me preocupo y busco más cercanía", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "Me alejo también para protegerme", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "No sé si insistir o dejarlo pasar", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "¿Qué importancia le das a la confianza en la relación?",
            "options": [
                {"text": "Es fundamental y la cuido día a día", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Me cuesta confiar plenamente", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "Prefiero no depender de la confianza", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "A veces confío y otras no sé si debería", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}}
            ]
        }
    ]
}

def calculate_attachment_style(scores):
    max_score = max(scores.values())
    predominant_styles = [style for style, score in scores.items() if score == max_score]
    return predominant_styles[0] if predominant_styles else "secure"

def get_style_description(style, language="es"):
    descriptions = {
        "es": {
            "secure": "Seguro: Te sientes cómodo con la intimidad y la independencia.",
            "anxious": "Ansioso: Buscas mucha cercanía y te preocupas por el rechazo.",
            "avoidant": "Evitativo: Prefieres mantener distancia emocional.",
            "disorganized": "Desorganizado: Tienes patrones contradictorios."
        }
    }
    return descriptions.get(language, descriptions["es"]).get(style, "") 
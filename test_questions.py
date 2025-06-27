# Test questions and scoring system
TEST_QUESTIONS = {
    "es": [
        {
            "question": "Cuando estás en una relación, ¿cómo sueles reaccionar cuando tu pareja no responde a tus mensajes inmediatamente?",
            "options": [
                {"text": "Me preocupo y pienso que algo está mal", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "Me enfado y me distancio", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "Entiendo que puede estar ocupada", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Me siento confundido y no sé qué hacer", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "¿Cómo te sientes cuando tu pareja quiere pasar mucho tiempo contigo?",
            "options": [
                {"text": "Me siento feliz y seguro", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Me siento abrumado y necesito espacio", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "Me preocupa que se aburra de mí", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "Me siento confundido entre querer cercanía y miedo", "scores": {"anxious": 1, "avoidant": 1, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "Cuando hay un conflicto en tu relación, ¿qué sueles hacer?",
            "options": [
                {"text": "Busco resolverlo hablando abiertamente", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Me alejo y necesito tiempo para pensar", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "Me siento muy ansioso y busco resolverlo inmediatamente", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "Me siento paralizado y no sé cómo actuar", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "¿Cómo te sientes con la intimidad emocional en tus relaciones?",
            "options": [
                {"text": "Me siento cómodo compartiendo mis sentimientos", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Me cuesta abrirme emocionalmente", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "Necesito mucha confirmación de que me quieren", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "A veces quiero intimidad y a veces me asusta", "scores": {"anxious": 1, "avoidant": 1, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "¿Cómo te sientes cuando tu pareja tiene amigos del sexo opuesto?",
            "options": [
                {"text": "Me siento seguro y confío en ella", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Me siento celoso y preocupado", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "Me da igual, prefiero mi independencia", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "Me siento confundido entre confiar y desconfiar", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}}
            ]
        }
    ],
    "en": [
        {
            "question": "When you're in a relationship, how do you usually react when your partner doesn't respond to your messages immediately?",
            "options": [
                {"text": "I worry and think something is wrong", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "I get angry and distance myself", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "I understand they might be busy", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "I feel confused and don't know what to do", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "How do you feel when your partner wants to spend a lot of time with you?",
            "options": [
                {"text": "I feel happy and secure", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "I feel overwhelmed and need space", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "I worry they'll get bored of me", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "I feel confused between wanting closeness and fear", "scores": {"anxious": 1, "avoidant": 1, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "When there's a conflict in your relationship, what do you usually do?",
            "options": [
                {"text": "I seek to resolve it by talking openly", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "I distance myself and need time to think", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "I feel very anxious and seek to resolve it immediately", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "I feel paralyzed and don't know how to act", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "How do you feel about emotional intimacy in your relationships?",
            "options": [
                {"text": "I feel comfortable sharing my feelings", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "I have difficulty opening up emotionally", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "I need a lot of confirmation that they love me", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "Sometimes I want intimacy and sometimes it scares me", "scores": {"anxious": 1, "avoidant": 1, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "How do you feel when your partner has friends of the opposite sex?",
            "options": [
                {"text": "I feel secure and trust them", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "I feel jealous and worried", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "I don't care, I prefer my independence", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "I feel confused between trusting and distrusting", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}}
            ]
        }
    ],
    "ru": [
        {
            "question": "Когда ты в отношениях, как ты обычно реагируешь, когда твоя партнерша не отвечает на твои сообщения сразу?",
            "options": [
                {"text": "Я беспокоюсь и думаю, что что-то не так", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "Я злюсь и отдаляюсь", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "Я понимаю, что она может быть занята", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Я чувствую себя растерянным и не знаю, что делать", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "Как ты себя чувствуешь, когда твоя партнерша хочет проводить много времени с тобой?",
            "options": [
                {"text": "Я чувствую себя счастливым и безопасным", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Я чувствую себя перегруженным и нуждаюсь в пространстве", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "Я беспокоюсь, что она устанет от меня", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "Я чувствую себя растерянным между желанием близости и страхом", "scores": {"anxious": 1, "avoidant": 1, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "Когда в твоих отношениях есть конфликт, что ты обычно делаешь?",
            "options": [
                {"text": "Я ищу решение через открытый разговор", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Я отдаляюсь и нуждаюсь во времени подумать", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "Я чувствую себя очень тревожным и ищу немедленного решения", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "Я чувствую себя парализованным и не знаю, как действовать", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "Как ты себя чувствуешь с эмоциональной близостью в твоих отношениях?",
            "options": [
                {"text": "Я чувствую себя комфортно, делясь своими чувствами", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Мне трудно эмоционально открываться", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "Мне нужно много подтверждений, что меня любят", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "Иногда я хочу близости, а иногда это пугает меня", "scores": {"anxious": 1, "avoidant": 1, "secure": 0, "disorganized": 2}}
            ]
        },
        {
            "question": "Как ты себя чувствуешь, когда у твоей партнерши есть друзья противоположного пола?",
            "options": [
                {"text": "Я чувствую себя безопасно и доверяю ей", "scores": {"anxious": 0, "avoidant": 0, "secure": 2, "disorganized": 0}},
                {"text": "Я чувствую себя ревнивым и обеспокоенным", "scores": {"anxious": 2, "avoidant": 0, "secure": 0, "disorganized": 1}},
                {"text": "Мне все равно, я предпочитаю свою независимость", "scores": {"anxious": 0, "avoidant": 2, "secure": 0, "disorganized": 1}},
                {"text": "Я чувствую себя растерянным между доверием и недоверием", "scores": {"anxious": 1, "avoidant": 0, "secure": 0, "disorganized": 2}}
            ]
        }
    ]
}

def calculate_attachment_style(scores):
    """Calculate the predominant attachment style based on scores"""
    max_score = max(scores.values())
    predominant_styles = [style for style, score in scores.items() if score == max_score]
    
    if len(predominant_styles) > 1:
        # If there's a tie, return the first one (could be enhanced with more logic)
        return predominant_styles[0]
    return predominant_styles[0]

def get_style_description(style, language="es"):
    """Get description for each attachment style"""
    descriptions = {
        "es": {
            "secure": "Seguro: Te sientes cómodo con la intimidad y la independencia. Puedes mantener relaciones saludables y equilibradas.",
            "anxious": "Ansioso: Buscas mucha cercanía y te preocupas por el rechazo. Necesitas confirmación constante de que te quieren.",
            "avoidant": "Evitativo: Prefieres mantener distancia emocional. Te sientes más cómodo con la independencia que con la intimidad.",
            "disorganized": "Desorganizado: Tienes patrones contradictorios. A veces buscas cercanía y a veces la evitas, sintiéndote confundido."
        },
        "en": {
            "secure": "Secure: You feel comfortable with intimacy and independence. You can maintain healthy and balanced relationships.",
            "anxious": "Anxious: You seek a lot of closeness and worry about rejection. You need constant confirmation that you are loved.",
            "avoidant": "Avoidant: You prefer to maintain emotional distance. You feel more comfortable with independence than intimacy.",
            "disorganized": "Disorganized: You have contradictory patterns. Sometimes you seek closeness and sometimes you avoid it, feeling confused."
        },
        "ru": {
            "secure": "Безопасный: Ты чувствуешь себя комфортно с близостью и независимостью. Ты можешь поддерживать здоровые и сбалансированные отношения.",
            "anxious": "Тревожный: Ты ищешь много близости и беспокоишься об отвержении. Тебе нужно постоянное подтверждение, что тебя любят.",
            "avoidant": "Избегающий: Ты предпочитаешь поддерживать эмоциональную дистанцию. Ты чувствуешь себя более комфортно с независимостью, чем с близостью.",
            "disorganized": "Дезорганизованный: У тебя противоречивые паттерны. Иногда ты ищешь близости, а иногда избегаешь её, чувствуя себя растерянным."
        }
    }
    return descriptions.get(language, descriptions["es"]).get(style, "") 
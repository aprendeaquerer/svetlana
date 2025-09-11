# Test questions and scoring system
TEST_QUESTIONS = {
    "es": [
        {
            "question": "1. Cuando alguien me cuenta algo personal…",
            "options": [
                {"text": "A) Me gusta que confien en mi, escucho con calma y conecto con lo que sienten", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Me encanta y enseguida quiero contar mis propias experiencias para sentirnos mas unidos", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) A veces me engancho mucho, otras me siento raro y no se como reaccionar", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}},
                {"text": "D) Me cuesta, prefiero cambiar de tema o quitarle seriedad con una broma", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}}
            ]
        },
        {
            "question": "2. Cuando una relación empieza a ponerse seria o muy cercana…",
            "options": [
                {"text": "A) Lo vivo con calma, disfruto de la cercanía y no siento que tenga que sacrificar mi espacio personal", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Me engancho rápido y quiero pasar todo el tiempo con esa persona, me cuesta soltarla", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) Al principio me acerco con muchas ganas, pero luego me agobio y necesito alejarme sin saber bien por qué", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}},
                {"text": "D) Me da miedo tanto compromiso y termino saboteándolo o alejandome para protegerme", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}}
            ]
        },
        {
            "question": "3. Cuando discuto con alguien importante…",
            "options": [
                {"text": "A) Confío en que lo podemos hablarlo y resolverlo sin que la relación sufra", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Lo paso fatal, tengo miedo de que se enfade conmigo y me deje", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) Puedo pasar del cariño al enfado muy rápido y luego me arrepiento de como reacciono", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}},
                {"text": "D) Yo no discuto, prefiero irme antes incluso de que la otra persona pueda decir algo", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}}
            ]
        },
        {
            "question": "4. Si alguien cercano tarda en contestar un mensaje…",
            "options": [
                {"text": "A) Suelo pensar que estará ocupado/a, confío en la relación y no me hago lios en la cabeza", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Me pongo inquieto/a, empiezo a darle vueltas y pienso si habré dicho o hecho algo mal", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) Primero me preocupo mucho, me siento ignorado/a, luego me enfado y termino alejándome para protegerme", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}},
                {"text": "D) No le doy importancia, sigo a lo mío y ni siquiera reviso el móvil esperando respuesta", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}}
            ]
        },
        {
            "question": "5. Cuando tengo que mostrar mi parte vulnerable…",
            "options": [
                {"text": "A) Lo digo tal cual, confío en que la otra persona lo va a entender", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Lo muestro pero con miedo de que me juzguen o me dejen de lado, y necesito que me tranquilicen para sentirme seguro", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) Tan pronto lloro contigo, como no digo ni una palabra, eso depende del día", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}},
                {"text": "D) Ni yo mismo termino de entender qué significa ser vulnerable, así que menos aún sé cómo mostrarlo a alguien", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}}
            ]
        },
        {
            "question": "6. Si alguien me critica o me señala un error…",
            "options": [
                {"text": "A) Escucho lo que me dice, aunque me incomode, e intento ver si tiene algo de razón", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Me lo tomo muy a pecho, ya no les voy a gustar más y no me van a querer, me van a abandonar", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) De entrada lo vivo como un ataque, me pongo a la defensiva, y luego me siento mal conmigo mismo/a por haber reaccionado así", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}},
                {"text": "D) Me cierro en banda y me digo \"bah, ni caso\", pero me queda dando vueltas por que me fastidia bastante", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}}
            ]
        },
        {
            "question": "7. Cuando pienso en el futuro de mis relaciones…",
            "options": [
                {"text": "A) Pienso en el futuro lo justo y normal, confío en que si seguimos cuidándonos todo irá bien", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Le doy vueltas todo el tiempo, necesito saber si estaremos juntos o no para poder dormir bien", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) A veces me ilusiono con planes a futuro y otras me entra miedo y quiero salir corriendo", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}},
                {"text": "D) Yo no pienso en el futuro, prefiero centrarme en lo que estoy viviendo ahora", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}}
            ]
        },
        {
            "question": "8. Cuando tengo que tomar una decisión importante…",
            "options": [
                {"text": "A) Me tomo mi tiempo, pienso con calma y confío en que pase lo que pase sabré manejarlo", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Me bloqueo y necesito preguntar a otros antes de tomar la decisión para estar seguro", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) A veces decido impulsivamente y me tiro al vacio, otras veces se me pasa el tiempo y la oportunidad ya ha pasado", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}},
                {"text": "D) Decido muy rápido, casi sin pensar y sigo adelante con ello cueste lo que cueste", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}}
            ]
        },
        {
            "question": "9. Cuando estoy pasando por un momento difícil…",
            "options": [
                {"text": "A) Entiendo que la vida es así y que pasará, y si lo necesito, pido ayuda", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Pienso que nunca va a acabar, y me encierro en pensamientos negativos", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) Me entra la necesidad de buscar apoyo y las ganas de alejarme de todos", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}},
                {"text": "D) Me lo guardo, no se lo cuento a nadie y finjo que está todo perfecto", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}}
            ]
        },
        {
            "question": "10. Cuando alguien nuevo entra en mi vida (amistad, trabajo, grupo)…",
            "options": [
                {"text": "A) Me adapto fácil, hablo con la gente y me integro rápido", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Me entra vergüenza, necesito sentir que encajo primero y luego empezar a mostrarme", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) A veces me lanzo con muchas ganas, y al rato me da corte, como si no fuera yo", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}},
                {"text": "D) Puedo hablar y participar, pero que no me pregunten demasiado o me iré", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}}
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
            "secure": "Seguro: Te sientes cómodo con la intimidad y la independencia, confías en las relaciones y manejas bien los conflictos.",
            "anxious": "Ansioso: Buscas mucha cercanía y te preocupas por el rechazo, necesitas constantemente tranquilidad en las relaciones.",
            "desorganizado": "Evitativo temeroso: Tienes patrones contradictorios, a veces buscas cercanía y otras te alejas para protegerte.",
            "avoidant": "Evitativo: Prefieres mantener distancia emocional, evitas la intimidad y tiendes a ser independiente."
        }
    }
    return descriptions.get(language, descriptions["es"]).get(style, "") 
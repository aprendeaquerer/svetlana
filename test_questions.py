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

# Partner test questions
PARTNER_TEST_QUESTIONS = {
    "es": [
        {
            "question": "1. Cuando sale el tema de planes a futuro…",
            "options": [
                {"text": "A) Dice cosas como: \"¿Y si el finde que viene vamos a ver a mis padres?\" o \"En verano podríamos hacer un viaje juntos\". Habla de futuro conmigo de forma natural.", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Hace mil preguntas: \"¿Entonces, qué somos? ¿Cuándo vamos a vivir juntos?\". Y necesita respuestas rápido sino se pone nervioso.", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) Primero intenta cambiar la conversación o dice cosas como: \"Bueno… ya veremos más adelante\". Piensa que le presiono.", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}},
                {"text": "D) Le he escuchado decir \"cuando tengamos hijos\" y también \"Yo no quiero una relación a largo plazo ahora mismo\". Me confunden sus respustas.", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}}
            ]
        },
        {
            "question": "2. Respecto al tiempo juntos…",
            "options": [
                {"text": "A) Le encanta estar contigo, pero también hay momentos de: \"Hoy me apetece leer un rato solo\". Sabe equilibrar cercanía y espacio.", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Quiere estar pegado a ti todo el rato: \"Escríbeme cuando llegues… mándame foto… ¿por qué no me contestas?\". Necesita contacto constante.", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) Prefiere cierta distancia: \"Cada uno en su casa\" o \"Me voy solo de viaje, me gusta más\". Mantiene sus rutinas muy separadas de las tuyas.", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}},
                {"text": "D) Un día no se despega de ti, súper cariñoso, y al siguiente parece frío o distante sin darte una explicación clara.", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}}
            ]
        },
        {
            "question": "3. Cuando hay una discusión…",
            "options": [
                {"text": "A) Dice: \"Vale, hablemos tranquilos y vemos cómo lo arreglamos\". Busca resolver sin dramatizar.", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Se pone nervioso/a: \"No me ignores, dime que estamos bien\". Tiene miedo a que la pelea signifique ruptura.", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) Se encierra o responde con un: \"No es para tanto, lo hablamos otro día\". Evita enfrentarse al conflicto.", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}},
                {"text": "D) Puede explotar con frases fuertes y luego al rato comportarse como si no hubiera pasado nada.", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}}
            ]
        },
        {
            "question": "4. Cuando le cuentas cómo te sientes…",
            "options": [
                {"text": "A) Te escucha y responde: \"Entiendo lo que me dices\". Valida tus emociones.", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Se autoculpa: \"¿Estás enfadado conmigo? ¿Hice algo mal?\". Teme que tus emociones sean señal de rechazo.", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) Cambia de tema rápido: \"No le des tantas vueltas, vámonos a cenar\". No entra mucho en lo emocional.", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}},
                {"text": "D) A veces se abre demasiado y al día siguiente parece que no recuerda nada de lo que contó.", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}}
            ]
        },
        {
            "question": "5. Cuando no contestas rápido a sus mensajes…",
            "options": [
                {"text": "A) No se preocupa, luego te escribe un \"¿Qué tal tu día?\" como si nada.", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Se pone ansioso: \"¿Por qué no me contestas? Seguro que estás molesto conmigo\"", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) Lo interpreta como espacio: \"Genial, aprovecho y hago mis cosas\"", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}},
                {"text": "D) Puede enfriarse y devolverte el silencio como forma de castigo.", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}}
            ]
        },
        {
            "question": "6. En su vida social y amistades…",
            "options": [
                {"text": "A) Te incluye de manera natural: \"Ven, que quiero que conozcas a mis amigos\".", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Está pendiente de si gusta o no, busca aprobación: \"¿Crees que les caí bien?\"", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) Prefiere mantenerlo aparte: \"Voy solo, es mejor así\"", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}},
                {"text": "D) A veces te presenta como si fueras lo más importante y otras ni siquiera te menciona.", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}}
            ]
        },
        {
            "question": "7. En el trabajo o proyectos personales…",
            "options": [
                {"text": "A) Comparte: \"Hoy tuve un día duro en la oficina\" o \"Estoy contento, me ascendieron\". No le cuesta mostrarte su mundo.", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Siente mucha presión y miedo a fallar: \"Si no hago todo perfecto, seguro me critican o me dejan fuera\"", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) No suele contarte: \"Todo bien, nada importante\". Comparte lo justo.", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}},
                {"text": "D) Empieza proyectos con mucha ilusión y de repente, dejarlo sin ninguna explicación.", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}}
            ]
        },
        {
            "question": "8. Durante la intimidad sexual…",
            "options": [
                {"text": "A) Se nota que busca conexión: te mira, te escucha, disfruta de la cercanía.", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Lo usa para asegurarse de que lo quieres: \"Después de hacerlo me siento más tranquilo contigo\"", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) Puede tener sexo, pero como algo físico sin mucha carga emocional.", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}},
                {"text": "D) Puede estar súper cariñoso en el momento y, de golpe, apartarse con un \"mejor ya no\"", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}}
            ]
        },
        {
            "question": "9. Cuando se equivoca o mete la pata…",
            "options": [
                {"text": "A) Dice: \"Perdón, me equivoqué. ¿Cómo lo arreglo?\". Asume y repara.", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Se disculpa mil veces: \"Perdona, perdona, perdona… ¿me sigues queriendo?\"", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) Lo minimiza: \"No es tan grave, exageras\"", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}},
                {"text": "D) Puede negarlo de entrada y luego al día siguiente disculparse exageradamente.", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}}
            ]
        },
        {
            "question": "10. Cómo maneja la confianza…",
            "options": [
                {"text": "A) Confía en ti: no necesita pruebas constantes para sentirse seguro/a. Si sales con amigos te dice algo como: \"Vale, pásalo bien, luego me cuentas\".", "scores": {"secure": 1, "anxious": 0, "desorganizado": 0, "avoidant": 0}},
                {"text": "B) Se pone celoso fácilmente: \"¿Quién te escribió? Seguro que era alguien más\"", "scores": {"secure": 0, "anxious": 1, "desorganizado": 0, "avoidant": 0}},
                {"text": "C) Desconfía pero en otro sentido: \"Si me meto demasiado, pierdo mi libertad\". Piensa que una relación seria le quitará su libertad, o identidad, o independencia.", "scores": {"secure": 0, "anxious": 0, "desorganizado": 0, "avoidant": 1}},
                {"text": "D) Puede llegar a revisarte el móvil o sospechar de infidelidades sin razón clara.", "scores": {"secure": 0, "anxious": 0, "desorganizado": 1, "avoidant": 0}}
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

def calculate_relationship_status(user_style, partner_style):
    """
    Calculate relationship status based on both attachment styles
    Returns a descriptive string of the relationship dynamic
    """
    if not user_style or not partner_style:
        return "unknown"
    
    # Create a consistent ordering for the combination
    styles = sorted([user_style, partner_style])
    combination = f"{styles[0]}_and_{styles[1]}"
    
    relationship_dynamics = {
        "secure_and_secure": "secure_secure",
        "secure_and_anxious": "secure_anxious", 
        "secure_and_avoidant": "secure_avoidant",
        "secure_and_desorganizado": "secure_disorganized",
        "anxious_and_anxious": "anxious_anxious",
        "anxious_and_avoidant": "anxious_avoidant",
        "anxious_and_desorganizado": "anxious_disorganized", 
        "avoidant_and_avoidant": "avoidant_avoidant",
        "avoidant_and_desorganizado": "avoidant_disorganized",
        "desorganizado_and_desorganizado": "disorganized_disorganized"
    }
    
    return relationship_dynamics.get(combination, "unknown")

def get_relationship_description(relationship_status, language="es"):
    """
    Get description of relationship dynamic based on attachment style combination
    """
    descriptions = {
        "es": {
            "secure_secure": "Relación segura-segura: Ambos manejan bien la intimidad y la independencia, con comunicación abierta y resolución sana de conflictos.",
            "secure_anxious": "Relación segura-ansiosa: El estilo seguro puede proporcionar estabilidad y tranquilidad al estilo ansioso, mientras que el ansioso aporta intensidad emocional.",
            "secure_avoidant": "Relación segura-evitativa: El estilo seguro respeta la necesidad de espacio del evitativo, mientras que el evitativo puede aprender a abrirse gradualmente.",
            "secure_disorganized": "Relación segura-desorganizada: El estilo seguro puede proporcionar consistencia y estabilidad al estilo desorganizado, ayudando a regular las emociones.",
            "anxious_anxious": "Relación ansiosa-ansiosa: Alta intensidad emocional, pero pueden reforzarse mutuamente las inseguridades. Necesitan trabajar en la confianza mutua.",
            "anxious_avoidant": "Relación ansiosa-evitativa: Dinámica clásica de persecución-evitación. El ansioso busca cercanía mientras el evitativo se aleja, creando ciclos de tensión.",
            "anxious_disorganized": "Relación ansiosa-desorganizada: Patrones impredecibles y alta intensidad emocional. Pueden experimentar montañas rusas emocionales.",
            "avoidant_avoidant": "Relación evitativa-evitativa: Ambos mantienen distancia emocional. Puede funcionar si ambos valoran la independencia, pero puede carecer de intimidad profunda.",
            "avoidant_disorganized": "Relación evitativa-desorganizada: Patrones contradictorios donde uno evita y el otro alterna entre acercarse y alejarse.",
            "disorganized_disorganized": "Relación desorganizada-desorganizada: Patrones muy impredecibles y caóticos. Puede ser muy intensa pero también muy inestable.",
            "unknown": "Estado de relación no determinado"
        }
    }
    return descriptions.get(language, descriptions["es"]).get(relationship_status, "Estado de relación no determinado") 
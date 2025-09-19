#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration script to add missing columns to test_state table
This script adds q3, q4, q5 columns if they don't exist
"""
import os
from databases import Database
import asyncio

DATABASE_URL = os.getenv("DATABASE_URL")

drop_sql = "DROP TABLE IF EXISTS test_state;"
create_sql = """
CREATE TABLE test_state (
    user_id TEXT PRIMARY KEY,
    state TEXT,
    last_choice TEXT,
    q1 TEXT,
    q2 TEXT,
    q3 TEXT,
    q4 TEXT,
    q5 TEXT,
    q6 TEXT,
    q7 TEXT,
    q8 TEXT,
    q9 TEXT,
    q10 TEXT,
    language TEXT DEFAULT 'es'
);
"""

async def main():
    if not DATABASE_URL:
        print("DATABASE_URL not set")
        return
    db = Database(DATABASE_URL)
    await db.connect()
    print("Dropping test_state table if exists...")
    await db.execute(drop_sql)
    print("Creating test_state table...")
    await db.execute(create_sql)
    print("Done.")
    await db.disconnect()

async def migrate_database():
    from main import database
    # Agrega el campo email si no existe, permite nulos y lo hace único
    await database.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            hashed_password TEXT,
            email TEXT UNIQUE
        )
    ''')
    # Si la tabla ya existe, intenta agregar la columna email si falta
    try:
        await database.execute('ALTER TABLE users ADD COLUMN email TEXT UNIQUE')
    except Exception as e:
        # Puede fallar si la columna ya existe, lo ignoramos
        print(f"[DEBUG] (migración) email ya existe o error benigno: {e}")
    
    # Add email verification columns
    try:
        await database.execute('ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE')
    except Exception as e:
        print(f"[DEBUG] (migración) email_verified ya existe o error benigno: {e}")
    
    try:
        await database.execute('ALTER TABLE users ADD COLUMN verification_code TEXT')
    except Exception as e:
        print(f"[DEBUG] (migración) verification_code ya existe o error benigno: {e}")
    
    try:
        await database.execute('ALTER TABLE users ADD COLUMN verification_code_expires TIMESTAMP')
    except Exception as e:
        print(f"[DEBUG] (migración) verification_code_expires ya existe o error benigno: {e}")
    
    return True

async def migrate_user_profile(database):
    await database.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            user_id TEXT PRIMARY KEY,
            nombre TEXT,
            edad INTEGER,
            tiene_pareja BOOLEAN,
            nombre_pareja TEXT,
            tiempo_pareja TEXT,
            estado_emocional TEXT,
            estado_relacion TEXT,
            opinion_apego TEXT,
            fecha_ultima_conversacion TIMESTAMP,
            fecha_ultima_mencion_pareja TIMESTAMP,
            attachment_style TEXT,
            partner_attachment_style TEXT,
            relationship_status TEXT,
            fecha_ultima_afirmacion TIMESTAMP,
            afirmacion_anxious TEXT,
            afirmacion_avoidant TEXT,
            afirmacion_secure TEXT,
            afirmacion_disorganized TEXT
        )
    ''')
    # Intentar agregar las columnas si la tabla ya existe
    try:
        await database.execute('ALTER TABLE user_profile ADD COLUMN attachment_style TEXT')
    except Exception:
        pass  # Ya existe
    try:
        await database.execute('ALTER TABLE user_profile ADD COLUMN tiempo_pareja TEXT')
    except Exception:
        pass  # Ya existe
    try:
        await database.execute('ALTER TABLE user_profile ADD COLUMN fecha_ultima_afirmacion TIMESTAMP')
    except Exception:
        pass  # Ya existe
    try:
        await database.execute('ALTER TABLE user_profile ADD COLUMN afirmacion_anxious TEXT')
    except Exception:
        pass  # Ya existe
    try:
        await database.execute('ALTER TABLE user_profile ADD COLUMN afirmacion_avoidant TEXT')
    except Exception:
        pass  # Ya existe
    try:
        await database.execute('ALTER TABLE user_profile ADD COLUMN afirmacion_secure TEXT')
    except Exception:
        pass  # Ya existe
    try:
        await database.execute('ALTER TABLE user_profile ADD COLUMN afirmacion_disorganized TEXT')
    except Exception:
        pass  # Ya existe
    try:
        await database.execute('ALTER TABLE user_profile ADD COLUMN partner_attachment_style TEXT')
    except Exception:
        pass  # Ya existe
    try:
        await database.execute('ALTER TABLE user_profile ADD COLUMN relationship_status TEXT')
    except Exception:
        pass  # Ya existe
    
    # Create affirmations table
    await database.execute('''
        CREATE TABLE IF NOT EXISTS affirmations (
            id SERIAL PRIMARY KEY,
            attachment_style TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'es',
            text TEXT NOT NULL,
            order_index INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Populate affirmations table if empty
    await populate_affirmations(database)
    
    return True

async def populate_affirmations(database):
    """Populate the affirmations table with existing data"""
    # Check if affirmations already exist
    count = await database.fetch_val("SELECT COUNT(*) FROM affirmations")
    if count > 0:
        print("[DEBUG] Affirmations already exist in database, skipping population")
        return
    
    # Daily affirmations data - Updated versions
    affirmations_data = {
        "avoidant": [
            "Soy suficiente y no necesito demostrar nada para que me quieran",
            "Si, soy suficiente tal y como soy",
            "Me van a aceptar con lo bueno y lo malo, y pensarán que soy increíble, igual que yo hago con los demás",
            "No necesito ser perfecto/a",
            "Merezco amor",
            "Merezco tener una pareja que me valore de verdad",
            "Me siento bien en mi propio cuerpo",
            "Puedo confiar en esta relación",
            "Estoy a salvo para poner límites cuando los necesito",
            "Tengo mucho que aportar a una pareja",
            "Hay alguien ahí fuera que piensa que soy justo lo que está buscando",
            "Estoy seguro/a en este momento",
            "Estoy seguro/a con ellos",
            "Se preocupan por mí y por lo que siento",
            "Puedo confiar en que los demás quieren cosas buenas para mi",
            "Abrirme a los demás no significa perderme a mi mismo ni mi libertad",
            "Que alguien me haya fallado antes no significa que vaya a pasar ahora",
            "Puedo abrirme y hablar de lo que siento y necesito",
            "No necesito esconder mis necesidades, todos las tenemos",
            "Puedo expresar lo que siento y afrontarlo por mí mismo/a.",
            "Puedo querer y dejarme querer al mismo tiempo",
            "El amor no tiene por qué ser siempre difícil para mí",
            "Hablar de mis limites es una forma sana de cuidarme, no de alejarme",
            "Mi independencia no desaparece por compartir lo que siento"
        ],
        "anxious": [
            "No necesito estar pendiente de todo para que. me quieran",
            "No necesito ser perfecto para que me quieran",
            "La incertidumbre no es el fin del mundo, todo ira bien y yo estaré bien pase lo que pase",
            "Puedo equivocarme y que me sigan queriendo",
            "Puedo estar tranquilo aunque no me contesten enseguida, yo tengo mi propia vida",
            "Podemos tener diferencias y discutirlas y aun así seguir queriendonos",
            "El silencio no significa rechazo",
            "Puedo cuidar de mi sin esperar que el otro lo haga siempre",
            "Está bien pedir cariño, pero tambien está bien darmelo yo mismo",
            "No todo lo que pienso es lo que esta pasando",
            "No tengo que estar vigilando, comprobando y observando todo el tiempo",
            "El amor puede sentirse en paz y sin dramas",
            "Mi cerebro puede decirme mil cosas negativas pero eso no significa que sean verdad y no me lo tengo que creer",
            "Si algo no funciona, no tiene porque ser mi culpa. Simplemente no era adecuado a mi.",
            "Alguien va a ser muy afortunado de tenerme como pareja y darle mi amor",
            "No necesito aprobación constante del exterior para estar en paz, lo hago desde mi interior"
        ],
        "disorganized": [
            "Si alguien tarda en contestar, no significa que te estén dejando de lado. A veces la gente simplemente tiene su vida, y eso no borra lo que sienten por ti.",
            "No tienes que estar siempre \"bien\" para que te quieran. Incluso en tus días grises, sigues siendo digno/a de cariño.",
            "Pedir espacio no rompe el vínculo. Puedes necesitar tiempo para ti y seguir estando conectado/a con los demás.",
            "Ese miedo que aparece cuando alguien se acerca demasiado es antiguo. Hoy ya puedes poner límites sanos sin perder a la otra persona.",
            "Decir \"te echo de menos\" no te hace débil. Te hace humano/a y abierto/a a la conexión.",
            "Que alguien te haya fallado antes no significa que todos lo harán. Cada persona es una historia nueva.",
            "Puedes querer mucho y también necesitar tu espacio. Ambas cosas son parte de un amor sano.",
            "Cuando aparece la voz de \"¿y si me hace daño?\", recuerda: hoy tienes más recursos para cuidarte que en el pasado.",
            "El amor no tiene por qué sentirse como una montaña rusa. También puede ser estable, tranquilo, y seguir siendo profundo.",
            "Un error en una conversación no destruye una relación. Los vínculos sanos se reparan, no se rompen a la primera.",
            "Tu valor no depende de lo intenso que sea el vínculo. Eres suficiente por quién eres, no por cuánto das o cuánto recibes.",
            "Que antes te doliera la cercanía no significa que siempre vaya a ser así. Ahora tienes la opción de vivirla distinto.",
            "Puedes aprender a vivir el amor desde la calma, no desde la alarma. Y eso empieza por escucharte sin miedo.",
            "Eres digno/a de una conexión clara, constante y amorosa. No tienes que ganártela con esfuerzo extra.",
            "Puedes construir vínculos que te hagan crecer y darte paz, no dudas. Esa elección está en ti, y la puedes practicar cada día."
        ],
        "secure": [
            "Puedo decir lo que siento sin miedo a que me dejen. Hablar claro no rompe los vínculos, los fortalece.",
            "Si algo me incomoda, puedo expresarlo con calma y la otra persona tiene derecho a escucharlo sin que eso signifique pelea.",
            "Tener un mal día no hace que me dejen de querer. Todos tenemos altibajos y la relación puede sostenerlos.",
            "Puedo pedir lo que necesito sin sentirme débil ni exigente. Mis necesidades importan.",
            "No tengo que estar siempre de acuerdo para estar bien con alguien. Se puede querer y pensar distinto a la vez.",
            "Puedo poner límites sin miedo al rechazo. El que me quiere de verdad también respeta mis espacios.",
            "Si hay un conflicto, no significa que todo se rompa. Las relaciones sanas se pueden reparar.",
            "El afecto se recibe sin sospecha. No tengo que buscarle un \"pero\" al cariño que me dan.",
            "Puedo estar solo/a sin sentirme abandonado/a, y acompañado/a sin sentirme invadido/a.",
            "El amor seguro no es perfecto, es real: incluye hablar, escuchar, equivocarse y volver a acercarse.",
            "Mostrar vulnerabilidad no me hace débil. Me hace auténtico/a y cercano/a.",
            "La distancia no significa rechazo, a veces es solo espacio necesario.",
            "Soy capaz de escuchar al otro sin cargar con todo lo que siente. Empatizo sin perderme.",
            "No necesito pruebas constantes de amor. Sé que el vínculo no depende de un mensaje o un gesto inmediato.",
            "El apego seguro se elige cada día: con las palabras que digo, con los límites que pongo y con el cuidado que doy y recibo"
        ]
    }
    
    # Insert affirmations into database
    for style, affirmations in affirmations_data.items():
        for index, text in enumerate(affirmations):
            await database.execute("""
                INSERT INTO affirmations (attachment_style, language, text, order_index)
                VALUES (:style, 'es', :text, :index)
            """, {"style": style, "text": text, "index": index})
    
    print(f"[DEBUG] Populated affirmations table with {sum(len(affs) for affs in affirmations_data.values())} affirmations")

if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(migrate_database()) 
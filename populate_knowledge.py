#!/usr/bin/env python3
"""
Script to populate the eldric_knowledge table with attachment theory content from "Attached" book.
Run this script to add knowledge chunks that Eldric can use to provide more informed responses.
"""

import asyncio
import os
from databases import Database

# Sample knowledge chunks from "Attached" book
KNOWLEDGE_CHUNKS = [
    {
        "content": "Las personas con apego ansioso tienden a buscar mucha cercanía y confirmación en sus relaciones. Se preocupan por el rechazo y pueden interpretar pequeñas señales como indicadores de que su pareja los está abandonando.",
        "tags": "anxious,apego ansioso,cercanía,confirmación,rechazo,abandono"
    },
    {
        "content": "El apego evitativo se caracteriza por mantener distancia emocional. Estas personas valoran su independencia y pueden sentirse sofocadas por demasiada intimidad o dependencia emocional.",
        "tags": "avoidant,evitativo,distancia,independencia,sofocado,intimidad"
    },
    {
        "content": "El apego seguro permite a las personas sentirse cómodas tanto con la intimidad como con la independencia. Manejan los conflictos de manera equilibrada y confían en que sus necesidades serán atendidas.",
        "tags": "secure,seguro,intimidad,independencia,confianza,equilibrio"
    },
    {
        "content": "La comunicación efectiva es fundamental en las relaciones. Las personas con apego seguro tienden a expresar sus necesidades de manera clara y directa, sin temor al rechazo.",
        "tags": "communication,comunicación,necesidades,expresar,seguro"
    },
    {
        "content": "Los conflictos en las relaciones son normales, pero cómo los manejamos depende de nuestro estilo de apego. Las personas ansiosas pueden buscar resolverlos inmediatamente, mientras que las evitativas pueden necesitar tiempo para procesar.",
        "tags": "conflict,conflicto,ansioso,evitativo,resolver,procesar"
    },
    {
        "content": "La confianza se construye gradualmente en las relaciones. Las personas con apego seguro desarrollan confianza más fácilmente, mientras que las ansiosas pueden necesitar más confirmación y las evitativas pueden tener dificultades para confiar.",
        "tags": "trust,confianza,seguro,ansioso,evitativo,confirmación"
    },
    {
        "content": "Las emociones en las relaciones pueden ser intensas. Es importante reconocer que todos tenemos necesidades emocionales válidas, independientemente de nuestro estilo de apego.",
        "tags": "emotions,emociones,necesidades,válidas,apego"
    },
    {
        "content": "El apego desorganizado se caracteriza por patrones contradictorios. Estas personas pueden alternar entre buscar cercanía y alejarse, creando confusión tanto en sí mismas como en sus parejas.",
        "tags": "disorganized,desorganizado,contradictorio,cercanía,alejarse,confusión"
    },
    {
        "content": "La intimidad emocional requiere vulnerabilidad. Las personas con apego seguro pueden ser vulnerables sin temor, mientras que las evitativas pueden protegerse manteniendo distancia emocional.",
        "tags": "intimidad,vulnerabilidad,seguro,evitativo,distancia,protección"
    },
    {
        "content": "Los estilos de apego no son fijos. Con conciencia y trabajo, es posible desarrollar un apego más seguro y cambiar patrones que no nos sirven en las relaciones.",
        "tags": "cambio,desarrollo,conciencia,trabajo,patrones,relaciones"
    },
    {
        "content": "Las necesidades emocionales son universales. Todos necesitamos sentirnos amados, seguros y valorados en nuestras relaciones. La diferencia está en cómo expresamos y buscamos satisfacer estas necesidades.",
        "tags": "necesidades,universales,amados,seguros,valorados,expresar"
    },
    {
        "content": "La ansiedad en las relaciones puede manifestarse como preocupación constante, necesidad de confirmación o miedo al abandono. Es importante reconocer estos patrones para poder trabajarlos.",
        "tags": "anxious,ansiedad,preocupación,confirmación,miedo,abandono,patrones"
    },
    {
        "content": "La evitación emocional puede manifestarse como distanciamiento, dificultad para expresar emociones o preferencia por mantener relaciones superficiales. Reconocer estos patrones es el primer paso para el cambio.",
        "tags": "avoidant,evitación,distancia,emociones,superficial,patrones,cambio"
    },
    {
        "content": "La seguridad emocional se construye a través de la consistencia, la disponibilidad emocional y la respuesta a las necesidades del otro. Las personas con apego seguro han experimentado estas cualidades en sus relaciones tempranas.",
        "tags": "secure,seguridad,consistencia,disponibilidad,respuesta,necesidades"
    },
    {
        "content": "Los conflictos en las relaciones pueden ser oportunidades de crecimiento. La clave está en abordarlos con respeto, escucha activa y disposición para encontrar soluciones que funcionen para ambos.",
        "tags": "conflict,conflicto,crecimiento,respeto,escucha,soluciones"
    }
]

async def populate_knowledge():
    """Populate the eldric_knowledge table with sample data."""
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable not set")
        return
    
    database = Database(DATABASE_URL)
    
    try:
        await database.connect()
        print("Connected to database successfully")
        
        # Check if table exists and has data
        existing_count = await database.fetch_val("SELECT COUNT(*) FROM eldric_knowledge")
        print(f"Existing knowledge chunks: {existing_count}")
        
        if existing_count > 0:
            print("Knowledge table already has data. Skipping population.")
            return
        
        # Insert knowledge chunks
        for chunk in KNOWLEDGE_CHUNKS:
            await database.execute(
                "INSERT INTO eldric_knowledge (content, tags) VALUES (:content, :tags)",
                {"content": chunk["content"], "tags": chunk["tags"]}
            )
        
        print(f"Successfully inserted {len(KNOWLEDGE_CHUNKS)} knowledge chunks")
        
        # Verify insertion
        final_count = await database.fetch_val("SELECT COUNT(*) FROM eldric_knowledge")
        print(f"Total knowledge chunks in database: {final_count}")
        
    except Exception as e:
        print(f"Error populating knowledge: {e}")
    finally:
        await database.disconnect()

if __name__ == "__main__":
    asyncio.run(populate_knowledge()) 
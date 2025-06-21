#!/usr/bin/env python3
"""
Test script to verify keyword extraction and knowledge injection functionality.
"""

import asyncio
import os
from databases import Database

# Import the functions from main.py
import sys
sys.path.append('.')
from main import extract_keywords, get_relevant_knowledge, inject_knowledge_into_prompt

# Sample Eldric prompt for testing
SAMPLE_PROMPT = """Eres Eldric, un coach emocional cálido, empático, sabio y cercano. 
Eres experto en teoría del apego, psicología de las relaciones y acompañamiento emocional. 
Intenta mantener las respuestas un poco mas cortas, mas simples
Hablas en español neutro, sin tecnicismos innecesarios, usando un tono accesible pero profundo. 
Escuchas activamente, haces preguntas reflexivas y das orientación emocional basada en el estilo de apego de cada persona. 
Cuando el usuario dice 'saludo inicial', responde con una bienvenida estructurada: 
una breve presentación tuya, una explicación sencilla de los estilos de apego y una invitación clara a realizar un test."""

async def test_knowledge_system():
    """Test the knowledge extraction and injection system."""
    
    # Test messages
    test_messages = [
        "Me siento muy ansioso en mi relación, siempre me preocupa que mi pareja me abandone",
        "Prefiero mantener distancia emocional, me siento sofocado cuando hay mucha intimidad",
        "Tengo confianza en mi relación y me siento seguro con mi pareja",
        "Me siento confundido sobre cómo manejar los conflictos en mi relación",
        "Necesito ayuda para comunicarme mejor con mi pareja"
    ]
    
    print("🧪 Testing Knowledge Extraction and Injection System\n")
    
    for i, message in enumerate(test_messages, 1):
        print(f"Test {i}: '{message}'")
        
        # Extract keywords
        keywords = extract_keywords(message)
        print(f"   Keywords extracted: {keywords}")
        
        # Get relevant knowledge
        knowledge = await get_relevant_knowledge(keywords)
        print(f"   Knowledge found: {len(knowledge)} characters")
        
        if knowledge:
            print(f"   Knowledge preview: {knowledge[:100]}...")
        
        # Test prompt injection
        enhanced_prompt = inject_knowledge_into_prompt(SAMPLE_PROMPT, knowledge)
        print(f"   Enhanced prompt length: {len(enhanced_prompt)} characters")
        
        print()

async def test_database_connection():
    """Test database connection and knowledge table."""
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL environment variable not set")
        return False
    
    database = Database(DATABASE_URL)
    
    try:
        await database.connect()
        print("✅ Database connection successful")
        
        # Check if eldric_knowledge table exists
        try:
            count = await database.fetch_val("SELECT COUNT(*) FROM eldric_knowledge")
            print(f"✅ eldric_knowledge table exists with {count} records")
            
            if count > 0:
                # Show a sample record
                sample = await database.fetch_one("SELECT content, tags FROM eldric_knowledge LIMIT 1")
                print(f"   Sample record: {sample['content'][:50]}...")
                print(f"   Tags: {sample['tags']}")
            
            return True
            
        except Exception as e:
            print(f"❌ eldric_knowledge table not found: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    finally:
        await database.disconnect()

async def main():
    """Main test function."""
    print("🚀 Starting Knowledge System Tests\n")
    
    # Test database connection first
    db_ok = await test_database_connection()
    print()
    
    if db_ok:
        # Test knowledge extraction and injection
        await test_knowledge_system()
        print("✅ All tests completed!")
    else:
        print("❌ Database tests failed. Please check your DATABASE_URL and run populate_knowledge.py first.")

if __name__ == "__main__":
    asyncio.run(main()) 
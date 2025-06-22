#!/usr/bin/env python3
"""
Script to populate language-specific knowledge tables for Eldric chatbot.
This script helps you import translated knowledge chunks into separate language tables.
"""

import asyncio
import json
import os
from databases import Database
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/eldric_db')
database = Database(DATABASE_URL)

async def populate_language_knowledge(language: str, json_file_path: str):
    """
    Populate knowledge table for a specific language from a JSON file.
    
    Args:
        language: Language code ('en', 'es', 'ru')
        json_file_path: Path to JSON file with knowledge chunks
    """
    try:
        # Read JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            knowledge_chunks = json.load(f)
        
        # Connect to database
        await database.connect()
        
        # Clear existing data for this language
        table_name = f"eldric_knowledge_{language}"
        await database.execute(f"DELETE FROM {table_name}")
        print(f"Cleared existing data from {table_name}")
        
        # Insert new knowledge chunks
        for chunk in knowledge_chunks:
            await database.execute(
                f"INSERT INTO {table_name} (content, tags) VALUES (:content, :tags)",
                {
                    "content": chunk["content"],
                    "tags": chunk["tags"]
                }
            )
        
        print(f"Successfully imported {len(knowledge_chunks)} knowledge chunks for {language}")
        
    except FileNotFoundError:
        print(f"Error: File {json_file_path} not found")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_file_path}")
    except Exception as e:
        print(f"Error importing knowledge for {language}: {e}")
    finally:
        await database.disconnect()

async def main():
    """Main function to populate all language knowledge tables."""
    print("Eldric Multilingual Knowledge Base Populator")
    print("=" * 50)
    
    # Define language files (you'll need to create these)
    language_files = {
        "en": "attached_knowledge_en.json",
        "es": "attached_knowledge_es.json", 
        "ru": "attached_knowledge_ru.json"
    }
    
    for language, filename in language_files.items():
        if os.path.exists(filename):
            print(f"\nImporting {language} knowledge from {filename}...")
            await populate_language_knowledge(language, filename)
        else:
            print(f"\nSkipping {language}: {filename} not found")
            print(f"Create {filename} with format:")
            print("""
[
    {
        "content": "Knowledge chunk content in the target language",
        "tags": "anxious,relationship,trust"
    },
    ...
]
            """)

if __name__ == "__main__":
    asyncio.run(main()) 
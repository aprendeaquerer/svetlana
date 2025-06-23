#!/usr/bin/env python3
"""
Script to populate the eldric_knowledge table with English content from multiple JSON files.
This script imports knowledge chunks from 4 different books into the main eldric_knowledge table.
"""

import asyncio
import json
import os
from databases import Database
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/eldric_db")
database = Database(DATABASE_URL)

# List of JSON files to import
JSON_FILES = [
    "C:/scripts/attached_medium_chunks_100_final.json",
    "C:/scripts/polyvagal_theory_medium_chunks_100_final.json", 
    "C:/scripts/the_power_of_attachment_medium_chunks_100_final.json"
]

async def populate_english_knowledge():
    """
    Populate the eldric_knowledge table with English content from JSON files.
    """
    try:
        # Connect to database
        await database.connect()
        
        # Clear existing data from eldric_knowledge table
        await database.execute("DELETE FROM eldric_knowledge")
        print("Cleared existing data from eldric_knowledge table")
        
        total_chunks = 0
        
        # Process each JSON file
        for json_file in JSON_FILES:
            if not os.path.exists(json_file):
                print(f"Warning: File {json_file} not found, skipping...")
                continue
                
            print(f"\nProcessing {json_file}...")
            
            # Read JSON file
            with open(json_file, "r", encoding="utf-8") as f:
                knowledge_chunks = json.load(f)
            
            # Insert knowledge chunks
            for chunk in knowledge_chunks:
                # Extract content and tags
                content = chunk.get("content", "")
                tags = chunk.get("tags", [])
                
                # Convert tags list to comma-separated string
                if isinstance(tags, list):
                    tags_str = ",".join(tags)
                else:
                    tags_str = str(tags)
                
                # Insert into database
                await database.execute(
                    "INSERT INTO eldric_knowledge (content, tags) VALUES (:content, :tags)",
                    {
                        "content": content,
                        "tags": tags_str
                    }
                )
            
            file_chunks = len(knowledge_chunks)
            total_chunks += file_chunks
            print(f"Imported {file_chunks} chunks from {os.path.basename(json_file)}")
        
        # Verify final count
        final_count = await database.fetch_val("SELECT COUNT(*) FROM eldric_knowledge")
        print(f"\n Successfully imported {total_chunks} total knowledge chunks")
        print(f" Total chunks in eldric_knowledge table: {final_count}")
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
    except Exception as e:
        print(f"Error importing knowledge: {e}")
    finally:
        await database.disconnect()

async def main():
    """Main function to populate English knowledge."""
    print("Eldric English Knowledge Base Populator")
    print("=" * 50)
    print("This will populate the eldric_knowledge table with English content")
    print("from the following files:")
    for file in JSON_FILES:
        print(f"  - {os.path.basename(file)}")
    print()
    
    await populate_english_knowledge()

if __name__ == "__main__":
    asyncio.run(main())

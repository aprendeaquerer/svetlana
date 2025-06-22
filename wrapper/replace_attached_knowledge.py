#!/usr/bin/env python3
"""
Script to replace the existing Attached book knowledge in the database with new content from attached_medium_chunks.json.
This will remove all existing knowledge chunks and replace them with the new ones.
"""

import asyncio
import json
import os
from databases import Database

# Use the same database URL as seed_from_json.py
DATABASE_URL = "postgresql://aprendeavivir_7ktf_user:y3M05HsW5AlRVcZ5luDsHvSh7pykgPvd@dpg-d11jgo8dl3ps73cs1s"

async def replace_attached_knowledge():
    """Replace all existing knowledge with new content from attached_medium_chunks.json."""
    database = Database(DATABASE_URL)
    
    try:
        await database.connect()
        print("✅ Connected to database successfully")
        
        # Check if the new file exists in the scripts directory
        filename = "../scripts/attached_medium_chunks.json"
        if not os.path.exists(filename):
            print(f"❌ File {filename} not found")
            return
        
        # Get current count
        current_count = await database.fetch_val("SELECT COUNT(*) FROM eldric_knowledge")
        print(f"📊 Current knowledge chunks in database: {current_count}")
        
        # Load new data
        print(f"📖 Loading new knowledge from {filename}...")
        with open(filename, 'r', encoding='utf-8') as f:
            new_data = json.load(f)
        
        print(f"📖 Found {len(new_data)} new knowledge chunks")
        
        # Confirm replacement
        print("\n⚠️  WARNING: This will DELETE ALL existing knowledge chunks and replace them with new ones.")
        confirm = input("Are you sure you want to continue? (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("❌ Operation cancelled")
            return
        
        # Clear existing data
        print("🗑️  Clearing existing knowledge chunks...")
        await database.execute("DELETE FROM eldric_knowledge")
        
        # Insert new data
        print("📝 Inserting new knowledge chunks...")
        imported_count = 0
        for item in new_data:
            await database.execute(
                "INSERT INTO eldric_knowledge (content, tags) VALUES (:content, :tags)",
                {"content": item["content"], "tags": item["tags"]}
            )
            imported_count += 1
        
        # Verify the replacement
        final_count = await database.fetch_val("SELECT COUNT(*) FROM eldric_knowledge")
        
        print(f"\n✅ Replacement completed successfully!")
        print(f"📊 Final statistics:")
        print(f"   Previous chunks: {current_count}")
        print(f"   New chunks imported: {imported_count}")
        print(f"   Total chunks in database: {final_count}")
        
        # Show a sample of the new content
        sample = await database.fetch_one("SELECT content, tags FROM eldric_knowledge LIMIT 1")
        if sample:
            print(f"\n📖 Sample of new content:")
            print(f"   Content: {sample['content'][:100]}...")
            print(f"   Tags: {sample['tags']}")
        
    except Exception as e:
        print(f"❌ Error during replacement: {e}")
    finally:
        await database.disconnect()

if __name__ == "__main__":
    asyncio.run(replace_attached_knowledge()) 
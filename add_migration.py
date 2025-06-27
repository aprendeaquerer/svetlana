#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration script to add missing columns to test_state table
This script adds q3, q4, q5 columns if they don't exist
"""
import asyncio
import os
from databases import Database

async def migrate_database():
    """Add missing columns to test_state table"""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False
    
    # Connect to database
    database = Database(database_url)
    try:
        await database.connect()
        print("✅ Connected to database successfully")
        
        # Check if table exists
        table_exists = await database.fetch_one("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'test_state'
            )
        """)
        
        if not table_exists[0]:
            print("❌ Table 'test_state' does not exist. Creating it...")
            await database.execute("""
                CREATE TABLE test_state (
                    user_id TEXT PRIMARY KEY,
                    state TEXT,
                    last_choice TEXT,
                    q1 TEXT,
                    q2 TEXT,
                    q3 TEXT,
                    q4 TEXT,
                    q5 TEXT,
                    language TEXT DEFAULT 'es'
                )
            """)
            print("✅ Table 'test_state' created with all columns")
            return True
        
        # Check which columns exist
        columns = await database.fetch_all("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'test_state'
        """)
        
        existing_columns = [col[0] for col in columns]
        print(f"📋 Existing columns: {existing_columns}")
        
        # Add missing columns
        missing_columns = []
        for col in ['q3', 'q4', 'q5']:
            if col not in existing_columns:
                missing_columns.append(col)
        
        if missing_columns:
            print(f"🔧 Adding missing columns: {missing_columns}")
            for col in missing_columns:
                try:
                    await database.execute(f"ALTER TABLE test_state ADD COLUMN {col} TEXT")
                    print(f"✅ Added column: {col}")
                except Exception as e:
                    print(f"⚠️  Warning adding column {col}: {e}")
        else:
            print("✅ All required columns already exist")
        
        # Verify final structure
        final_columns = await database.fetch_all("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'test_state'
            ORDER BY ordinal_position
        """)
        
        print(f"📋 Final table structure:")
        for col in final_columns:
            print(f"   - {col[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False
    finally:
        await database.disconnect()
        print("🔌 Disconnected from database")

if __name__ == "__main__":
    print("🚀 Starting database migration...")
    success = asyncio.run(migrate_database())
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        exit(1) 
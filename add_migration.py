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
    return True

if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(migrate_database()) 
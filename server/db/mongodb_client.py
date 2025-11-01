"""
MongoDB Client
==============
Async MongoDB connection and management for LearnPro platform
"""

import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from config.settings import settings


class MongoDBClient:
    """
    MongoDB client with async support using Motor
    """
    
    def __init__(self, connection_string: str = None, database_name: str = None):
        """
        Initialize MongoDB client
        
        Args:
            connection_string: MongoDB connection string
            database_name: Database name to use
        """
        self.connection_string = connection_string or settings.MONGODB_URL
        self.database_name = database_name or settings.MONGODB_DB_NAME
        
        # Async client (for FastAPI)
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        
        # Sync client (for scripts)
        self.sync_client: Optional[MongoClient] = None
        self.sync_db = None
        
        self._connected = False
    
    async def connect(self):
        """Establish async connection to MongoDB"""
        if self._connected:
            return
        
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            self.db = self.client[self.database_name]
            
            # Verify connection
            await self.client.admin.command('ping')
            
            self._connected = True
            print(f"✅ Connected to MongoDB: {self.database_name}")
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close async connection"""
        if self.client:
            self.client.close()
            self._connected = False
            print("🔌 Disconnected from MongoDB")
    
    def connect_sync(self):
        """Establish sync connection (for scripts)"""
        try:
            self.sync_client = MongoClient(self.connection_string)
            self.sync_db = self.sync_client[self.database_name]
            
            # Verify connection
            self.sync_client.admin.command('ping')
            
            print(f"✅ Connected to MongoDB (sync): {self.database_name}")
            
        except Exception as e:
            print(f"❌ MongoDB sync connection failed: {e}")
            raise
    
    def disconnect_sync(self):
        """Close sync connection"""
        if self.sync_client:
            self.sync_client.close()
            print("🔌 Disconnected from MongoDB (sync)")
    
    async def get_collection(self, collection_name: str):
        """Get async collection"""
        if not self._connected:
            await self.connect()
        return self.db[collection_name]
    
    def get_collection_sync(self, collection_name: str):
        """Get sync collection"""
        if not self.sync_db:
            self.connect_sync()
        return self.sync_db[collection_name]
    
    async def health_check(self) -> bool:
        """Check if MongoDB is accessible"""
        try:
            if not self._connected:
                await self.connect()
            await self.client.admin.command('ping')
            return True
        except:
            return False
    
    async def create_indexes(self):
        """Create necessary indexes for collections"""
        if not self._connected:
            await self.connect()
        
        # Student profiles indexes
        students = await self.get_collection('students')
        await students.create_index('student_id', unique=True)
        await students.create_index('email', unique=True, sparse=True)
        
        # Quiz attempts indexes
        attempts = await self.get_collection('quiz_attempts')
        await attempts.create_index([('student_id', 1), ('completed_at', -1)])
        await attempts.create_index('quiz_id')
        
        # Progress tracking indexes
        progress = await self.get_collection('student_progress')
        await progress.create_index([('student_id', 1), ('module_name', 1)])
        await progress.create_index('updated_at')
        
        print("✅ MongoDB indexes created")


# Global client instance
_mongodb_client: Optional[MongoDBClient] = None


async def get_mongodb() -> MongoDBClient:
    """Get or create global MongoDB client instance"""
    global _mongodb_client
    if _mongodb_client is None:
        _mongodb_client = MongoDBClient()
        await _mongodb_client.connect()
    return _mongodb_client


async def close_mongodb():
    """Close global MongoDB connection"""
    global _mongodb_client
    if _mongodb_client:
        await _mongodb_client.disconnect()
        _mongodb_client = None


if __name__ == "__main__":
    import asyncio
    
    async def test_connection():
        """Test MongoDB connection"""
        print("🧪 Testing MongoDB connection...")
        
        client = MongoDBClient()
        await client.connect()
        
        # Test health check
        is_healthy = await client.health_check()
        print(f"Health check: {'✅ Passed' if is_healthy else '❌ Failed'}")
        
        # Test collection access
        collection = await client.get_collection('test_collection')
        print(f"Collection access: ✅ {collection.name}")
        
        # Create indexes
        await client.create_indexes()
        
        await client.disconnect()
        
        print("\n✅ MongoDB test complete!")
    
    asyncio.run(test_connection())

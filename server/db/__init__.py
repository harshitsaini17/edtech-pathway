"""
Database package for LearnPro Platform
"""
from .vector_store import VectorStore, get_vector_store
from .mongodb_client import MongoDBClient, get_mongodb, close_mongodb
from .student_profile import (
    StudentProfile,
    ModuleProgress,
    PerformanceMetrics,
    StudentProfileManager,
    LearningStyle,
    PacePreference
)

__all__ = [
    "VectorStore",
    "get_vector_store",
    "MongoDBClient",
    "get_mongodb",
    "close_mongodb",
    "StudentProfile",
    "ModuleProgress",
    "PerformanceMetrics",
    "StudentProfileManager",
    "LearningStyle",
    "PacePreference"
]


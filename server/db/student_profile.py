"""
Student Profile Management
==========================
MongoDB schemas and operations for student profiles, progress tracking,
quiz history, and performance metrics.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum

from db.mongodb_client import get_mongodb, MongoDBClient


class LearningStyle(str, Enum):
    """Learning style preferences"""
    VISUAL = "visual"
    AUDITORY = "auditory"
    READING = "reading"
    KINESTHETIC = "kinesthetic"
    MIXED = "mixed"


class PacePreference(str, Enum):
    """Learning pace preferences"""
    SLOW = "slow"
    MODERATE = "moderate"
    FAST = "fast"
    ADAPTIVE = "adaptive"


@dataclass
class StudentProfile:
    """Student profile data model"""
    student_id: str
    name: str
    email: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Learning preferences
    learning_style: LearningStyle = LearningStyle.MIXED
    pace_preference: PacePreference = PacePreference.ADAPTIVE
    preferred_difficulty: str = "medium"
    
    # Profile metadata
    active: bool = True
    total_modules_completed: int = 0
    total_quizzes_taken: int = 0
    overall_average_score: float = 0.0
    
    # Current learning state
    current_module: Optional[str] = None
    module_progress: List[Any] = field(default_factory=list)  # List of ModuleProgress
    
    # Customization
    settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB"""
        return asdict(self)


@dataclass
class ModuleProgress:
    """Progress tracking for a module"""
    student_id: str
    module_name: str
    curriculum_id: str
    
    # Status
    status: str = "not_started"  # not_started, in_progress, completed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    # Progress metrics
    topics_completed: List[str] = field(default_factory=list)
    total_topics: int = 0
    completion_percentage: float = 0.0
    
    # Performance
    average_quiz_score: float = 0.0
    quiz_attempts: List[str] = field(default_factory=list)  # Quiz attempt IDs
    
    # Time tracking
    total_time_spent_seconds: int = 0
    last_accessed_at: Optional[str] = None
    
    # Mastery
    topic_mastery_scores: Dict[str, float] = field(default_factory=dict)
    weak_topics: List[str] = field(default_factory=list)
    strong_topics: List[str] = field(default_factory=list)
    
    # Metadata
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics"""
    student_id: str
    calculated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Overall metrics
    total_quizzes_taken: int = 0
    average_score: float = 0.0
    median_score: float = 0.0
    
    # Difficulty performance
    easy_questions_accuracy: float = 0.0
    medium_questions_accuracy: float = 0.0
    hard_questions_accuracy: float = 0.0
    
    # Topic performance
    strongest_topics: List[Dict[str, Any]] = field(default_factory=list)
    weakest_topics: List[Dict[str, Any]] = field(default_factory=list)
    
    # Trends
    performance_trend: str = "stable"  # improving, declining, stable
    streak_days: int = 0
    last_activity_date: Optional[str] = None
    
    # Recommendations
    recommended_difficulty: str = "medium"
    needs_review: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class StudentProfileManager:
    """
    Manages student profiles and progress in MongoDB
    """
    
    def __init__(self, mongodb_client: Optional[MongoDBClient] = None):
        """Initialize profile manager"""
        self.mongodb = mongodb_client
        self._initialized = False
    
    async def initialize(self):
        """Initialize MongoDB connection"""
        if not self.mongodb:
            self.mongodb = await get_mongodb()
        self._initialized = True
    
    async def create_student_profile(
        self,
        student_id: str,
        name: str,
        email: Optional[str] = None,
        **kwargs
    ) -> StudentProfile:
        """
        Create a new student profile
        
        Args:
            student_id: Unique student identifier
            name: Student name
            email: Student email
            **kwargs: Additional profile fields
            
        Returns:
            Created student profile
        """
        if not self._initialized:
            await self.initialize()
        
        profile = StudentProfile(
            student_id=student_id,
            name=name,
            email=email,
            **kwargs
        )
        
        # Insert into MongoDB
        collection = await self.mongodb.get_collection('students')
        await collection.insert_one(profile.to_dict())
        
        print(f"✅ Created profile for student: {student_id}")
        return profile
    
    async def get_student_profile(self, student_id: str) -> Optional[StudentProfile]:
        """Get student profile by ID"""
        if not self._initialized:
            await self.initialize()
        
        collection = await self.mongodb.get_collection('students')
        profile_data = await collection.find_one({'student_id': student_id})
        
        if profile_data:
            profile_data.pop('_id', None)  # Remove MongoDB ID
            return StudentProfile(**profile_data)
        return None
    
    async def update_student_profile(
        self,
        student_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update student profile"""
        if not self._initialized:
            await self.initialize()
        
        updates['updated_at'] = datetime.now().isoformat()
        
        collection = await self.mongodb.get_collection('students')
        result = await collection.update_one(
            {'student_id': student_id},
            {'$set': updates}
        )
        
        return result.modified_count > 0
    
    async def create_module_progress(
        self,
        student_id: str,
        module_name: str,
        curriculum_id: str,
        total_topics: int
    ) -> ModuleProgress:
        """Create progress tracking for a module"""
        if not self._initialized:
            await self.initialize()
        
        progress = ModuleProgress(
            student_id=student_id,
            module_name=module_name,
            curriculum_id=curriculum_id,
            total_topics=total_topics,
            status="not_started"
        )
        
        collection = await self.mongodb.get_collection('student_progress')
        await collection.insert_one(progress.to_dict())
        
        print(f"✅ Created progress tracking: {student_id} - {module_name}")
        return progress
    
    async def get_module_progress(
        self,
        student_id: str,
        module_name: str
    ) -> Optional[ModuleProgress]:
        """Get progress for a specific module"""
        if not self._initialized:
            await self.initialize()
        
        collection = await self.mongodb.get_collection('student_progress')
        progress_data = await collection.find_one({
            'student_id': student_id,
            'module_name': module_name
        })
        
        if progress_data:
            progress_data.pop('_id', None)
            return ModuleProgress(**progress_data)
        return None
    
    async def update_module_progress(
        self,
        student_id: str,
        module_name: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update module progress"""
        if not self._initialized:
            await self.initialize()
        
        updates['updated_at'] = datetime.now().isoformat()
        
        collection = await self.mongodb.get_collection('student_progress')
        result = await collection.update_one(
            {'student_id': student_id, 'module_name': module_name},
            {'$set': updates}
        )
        
        return result.modified_count > 0
    
    async def mark_topic_complete(
        self,
        student_id: str,
        module_name: str,
        topic_name: str,
        mastery_score: float = 1.0
    ) -> bool:
        """Mark a topic as completed"""
        if not self._initialized:
            await self.initialize()
        
        collection = await self.mongodb.get_collection('student_progress')
        
        # Add topic to completed list and update mastery score
        result = await collection.update_one(
            {'student_id': student_id, 'module_name': module_name},
            {
                '$addToSet': {'topics_completed': topic_name},
                '$set': {
                    f'topic_mastery_scores.{topic_name}': mastery_score,
                    'updated_at': datetime.now().isoformat()
                }
            }
        )
        
        # Recalculate completion percentage
        progress = await self.get_module_progress(student_id, module_name)
        if progress and progress.total_topics > 0:
            completion = (len(progress.topics_completed) / progress.total_topics) * 100
            await self.update_module_progress(
                student_id,
                module_name,
                {'completion_percentage': completion}
            )
        
        return result.modified_count > 0
    
    async def save_quiz_attempt(
        self,
        attempt_data: Dict[str, Any]
    ) -> str:
        """
        Save quiz attempt to database
        
        Args:
            attempt_data: Quiz attempt data
            
        Returns:
            Attempt ID
        """
        if not self._initialized:
            await self.initialize()
        
        collection = await self.mongodb.get_collection('quiz_attempts')
        result = await collection.insert_one(attempt_data)
        
        attempt_id = attempt_data.get('attempt_id')
        
        # Update student profile
        student_id = attempt_data.get('student_id')
        await self.update_student_profile(
            student_id,
            {
                '$inc': {'total_quizzes_taken': 1}
            }
        )
        
        # Update module progress
        module_name = attempt_data.get('module_name')
        if module_name:
            await self.update_module_progress(
                student_id,
                module_name,
                {
                    '$push': {'quiz_attempts': attempt_id},
                    '$inc': {'total_time_spent_seconds': attempt_data.get('time_taken_seconds', 0)}
                }
            )
        
        return attempt_id
    
    async def get_quiz_attempts(
        self,
        student_id: str,
        module_name: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get quiz attempts for a student"""
        if not self._initialized:
            await self.initialize()
        
        collection = await self.mongodb.get_collection('quiz_attempts')
        
        query = {'student_id': student_id}
        if module_name:
            query['module_name'] = module_name
        
        cursor = collection.find(query).sort('completed_at', -1).limit(limit)
        attempts = []
        
        async for attempt in cursor:
            attempt.pop('_id', None)
            attempts.append(attempt)
        
        return attempts
    
    async def calculate_performance_metrics(
        self,
        student_id: str
    ) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        if not self._initialized:
            await self.initialize()
        
        # Get all quiz attempts
        attempts = await self.get_quiz_attempts(student_id, limit=100)
        
        if not attempts:
            return PerformanceMetrics(student_id=student_id)
        
        # Calculate metrics
        scores = [a['percentage'] for a in attempts]
        avg_score = sum(scores) / len(scores) if scores else 0
        median_score = sorted(scores)[len(scores) // 2] if scores else 0
        
        # Topic performance
        topic_scores = {}
        for attempt in attempts:
            analysis = attempt.get('analysis', {})
            topic_mastery = analysis.get('topic_mastery_scores', {})
            for topic, score in topic_mastery.items():
                if topic not in topic_scores:
                    topic_scores[topic] = []
                topic_scores[topic].append(score)
        
        # Calculate average per topic
        topic_averages = {
            topic: sum(scores) / len(scores)
            for topic, scores in topic_scores.items()
        }
        
        # Sort topics
        sorted_topics = sorted(topic_averages.items(), key=lambda x: x[1])
        weakest = [{'topic': t, 'score': s} for t, s in sorted_topics[:3]]
        strongest = [{'topic': t, 'score': s} for t, s in sorted_topics[-3:]]
        strongest.reverse()
        
        # Trend analysis
        if len(scores) >= 3:
            recent_avg = sum(scores[:3]) / 3
            older_avg = sum(scores[3:6]) / min(3, len(scores) - 3) if len(scores) > 3 else recent_avg
            
            if recent_avg > older_avg + 5:
                trend = "improving"
            elif recent_avg < older_avg - 5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        metrics = PerformanceMetrics(
            student_id=student_id,
            total_quizzes_taken=len(attempts),
            average_score=avg_score,
            median_score=median_score,
            strongest_topics=strongest,
            weakest_topics=weakest,
            performance_trend=trend,
            last_activity_date=attempts[0]['completed_at'] if attempts else None,
            needs_review=[t['topic'] for t in weakest]
        )
        
        return metrics
    
    async def get_all_student_progress(
        self,
        student_id: str
    ) -> List[ModuleProgress]:
        """Get all module progress for a student"""
        if not self._initialized:
            await self.initialize()
        
        collection = await self.mongodb.get_collection('student_progress')
        cursor = collection.find({'student_id': student_id})
        
        progress_list = []
        async for progress_data in cursor:
            progress_data.pop('_id', None)
            progress_list.append(ModuleProgress(**progress_data))
        
        return progress_list


if __name__ == "__main__":
    import asyncio
    
    async def test_profile_manager():
        """Test student profile management"""
        print("🧪 Testing Student Profile Manager...")
        
        manager = StudentProfileManager()
        await manager.initialize()
        
        # Create test profile
        profile = await manager.create_student_profile(
            student_id="test_student_001",
            name="Test Student",
            email="test@example.com"
        )
        print(f"Created profile: {profile.student_id}")
        
        # Create module progress
        progress = await manager.create_module_progress(
            student_id="test_student_001",
            module_name="Introduction to Probability",
            curriculum_id="curr_001",
            total_topics=10
        )
        print(f"Created progress: {progress.module_name}")
        
        # Mark topic complete
        await manager.mark_topic_complete(
            student_id="test_student_001",
            module_name="Introduction to Probability",
            topic_name="Random Variables",
            mastery_score=0.85
        )
        print("Marked topic complete")
        
        # Get updated progress
        updated_progress = await manager.get_module_progress(
            "test_student_001",
            "Introduction to Probability"
        )
        print(f"Topics completed: {updated_progress.topics_completed}")
        print(f"Completion: {updated_progress.completion_percentage:.1f}%")
        
        # Calculate metrics
        metrics = await manager.calculate_performance_metrics("test_student_001")
        print(f"Performance metrics: {metrics.average_score:.1f}%")
        
        print("\n✅ Profile manager test complete!")
    
    asyncio.run(test_profile_manager())

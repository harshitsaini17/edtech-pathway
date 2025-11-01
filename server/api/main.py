"""
FastAPI REST API
=================
Main API endpoints for the adaptive learning platform.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from config.settings import settings
from agent.learning_agent_orchestrator import LearningAgentOrchestrator, LearningState
from db.student_profile import StudentProfileManager, StudentProfile, ModuleProgress
from assessment.adaptive_quiz_generator import AdaptiveQuizGenerator
from assessment.quiz_analyzer import QuizAnalyzer
from cache.cache_manager import get_cache_manager


# Pydantic models for requests/responses
class TheoryRequest(BaseModel):
    """Request for theory content"""
    student_id: str
    module_name: str
    topic_name: Optional[str] = None


class TheoryResponse(BaseModel):
    """Response with theory content"""
    module_name: str
    topic_name: str
    content: str
    source: str  # cache or generated
    estimated_time_minutes: int


class QuizRequest(BaseModel):
    """Request to generate a quiz"""
    student_id: str
    module_name: str
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty: Optional[str] = None


class QuizResponse(BaseModel):
    """Response with quiz"""
    quiz_id: str
    module_name: str
    questions: List[Dict[str, Any]]
    total_questions: int
    estimated_time_minutes: int


class QuizSubmission(BaseModel):
    """Quiz submission from student"""
    student_id: str
    quiz_id: str
    answers: Dict[str, str]  # question_id -> answer
    time_taken_seconds: int


class QuizResult(BaseModel):
    """Quiz evaluation result"""
    quiz_id: str
    student_id: str
    score: float
    max_score: float
    percentage: float
    correct_answers: int
    total_questions: int
    weak_topics: List[str]
    mastery_score: float
    feedback: str


class ProfileResponse(BaseModel):
    """Student profile response"""
    student_id: str
    name: str
    email: str
    current_module: str
    enrolled_at: datetime
    module_progress: List[Dict[str, Any]]


class MetricsResponse(BaseModel):
    """Performance metrics response"""
    student_id: str
    overall_progress: float
    modules_completed: int
    total_modules: int
    average_score: float
    weak_areas: List[str]
    strong_areas: List[str]
    total_quizzes: int
    total_time_spent_seconds: int


class NextActionResponse(BaseModel):
    """Agent's recommended next action"""
    student_id: str
    current_state: str
    next_action: str
    reasoning: str
    metadata: Dict[str, Any]


# Initialize FastAPI app
app = FastAPI(
    title="LearnPro Adaptive Learning API",
    description="Agentic RAG-based adaptive learning platform with real-time curriculum adaptation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
orchestrator = LearningAgentOrchestrator()
profile_manager = StudentProfileManager()
quiz_generator = AdaptiveQuizGenerator()
quiz_analyzer = QuizAnalyzer()
cache_manager = get_cache_manager()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Starting LearnPro API...")
    
    # Connect to databases
    await profile_manager.db_client.connect()
    
    # Check Redis connection
    health = await cache_manager.health_check()
    if health["status"] != "healthy":
        print("⚠️ Redis cache not available")
    
    print("✅ LearnPro API ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Shutting down LearnPro API...")
    
    # Close database connections
    await profile_manager.db_client.close()
    
    print("✅ Shutdown complete")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LearnPro Adaptive Learning API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check MongoDB
    mongo_health = await profile_manager.db_client.health_check()
    
    # Check Redis
    redis_health = await cache_manager.health_check()
    
    return {
        "status": "healthy" if mongo_health and redis_health["status"] == "healthy" else "degraded",
        "services": {
            "mongodb": "up" if mongo_health else "down",
            "redis": redis_health["status"]
        },
        "timestamp": datetime.now().isoformat()
    }


# Profile Endpoints
@app.post("/api/v1/profile", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    student_id: str,
    name: str,
    email: str
):
    """Create a new student profile"""
    try:
        # Check if profile exists
        existing = profile_manager.get_profile(student_id)
        if existing:
            raise HTTPException(status_code=400, detail="Profile already exists")
        
        # Create profile
        profile = StudentProfile(
            student_id=student_id,
            name=name,
            email=email,
            current_module="Module_1"
        )
        
        created = profile_manager.create_profile(profile)
        
        return ProfileResponse(
            student_id=created.student_id,
            name=created.name,
            email=created.email,
            current_module=created.current_module,
            enrolled_at=created.enrolled_at,
            module_progress=[]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/profile/{student_id}", response_model=ProfileResponse)
async def get_profile(student_id: str):
    """Get student profile"""
    profile = profile_manager.get_profile(student_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return ProfileResponse(
        student_id=profile.student_id,
        name=profile.name,
        email=profile.email,
        current_module=profile.current_module,
        enrolled_at=profile.enrolled_at,
        module_progress=[
            {
                "module_name": m.module_name,
                "mastery_score": m.mastery_score,
                "completed": m.completed,
                "weak_areas": m.weak_areas,
                "started_at": m.started_at.isoformat()
            }
            for m in profile.module_progress
        ]
    )


# Theory Endpoints
@app.post("/api/v1/theory", response_model=TheoryResponse)
async def get_theory(request: TheoryRequest):
    """Get theory content for a module/topic"""
    try:
        # Check cache first
        cache_key = f"theory:{request.module_name}:{request.topic_name or 'all'}"
        cached = cache_manager.get(cache_key)
        
        if cached:
            return TheoryResponse(
                module_name=request.module_name,
                topic_name=request.topic_name or "General",
                content=cached,
                source="cache",
                estimated_time_minutes=10
            )
        
        # Generate theory (placeholder - actual implementation uses flexible_module_theory_generator)
        content = f"Theory content for {request.module_name}"
        if request.topic_name:
            content += f" - {request.topic_name}"
        
        # Cache it
        await cache_manager.set_with_ttl(cache_key, content, ttl=3600)
        
        return TheoryResponse(
            module_name=request.module_name,
            topic_name=request.topic_name or "General",
            content=content,
            source="generated",
            estimated_time_minutes=10
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Quiz Endpoints
@app.post("/api/v1/quiz", response_model=QuizResponse)
async def generate_quiz(request: QuizRequest):
    """Generate an adaptive quiz"""
    try:
        # Generate quiz
        quiz = quiz_generator.generate_quiz(
            module_name=request.module_name,
            num_questions=request.num_questions
        )
        
        # Cache quiz
        quiz_id = quiz.get("quiz_id", "unknown")
        cache_manager.cache_quiz(quiz_id, quiz)
        
        return QuizResponse(
            quiz_id=quiz_id,
            module_name=quiz.get("module_name"),
            questions=quiz.get("questions", []),
            total_questions=len(quiz.get("questions", [])),
            estimated_time_minutes=quiz.get("estimated_time_minutes", 15)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/quiz/submit", response_model=QuizResult)
async def submit_quiz(submission: QuizSubmission):
    """Submit quiz answers for evaluation"""
    try:
        # Get quiz from cache
        cached_quiz = cache_manager.get(f"quiz:{submission.quiz_id}")
        
        if not cached_quiz:
            raise HTTPException(status_code=404, detail="Quiz not found or expired")
        
        # Analyze quiz
        analysis = quiz_analyzer.analyze_quiz_submission(
            quiz_data=cached_quiz,
            student_answers=submission.answers,
            student_id=submission.student_id
        )
        
        # Update student profile
        module_name = cached_quiz.get("module_name")
        profile_manager.add_quiz_attempt(
            student_id=submission.student_id,
            module_name=module_name,
            quiz_id=submission.quiz_id,
            score=analysis["overall_metrics"]["percentage"],
            max_score=100.0
        )
        
        return QuizResult(
            quiz_id=submission.quiz_id,
            student_id=submission.student_id,
            score=analysis["overall_metrics"]["score"],
            max_score=analysis["overall_metrics"]["max_score"],
            percentage=analysis["overall_metrics"]["percentage"],
            correct_answers=analysis["overall_metrics"]["correct_answers"],
            total_questions=analysis["overall_metrics"]["total_questions"],
            weak_topics=analysis["weak_areas"],
            mastery_score=analysis["overall_metrics"].get("mastery_score", 0.0),
            feedback=analysis["summary"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Metrics Endpoints
@app.get("/api/v1/metrics/{student_id}", response_model=MetricsResponse)
async def get_metrics(student_id: str):
    """Get student performance metrics"""
    profile = profile_manager.get_profile(student_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Calculate metrics
    total_modules = len(profile.module_progress)
    completed_modules = sum(1 for m in profile.module_progress if m.completed)
    
    avg_score = sum(m.mastery_score for m in profile.module_progress) / total_modules if total_modules > 0 else 0
    
    # Aggregate weak and strong areas
    weak_areas = []
    strong_areas = []
    total_quizzes = 0
    total_time = 0
    
    for module in profile.module_progress:
        weak_areas.extend(module.weak_areas)
        total_quizzes += len(module.quiz_attempts)
        total_time += module.time_spent_seconds
        
        if module.mastery_score >= 0.8:
            strong_areas.append(module.module_name)
    
    return MetricsResponse(
        student_id=student_id,
        overall_progress=completed_modules / total_modules * 100 if total_modules > 0 else 0,
        modules_completed=completed_modules,
        total_modules=total_modules,
        average_score=avg_score * 100,
        weak_areas=list(set(weak_areas)),
        strong_areas=strong_areas,
        total_quizzes=total_quizzes,
        total_time_spent_seconds=total_time
    )


# Agent Endpoints
@app.get("/api/v1/agent/next-action/{student_id}", response_model=NextActionResponse)
async def get_next_action(student_id: str):
    """Get agent's recommended next action for student"""
    try:
        # Make decision
        decision = orchestrator.make_decision(student_id)
        
        return NextActionResponse(
            student_id=student_id,
            current_state=decision.current_state.value,
            next_action=decision.action,
            reasoning=decision.reasoning,
            metadata=decision.metadata
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/agent/execute/{student_id}")
async def execute_action(student_id: str):
    """Execute the agent's recommended action"""
    try:
        # Make decision
        decision = orchestrator.make_decision(student_id)
        
        # Execute action
        result = orchestrator.execute_action(decision)
        
        return {
            "success": result["success"],
            "action": result["action"],
            "message": result["message"],
            "data": result.get("data", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# System Endpoints
@app.get("/api/v1/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    stats = await cache_manager.get_stats()
    return stats


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting LearnPro API server...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

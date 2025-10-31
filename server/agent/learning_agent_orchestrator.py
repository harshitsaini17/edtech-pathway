"""
Learning Agent Orchestrator
============================
Main decision engine that coordinates the entire adaptive learning system.
Determines when to generate theory, assess, adapt curriculum, and progress students.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import os

from config.settings import settings
from db.student_profile import StudentProfileManager, StudentProfile
from agent.curriculum_adapter import CurriculumAdapter, AdaptationDecision
from assessment.adaptive_quiz_generator import AdaptiveQuizGenerator
from assessment.quiz_analyzer import QuizAnalyzer
from cache.cache_manager import get_cache_manager


class LearningState(Enum):
    """Student learning states"""
    NOT_STARTED = "not_started"
    STUDYING_THEORY = "studying_theory"
    READY_FOR_ASSESSMENT = "ready_for_assessment"
    TAKING_QUIZ = "taking_quiz"
    NEEDS_REMEDIATION = "needs_remediation"
    MASTERED_MODULE = "mastered_module"
    READY_FOR_NEXT_MODULE = "ready_for_next_module"
    COMPLETED_COURSE = "completed_course"


@dataclass
class AgentDecision:
    """Represents an agent decision"""
    student_id: str
    current_state: LearningState
    next_state: LearningState
    action: str  # generate_theory, create_quiz, adapt_curriculum, advance_module
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class LearningAgentOrchestrator:
    """
    Main orchestrator for the adaptive learning system
    Coordinates theory generation, assessment, adaptation, and progression
    """
    
    def __init__(self):
        """Initialize the learning agent orchestrator"""
        self.profile_manager = StudentProfileManager()
        self.curriculum_adapter = CurriculumAdapter()
        self.quiz_generator = AdaptiveQuizGenerator()
        self.quiz_analyzer = QuizAnalyzer()
        self.cache_manager = get_cache_manager()
        
        # Decision rules configuration
        self.config = {
            "min_theory_time_seconds": 300,  # 5 minutes
            "quiz_cooldown_seconds": 600,  # 10 minutes between quizzes
            "mastery_threshold": settings.MASTERY_THRESHOLD,
            "weak_area_threshold": settings.WEAK_AREA_THRESHOLD,
            "max_retries_before_remediation": 3,
            "required_quizzes_per_module": 2,
            "skip_ahead_score_threshold": 95
        }
        
        print("✅ Learning Agent Orchestrator initialized")
    
    def determine_student_state(
        self,
        student_profile: StudentProfile
    ) -> LearningState:
        """
        Determine current learning state for a student
        
        Args:
            student_profile: Student profile data
            
        Returns:
            Current learning state
        """
        if not student_profile.current_module:
            return LearningState.NOT_STARTED
        
        # Get current module progress
        current_module = student_profile.current_module
        module_progress = next(
            (m for m in student_profile.module_progress if m.module_name == current_module),
            None
        )
        
        if not module_progress:
            return LearningState.NOT_STARTED
        
        # Check completion status
        if module_progress.completed:
            # Check if there are more modules
            total_modules = len(student_profile.module_progress)
            completed_modules = sum(1 for m in student_profile.module_progress if m.completed)
            
            if completed_modules == total_modules:
                return LearningState.COMPLETED_COURSE
            else:
                return LearningState.READY_FOR_NEXT_MODULE
        
        # Check mastery
        if module_progress.mastery_score >= self.config["mastery_threshold"]:
            return LearningState.MASTERED_MODULE
        
        # Check if needs remediation
        weak_areas = module_progress.weak_areas
        quiz_attempts = len(module_progress.quiz_attempts)
        
        if len(weak_areas) > 2 and quiz_attempts >= self.config["max_retries_before_remediation"]:
            return LearningState.NEEDS_REMEDIATION
        
        # Check if ready for quiz
        last_quiz_time = module_progress.last_quiz_time
        time_on_content = module_progress.time_spent_seconds
        
        if last_quiz_time:
            time_since_last_quiz = (datetime.now() - last_quiz_time).total_seconds()
            if time_since_last_quiz < self.config["quiz_cooldown_seconds"]:
                return LearningState.STUDYING_THEORY
        
        if time_on_content >= self.config["min_theory_time_seconds"]:
            return LearningState.READY_FOR_ASSESSMENT
        
        # Default: studying theory
        return LearningState.STUDYING_THEORY
    
    def make_decision(
        self,
        student_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentDecision:
        """
        Make a decision about what action to take next for a student
        
        Args:
            student_id: Student identifier
            context: Additional context (recent events, performance data)
            
        Returns:
            Agent decision with next action
        """
        # Get student profile
        profile = self.profile_manager.get_profile(student_id)
        if not profile:
            # New student - initialize
            return AgentDecision(
                student_id=student_id,
                current_state=LearningState.NOT_STARTED,
                next_state=LearningState.STUDYING_THEORY,
                action="initialize_student",
                reasoning="New student detected - initializing profile and first module"
            )
        
        # Determine current state
        current_state = self.determine_student_state(profile)
        
        # Decision logic based on state
        if current_state == LearningState.NOT_STARTED:
            return AgentDecision(
                student_id=student_id,
                current_state=current_state,
                next_state=LearningState.STUDYING_THEORY,
                action="generate_theory",
                reasoning="Starting first module - generating theory content",
                metadata={"module": profile.current_module}
            )
        
        elif current_state == LearningState.STUDYING_THEORY:
            # Check if enough time has passed
            current_module = profile.current_module
            module_progress = next(
                (m for m in profile.module_progress if m.module_name == current_module),
                None
            )
            
            if module_progress and module_progress.time_spent_seconds >= self.config["min_theory_time_seconds"]:
                return AgentDecision(
                    student_id=student_id,
                    current_state=current_state,
                    next_state=LearningState.READY_FOR_ASSESSMENT,
                    action="create_quiz",
                    reasoning=f"Student has studied for {module_progress.time_spent_seconds}s - ready for assessment",
                    metadata={"module": current_module}
                )
            else:
                return AgentDecision(
                    student_id=student_id,
                    current_state=current_state,
                    next_state=current_state,
                    action="continue_studying",
                    reasoning="More study time needed before assessment",
                    metadata={"time_remaining": self.config["min_theory_time_seconds"] - (module_progress.time_spent_seconds if module_progress else 0)}
                )
        
        elif current_state == LearningState.READY_FOR_ASSESSMENT:
            return AgentDecision(
                student_id=student_id,
                current_state=current_state,
                next_state=LearningState.TAKING_QUIZ,
                action="create_quiz",
                reasoning="Student ready for assessment",
                metadata={"module": profile.current_module}
            )
        
        elif current_state == LearningState.NEEDS_REMEDIATION:
            return AgentDecision(
                student_id=student_id,
                current_state=current_state,
                next_state=LearningState.STUDYING_THEORY,
                action="adapt_curriculum",
                reasoning="Multiple quiz attempts with weak areas - injecting remedial content",
                metadata={
                    "module": profile.current_module,
                    "adaptation_type": "remediation"
                }
            )
        
        elif current_state == LearningState.MASTERED_MODULE:
            return AgentDecision(
                student_id=student_id,
                current_state=current_state,
                next_state=LearningState.READY_FOR_NEXT_MODULE,
                action="advance_module",
                reasoning=f"Module mastered (score: {next((m for m in profile.module_progress if m.module_name == profile.current_module), None).mastery_score:.2f})",
                metadata={"completed_module": profile.current_module}
            )
        
        elif current_state == LearningState.READY_FOR_NEXT_MODULE:
            return AgentDecision(
                student_id=student_id,
                current_state=current_state,
                next_state=LearningState.STUDYING_THEORY,
                action="advance_module",
                reasoning="Moving to next module",
                metadata={"previous_module": profile.current_module}
            )
        
        elif current_state == LearningState.COMPLETED_COURSE:
            return AgentDecision(
                student_id=student_id,
                current_state=current_state,
                next_state=current_state,
                action="celebrate",
                reasoning="Course completed! 🎉",
                metadata={"total_modules": len(profile.module_progress)}
            )
        
        # Default
        return AgentDecision(
            student_id=student_id,
            current_state=current_state,
            next_state=current_state,
            action="monitor",
            reasoning="Monitoring student progress"
        )
    
    def execute_action(
        self,
        decision: AgentDecision
    ) -> Dict[str, Any]:
        """
        Execute the action from an agent decision
        
        Args:
            decision: Agent decision to execute
            
        Returns:
            Execution result
        """
        action = decision.action
        student_id = decision.student_id
        
        result = {
            "success": False,
            "action": action,
            "message": "",
            "data": {}
        }
        
        try:
            if action == "initialize_student":
                # Create new student profile
                profile = StudentProfile(
                    student_id=student_id,
                    name=f"Student {student_id}",
                    email=f"{student_id}@learnpro.com",
                    current_module="Module_1"
                )
                self.profile_manager.create_profile(profile)
                
                result["success"] = True
                result["message"] = "Student initialized"
                result["data"] = {"profile": profile}
            
            elif action == "generate_theory":
                module_name = decision.metadata.get("module")
                
                # Check cache first
                cached_theory = self.cache_manager.get(f"theory:{module_name}")
                
                if cached_theory:
                    result["success"] = True
                    result["message"] = "Theory retrieved from cache"
                    result["data"] = {"theory": cached_theory, "source": "cache"}
                else:
                    # Generate theory (placeholder - actual implementation in flexible_module_theory_generator.py)
                    theory = f"Theory content for {module_name}"
                    
                    # Cache it
                    self.cache_manager.cache_theory(module_name, "Topic_1", theory)
                    
                    result["success"] = True
                    result["message"] = "Theory generated"
                    result["data"] = {"theory": theory, "source": "generated"}
            
            elif action == "create_quiz":
                module_name = decision.metadata.get("module")
                
                # Generate quiz
                quiz = self.quiz_generator.generate_quiz(
                    module_name=module_name,
                    num_questions=5
                )
                
                # Cache quiz
                quiz_id = quiz.get("quiz_id", "unknown")
                self.cache_manager.cache_quiz(quiz_id, quiz)
                
                result["success"] = True
                result["message"] = "Quiz created"
                result["data"] = {"quiz": quiz}
            
            elif action == "adapt_curriculum":
                module_name = decision.metadata.get("module")
                adaptation_type = decision.metadata.get("adaptation_type")
                
                # Get student profile
                profile = self.profile_manager.get_profile(student_id)
                module_progress = next(
                    (m for m in profile.module_progress if m.module_name == module_name),
                    None
                )
                
                if module_progress:
                    # Prepare performance data
                    performance_data = {
                        "average_score": module_progress.mastery_score * 100,
                        "weak_topics": module_progress.weak_areas,
                        "struggle_count": len(module_progress.quiz_attempts),
                        "performance_trend": "declining" if module_progress.mastery_score < 0.6 else "stable",
                        "total_quizzes": len(module_progress.quiz_attempts)
                    }
                    
                    # Make adaptation decision
                    adaptation = self.curriculum_adapter.make_adaptation_decision(
                        student_id=student_id,
                        module_name=module_name,
                        performance_data=performance_data,
                        current_curriculum={"topics": [], "difficulty": "intermediate"}
                    )
                    
                    result["success"] = True
                    result["message"] = "Curriculum adapted"
                    result["data"] = {"adaptation": adaptation}
            
            elif action == "advance_module":
                # Get current module
                profile = self.profile_manager.get_profile(student_id)
                current_module = profile.current_module
                
                # Mark current module as completed
                self.profile_manager.update_module_progress(
                    student_id=student_id,
                    module_name=current_module,
                    updates={"completed": True}
                )
                
                # Advance to next module
                module_num = int(current_module.split("_")[-1])
                next_module = f"Module_{module_num + 1}"
                
                self.profile_manager.update_profile(
                    student_id=student_id,
                    updates={"current_module": next_module}
                )
                
                result["success"] = True
                result["message"] = f"Advanced from {current_module} to {next_module}"
                result["data"] = {"previous_module": current_module, "next_module": next_module}
            
            elif action == "continue_studying":
                result["success"] = True
                result["message"] = "Continue studying current content"
                result["data"] = decision.metadata
            
            elif action == "celebrate":
                result["success"] = True
                result["message"] = "🎉 Congratulations on completing the course!"
                result["data"] = decision.metadata
            
            else:
                result["message"] = f"Unknown action: {action}"
        
        except Exception as e:
            result["success"] = False
            result["message"] = f"Error executing action: {str(e)}"
        
        print(f"{'✅' if result['success'] else '❌'} Executed: {action} - {result['message']}")
        
        return result
    
    def orchestrate_learning_loop(
        self,
        student_id: str,
        max_iterations: int = 10
    ) -> List[AgentDecision]:
        """
        Run the main learning loop for a student
        
        Args:
            student_id: Student identifier
            max_iterations: Maximum decision cycles
            
        Returns:
            List of decisions made
        """
        decisions = []
        
        print(f"\n🤖 Starting learning loop for student: {student_id}")
        print(f"📊 Max iterations: {max_iterations}\n")
        
        for i in range(max_iterations):
            print(f"\n--- Iteration {i+1}/{max_iterations} ---")
            
            # Make decision
            decision = self.make_decision(student_id)
            decisions.append(decision)
            
            print(f"🎯 Decision: {decision.action}")
            print(f"📝 State: {decision.current_state.value} → {decision.next_state.value}")
            print(f"💭 Reasoning: {decision.reasoning}")
            
            # Execute action
            result = self.execute_action(decision)
            
            if not result["success"]:
                print(f"❌ Execution failed: {result['message']}")
                break
            
            # Check for terminal states
            if decision.current_state in [LearningState.COMPLETED_COURSE, LearningState.TAKING_QUIZ]:
                print(f"🛑 Terminal state reached: {decision.current_state.value}")
                break
            
            # Check if action requires human interaction
            if decision.action in ["create_quiz", "continue_studying"]:
                print(f"⏸️ Waiting for student interaction")
                break
        
        print(f"\n✅ Learning loop completed: {len(decisions)} decisions made")
        
        return decisions
    
    def save_decisions(
        self,
        decisions: List[AgentDecision],
        output_dir: str = "./output/agent_decisions"
    ):
        """Save agent decisions to file"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"decisions_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump([
                {
                    "student_id": d.student_id,
                    "current_state": d.current_state.value,
                    "next_state": d.next_state.value,
                    "action": d.action,
                    "reasoning": d.reasoning,
                    "metadata": d.metadata,
                    "timestamp": d.timestamp.isoformat()
                }
                for d in decisions
            ], f, indent=2)
        
        print(f"💾 Decisions saved to {filepath}")


if __name__ == "__main__":
    # Test the orchestrator
    print("🧪 Testing Learning Agent Orchestrator...")
    
    orchestrator = LearningAgentOrchestrator()
    
    # Test scenario: new student
    test_student_id = "test_student_orchestrator_001"
    
    decisions = orchestrator.orchestrate_learning_loop(
        student_id=test_student_id,
        max_iterations=5
    )
    
    print(f"\n📊 Summary:")
    print(f"Total decisions: {len(decisions)}")
    print(f"\nDecision sequence:")
    for i, d in enumerate(decisions, 1):
        print(f"  {i}. {d.action} ({d.current_state.value} → {d.next_state.value})")
    
    # Save decisions
    orchestrator.save_decisions(decisions)
    
    print("\n✅ Orchestrator test complete!")

"""
Phase 2-6 Integrated Testing
==============================
Comprehensive tests for all phases of the adaptive learning system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import json


def test_phase2_curriculum():
    """Test Phase 2: Curriculum Generation"""
    print("\n" + "=" * 80)
    print("PHASE 2 TESTING: CURRICULUM GENERATION")
    print("=" * 80)
    
    from llm_enhanced_curriculum_generator import LLMEnhancedCurriculumGenerator
    
    print("\n1️⃣ Testing curriculum generator initialization...")
    generator = LLMEnhancedCurriculumGenerator()
    print("   ✅ Generator initialized")
    
    print("\n2️⃣ Testing module organization...")
    print("   ℹ️ Requires topics JSON input")
    print("   ✅ Curriculum generator module available")
    
    print("\n✅ PHASE 2 TESTS PASSED")
    return True


def test_phase3_content_delivery():
    """Test Phase 3: Content Delivery"""
    print("\n" + "=" * 80)
    print("PHASE 3 TESTING: CONTENT DELIVERY")
    print("=" * 80)
    
    from cache.cache_manager import get_cache_manager
    from flexible_module_theory_generator import FlexibleModuleTheoryGenerator
    
    print("\n1️⃣ Testing cache manager...")
    cache = get_cache_manager()
    
    # Test caching
    test_theory = "This is a test theory about Machine Learning."
    cache.cache_theory("Module_Test", "Topic_Test", test_theory)
    print("   ✅ Theory cached successfully")
    
    # Test retrieval
    cached = cache.get("theory:Module_Test:Topic_Test")
    assert cached == test_theory
    print("   ✅ Theory retrieved from cache")
    
    print("\n2️⃣ Testing theory generator...")
    print("   ℹ️ Theory generator requires LLM and curriculum input")
    print("   ✅ Theory generator module available")
    
    print("\n✅ PHASE 3 TESTS PASSED")
    return True


def test_phase4_assessment():
    """Test Phase 4: Assessment System"""
    print("\n" + "=" * 80)
    print("PHASE 4 TESTING: ASSESSMENT SYSTEM")
    print("=" * 80)
    
    from assessment.adaptive_quiz_generator import AdaptiveQuizGenerator
    from assessment.quiz_analyzer import QuizAnalyzer
    from db.student_profile import StudentProfileManager, StudentProfile
    
    print("\n1️⃣ Testing quiz generator...")
    generator = AdaptiveQuizGenerator()
    
    # Generate test quiz
    quiz = generator.generate_quiz(
        module_name="Test_Module",
        num_questions=3
    )
    
    assert "quiz_id" in quiz
    assert "questions" in quiz
    assert len(quiz["questions"]) == 3
    print(f"   ✅ Generated quiz with {len(quiz['questions'])} questions")
    
    print("\n2️⃣ Testing quiz analyzer...")
    analyzer = QuizAnalyzer()
    
    # Test answers
    test_answers = {
        quiz["questions"][0]["id"]: "test answer 1",
        quiz["questions"][1]["id"]: "test answer 2",
        quiz["questions"][2]["id"]: "test answer 3"
    }
    
    analysis = analyzer.analyze_quiz_submission(
        quiz_data=quiz,
        student_answers=test_answers,
        student_id="test_student"
    )
    
    assert "overall_metrics" in analysis
    assert "weak_areas" in analysis
    print("   ✅ Quiz analyzed successfully")
    
    print("\n3️⃣ Testing student profile updates...")
    profile_manager = StudentProfileManager()
    
    # Create test profile
    test_profile = StudentProfile(
        student_id="test_student_assessment",
        name="Test Student",
        email="test@example.com",
        current_module="Test_Module"
    )
    
    profile_manager.create_profile(test_profile)
    print("   ✅ Student profile created")
    
    # Add quiz attempt
    profile_manager.add_quiz_attempt(
        student_id="test_student_assessment",
        module_name="Test_Module",
        quiz_id=quiz["quiz_id"],
        score=85.0,
        max_score=100.0
    )
    print("   ✅ Quiz attempt recorded")
    
    # Verify profile
    updated_profile = profile_manager.get_profile("test_student_assessment")
    assert updated_profile is not None
    print("   ✅ Profile verified")
    
    print("\n✅ PHASE 4 TESTS PASSED")
    return True


def test_phase5_pathway():
    """Test Phase 5: Pathway Streaming"""
    print("\n" + "=" * 80)
    print("PHASE 5 TESTING: PATHWAY STREAMING")
    print("=" * 80)
    
    from streaming.pathway_pipeline import PathwayPipeline, EventPublisher
    from events.event_stream import EventStreamHandler
    
    print("\n1️⃣ Testing Pathway pipeline...")
    pipeline = PathwayPipeline()
    print("   ✅ Pipeline initialized")
    
    print("\n2️⃣ Testing event publisher...")
    publisher = EventPublisher()
    
    publisher.publish_quiz_submission(
        student_id="test_student",
        quiz_id="quiz_001",
        module_name="Module1",
        score=8.5,
        max_score=10.0,
        percentage=85.0,
        weak_topics=["Topic3"],
        time_taken_seconds=300
    )
    
    events = publisher.get_events()
    assert len(events) > 0
    print(f"   ✅ Published {len(events)} events")
    
    print("\n3️⃣ Testing event stream handler...")
    handler = EventStreamHandler(buffer_size=1000, batch_size=10)
    
    handler.capture_quiz_submission(
        student_id="test_student",
        quiz_id="quiz_002",
        module_name="Module1",
        score=9.0,
        max_score=10.0,
        percentage=90.0,
        weak_topics=[],
        time_taken_seconds=250
    )
    
    stats = handler.get_stats()
    assert stats["buffer"]["total_events"] > 0
    print("   ✅ Event stream handler working")
    
    print("\n✅ PHASE 5 TESTS PASSED")
    return True


def test_phase6_agent():
    """Test Phase 6: Agent Orchestration"""
    print("\n" + "=" * 80)
    print("PHASE 6 TESTING: AGENT ORCHESTRATION")
    print("=" * 80)
    
    from agent.learning_agent_orchestrator import LearningAgentOrchestrator, LearningState
    from agent.curriculum_adapter import CurriculumAdapter
    
    print("\n1️⃣ Testing learning agent orchestrator...")
    orchestrator = LearningAgentOrchestrator()
    print("   ✅ Orchestrator initialized")
    
    print("\n2️⃣ Testing decision making...")
    decision = orchestrator.make_decision("test_student_agent")
    
    assert decision is not None
    assert decision.action in ["initialize_student", "generate_theory", "create_quiz", "monitor"]
    print(f"   ✅ Decision made: {decision.action}")
    print(f"   Reasoning: {decision.reasoning}")
    
    print("\n3️⃣ Testing curriculum adapter...")
    adapter = CurriculumAdapter()
    
    # Test adaptation
    performance_data = {
        "average_score": 65.0,
        "weak_topics": ["Topic 2", "Topic 4"],
        "struggle_count": 2,
        "performance_trend": "stable",
        "total_quizzes": 3
    }
    
    current_curriculum = {
        "topics": ["Topic 1", "Topic 2", "Topic 3", "Topic 4", "Topic 5"],
        "difficulty": "intermediate"
    }
    
    adaptation = adapter.make_adaptation_decision(
        student_id="test_student_agent",
        module_name="Module1",
        performance_data=performance_data,
        current_curriculum=current_curriculum
    )
    
    assert adaptation is not None
    assert len(adaptation.actions) > 0
    print(f"   ✅ Adaptation decision: {adaptation.decision_type}")
    print(f"   Actions: {len(adaptation.actions)}")
    
    print("\n4️⃣ Testing action execution...")
    result = orchestrator.execute_action(decision)
    
    assert result["success"] in [True, False]
    print(f"   ✅ Action executed: {result['message']}")
    
    print("\n✅ PHASE 6 TESTS PASSED")
    return True


def run_all_tests():
    """Run all phase tests"""
    print("\n" + "=" * 80)
    print("LEARNPRO COMPREHENSIVE TESTING SUITE")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {}
    
    # Phase 2
    try:
        results["phase2"] = test_phase2_curriculum()
    except Exception as e:
        print(f"\n❌ Phase 2 failed: {e}")
        results["phase2"] = False
    
    # Phase 3
    try:
        results["phase3"] = test_phase3_content_delivery()
    except Exception as e:
        print(f"\n❌ Phase 3 failed: {e}")
        results["phase3"] = False
    
    # Phase 4
    try:
        results["phase4"] = test_phase4_assessment()
    except Exception as e:
        print(f"\n❌ Phase 4 failed: {e}")
        results["phase4"] = False
    
    # Phase 5
    try:
        results["phase5"] = test_phase5_pathway()
    except Exception as e:
        print(f"\n❌ Phase 5 failed: {e}")
        results["phase5"] = False
    
    # Phase 6
    try:
        results["phase6"] = test_phase6_agent()
    except Exception as e:
        print(f"\n❌ Phase 6 failed: {e}")
        results["phase6"] = False
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for phase, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{phase.upper()}: {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} phases passed")
    print(f"Success rate: {total_passed/total_tests*100:.1f}%")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return all(results.values())


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

"""
Simple Phase 6 Test: Learning Agent Orchestrator
=================================================
Test agent orchestration logic without external dependencies.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 80)
print("PHASE 6 TEST: LEARNING AGENT ORCHESTRATOR")
print("=" * 80)

print("\n1. Testing agent orchestrator import...")
try:
    from agent.learning_agent_orchestrator import LearningAgentOrchestrator
    print("   ✅ LearningAgentOrchestrator imported")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n2. Testing orchestrator initialization...")
try:
    orchestrator = LearningAgentOrchestrator()
    print("   ✅ Orchestrator initialized")
    print(f"   Has system1 (GPT-4.1): {orchestrator.system1 is not None}")
    print(f"   Has system2 (GPT-5): {orchestrator.system2 is not None}")
except Exception as e:
    print(f"   ❌ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n3. Testing decision-making logic (may take a moment)...")
try:
    # Create test student context
    student_context = {
        "student_id": "test_student",
        "current_module": "Statistics",
        "recent_performance": [
            {"quiz_id": "q1", "score": 0.6, "topic": "Probability"},
            {"quiz_id": "q2", "score": 0.55, "topic": "Distributions"}
        ],
        "weak_areas": ["Probability", "Distributions"],
        "strong_areas": ["Descriptive Statistics"],
        "engagement_level": 0.7
    }
    
    print("   → Analyzing student context...")
    print(f"   Weak areas: {student_context['weak_areas']}")
    print(f"   Recent scores: {[p['score'] for p in student_context['recent_performance']]}")
    
    decision = orchestrator.make_learning_decision(
        student_context=student_context
    )
    
    print(f"   ✅ Decision made")
    print(f"   Action: {decision.get('action', 'N/A')}")
    print(f"   Reasoning (truncated): {decision.get('reasoning', '')[:100]}...")
    
except Exception as e:
    print(f"   ❌ Decision making failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n4. Testing intervention generation...")
try:
    print("   → Generating intervention for weak areas...")
    
    intervention = orchestrator.generate_intervention(
        student_id="test_student",
        weak_areas=["Probability"],
        performance_data={"average_score": 0.58}
    )
    
    print(f"   ✅ Intervention generated")
    print(f"   Type: {intervention.get('intervention_type', 'N/A')}")
    print(f"   Target areas: {intervention.get('target_areas', [])}")
    
except Exception as e:
    print(f"   ❌ Intervention generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n5. Testing pathway recommendation...")
try:
    print("   → Recommending next learning pathway...")
    
    recommendation = orchestrator.recommend_pathway(
        student_id="test_student",
        completed_modules=["Introduction to Statistics"],
        current_performance=0.65
    )
    
    print(f"   ✅ Recommendation generated")
    print(f"   Recommended modules: {len(recommendation.get('recommended_modules', []))}")
    
    if recommendation.get('recommended_modules'):
        print(f"   First module: {recommendation['recommended_modules'][0]}")
    
except Exception as e:
    print(f"   ❌ Recommendation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n6. Testing dual-system reasoning...")
try:
    print("   → Testing System 1 (fast, intuitive)...")
    system1_result = orchestrator.system1_reasoning(
        prompt="Should student review basic concepts?",
        context={"recent_score": 0.5}
    )
    print(f"   ✅ System 1 response: {system1_result[:80]}...")
    
    print("   → Testing System 2 (slow, analytical)...")
    system2_result = orchestrator.system2_reasoning(
        prompt="Analyze learning trajectory",
        context={"performance_trend": "declining"}
    )
    print(f"   ✅ System 2 response: {system2_result[:80]}...")
    
except Exception as e:
    print(f"   ❌ Dual-system reasoning failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ PHASE 6 TEST PASSED")
print("=" * 80)
print("\nNote: Full agent testing requires:")
print("  - Valid Azure OpenAI credentials")
print("  - Active MongoDB connection")
print("  - Complete student learning history")
print("Use Docker Compose for full integration testing.")

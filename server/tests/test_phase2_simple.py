"""
Simple Phase 2 Test: Curriculum Generation
===========================================
Test curriculum adapter and generation without streaming dependencies.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 80)
print("PHASE 2 TEST: CURRICULUM GENERATION")
print("=" * 80)

print("\n1. Testing curriculum adapter import...")
try:
    from agent.curriculum_adapter import CurriculumAdapter
    print("   ✅ CurriculumAdapter imported")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n2. Testing curriculum adapter initialization...")
try:
    adapter = CurriculumAdapter()
    print("   ✅ Adapter initialized")
except Exception as e:
    print(f"   ❌ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n3. Testing curriculum adaptation (may take a moment)...")
try:
    # Create test student profile
    student_profile = {
        "student_id": "test_student",
        "learning_style": "visual",
        "pace": "moderate",
        "weak_areas": ["probability", "statistics"],
        "strong_areas": ["algebra"],
        "engagement_level": 0.8
    }
    
    # Test base curriculum
    base_curriculum = {
        "module_name": "Mathematics Basics",
        "topics": [
            {"name": "Algebra", "difficulty": "intermediate"},
            {"name": "Statistics", "difficulty": "beginner"}
        ]
    }
    
    print("   → Adapting curriculum for student profile...")
    adapted = adapter.adapt_curriculum(
        student_profile=student_profile,
        base_curriculum=base_curriculum
    )
    
    print(f"   ✅ Curriculum adapted")
    print(f"   Adapted for: {adapted['adapted_for']}")
    print(f"   Learning style: {adapted.get('learning_style', 'N/A')}")
    print(f"   Number of topics: {len(adapted.get('topics', []))}")
    
except Exception as e:
    print(f"   ❌ Adaptation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n4. Testing prerequisite check...")
try:
    prerequisites = ["Algebra", "Basic Calculus"]
    student_knowledge = ["Algebra"]
    
    print("   → Checking prerequisites...")
    missing = adapter.check_prerequisites(
        prerequisites=prerequisites,
        student_knowledge=student_knowledge
    )
    
    print(f"   ✅ Prerequisites checked")
    print(f"   Missing: {missing}")
    
except Exception as e:
    print(f"   ❌ Prerequisite check failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n5. Testing difficulty adjustment...")
try:
    print("   → Adjusting difficulty based on performance...")
    
    performance = {
        "score": 0.6,  # 60%
        "time_taken": 300
    }
    
    adjusted_difficulty = adapter.adjust_difficulty(
        current_difficulty="intermediate",
        performance=performance
    )
    
    print(f"   ✅ Difficulty adjusted: intermediate → {adjusted_difficulty}")
    
except Exception as e:
    print(f"   ❌ Difficulty adjustment failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ PHASE 2 TEST PASSED")
print("=" * 80)

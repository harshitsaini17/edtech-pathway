"""
Simple Phase 4 Test: Assessment System
=======================================
Test quiz generation and analysis without database dependencies.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 80)
print("PHASE 4 TEST: ASSESSMENT SYSTEM")
print("=" * 80)

print("\n1. Testing quiz generator import...")
try:
    from assessment.adaptive_quiz_generator import AdaptiveQuizGenerator
    print("   ✅ AdaptiveQuizGenerator imported")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n2. Testing quiz analyzer import...")
try:
    from assessment.quiz_analyzer import QuizAnalyzer
    print("   ✅ QuizAnalyzer imported")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n3. Testing quiz generator initialization...")
try:
    generator = AdaptiveQuizGenerator()
    print("   ✅ Generator initialized")
    print(f"   Vector store: {generator.vector_store is not None}")
except Exception as e:
    print(f"   ❌ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n4. Testing quiz generation (may take a moment)...")
try:
    print("   → Generating quiz with 2 questions...")
    quiz = generator.generate_quiz(
        module_name="Test_Module",
        num_questions=2
    )
    print(f"   ✅ Quiz generated: {quiz['quiz_id']}")
    print(f"   Number of questions: {len(quiz['questions'])}")
    
    if quiz['questions']:
        q = quiz['questions'][0]
        print(f"   First question type: {q['type']}")
        print(f"   First question text (truncated): {q['question'][:100]}...")
    
except Exception as e:
    print(f"   ❌ Generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n5. Testing quiz analyzer...")
try:
    analyzer = QuizAnalyzer()
    print("   ✅ Analyzer initialized")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

print("\n6. Testing quiz analysis...")
try:
    # Create test answers
    test_answers = {}
    for q in quiz['questions']:
        test_answers[q['id']] = "Test answer for evaluation"
    
    print("   → Analyzing quiz submission...")
    analysis = analyzer.analyze_quiz_submission(
        quiz_data=quiz,
        student_answers=test_answers,
        student_id="test_student"
    )
    
    print(f"   ✅ Analysis complete")
    print(f"   Score: {analysis['overall_metrics']['score']:.1f}/{analysis['overall_metrics']['max_score']}")
    print(f"   Percentage: {analysis['overall_metrics']['percentage']:.1f}%")
    print(f"   Weak areas: {len(analysis['weak_areas'])}")
    
except Exception as e:
    print(f"   ❌ Analysis failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ PHASE 4 TEST PASSED")
print("=" * 80)

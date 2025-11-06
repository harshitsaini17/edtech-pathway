"""



LearnPro Demo Script
====================
End-to-end demonstration of the adaptive learning system.
Shows the complete workflow from PDF ingestion to adaptive curriculum.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

import time
from datetime import datetime
import json


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_step(step_num, description):
    """Print step description"""
    print(f"\n{'─' * 80}")
    print(f"STEP {step_num}: {description}")
    print('─' * 80)


def demo_phase1_knowledge_base():
    """Demo Phase 1: Knowledge Base Ingestion"""
    print_step(1, "KNOWLEDGE BASE INGESTION")
    
    from server.db.vector_store import get_vector_store
    
    print("\n📚 Initializing vector store...")
    vector_store = get_vector_store()
    
    print("\n📄 Adding sample educational content...")
    sample_topics = [
        {
            "topic_id": "ml_intro_1",
            "title": "Introduction to Machine Learning",
            "content": """
            Machine Learning is a subset of Artificial Intelligence that enables systems to learn 
            and improve from experience without being explicitly programmed. It focuses on developing 
            computer programs that can access data and use it to learn for themselves.
            
            Key concepts:
            - Supervised Learning: Learning with labeled data
            - Unsupervised Learning: Finding patterns in unlabeled data
            - Reinforcement Learning: Learning through trial and error
            """,
            "metadata": {"module": "ML_Basics", "difficulty": "beginner"}
        },
        {
            "topic_id": "ml_supervised_1",
            "title": "Supervised Learning",
            "content": """
            Supervised learning is a type of machine learning where the algorithm learns from labeled 
            training data. The algorithm makes predictions or classifications based on input data and 
            is corrected when those predictions are wrong.
            
            Common algorithms:
            - Linear Regression
            - Logistic Regression
            - Decision Trees
            - Support Vector Machines (SVM)
            - Neural Networks
            """,
            "metadata": {"module": "ML_Basics", "difficulty": "intermediate"}
        },
        {
            "topic_id": "ml_neural_1",
            "title": "Neural Networks",
            "content": """
            Neural Networks are computing systems inspired by biological neural networks. They consist 
            of interconnected nodes (neurons) organized in layers. Each connection has a weight that 
            adjusts as learning proceeds.
            
            Architecture:
            - Input Layer: Receives input features
            - Hidden Layers: Process information
            - Output Layer: Produces final predictions
            
            The network learns by adjusting weights through backpropagation.
            """,
            "metadata": {"module": "Deep_Learning", "difficulty": "advanced"}
        }
    ]
    
    vector_store.add_topics(sample_topics)
    print(f"   ✅ Added {len(sample_topics)} topics to vector store")
    
    print("\n🔍 Testing semantic search...")
    results = vector_store.search_topics("What is supervised machine learning?", n_results=2)
    print(f"   Found {len(results['documents'][0])} relevant topics:")
    for i, doc in enumerate(results['documents'][0][:2], 1):
        print(f"   {i}. {doc[:100]}...")
    
    print("\n✅ Phase 1 Complete: Knowledge base populated")


def demo_phase2_student_enrollment():
    """Demo Phase 2: Student Enrollment"""
    print_step(2, "STUDENT ENROLLMENT")
    
    from server.db.student_profile import StudentProfileManager, StudentProfile
    
    print("\n👤 Creating student profile...")
    profile_manager = StudentProfileManager()
    
    student = StudentProfile(
        student_id="demo_student_001",
        name="Alice Johnson",
        email="alice@example.com",
        current_module="ML_Basics"
    )
    
    profile_manager.create_profile(student)
    print(f"   ✅ Created profile for {student.name}")
    print(f"   📧 Email: {student.email}")
    print(f"   📚 Starting module: {student.current_module}")
    
    print("\n✅ Phase 2 Complete: Student enrolled")
    return student.student_id


def demo_phase3_initial_assessment(student_id):
    """Demo Phase 3: Initial Assessment"""
    print_step(3, "INITIAL ASSESSMENT")
    
    from server.assessment.adaptive_quiz_generator import AdaptiveQuizGenerator
    from server.assessment.quiz_analyzer import QuizAnalyzer
    from server.db.student_profile import StudentProfileManager
    
    print(f"\n📝 Generating initial quiz for {student_id}...")
    generator = AdaptiveQuizGenerator()
    
    quiz = generator.generate_quiz(
        module_name="ML_Basics",
        num_questions=5
    )
    
    print(f"   ✅ Generated quiz: {quiz['quiz_id']}")
    print(f"   📊 Questions: {len(quiz['questions'])}")
    
    print("\n🎯 Simulating quiz submission...")
    # Simulate student answers (some correct, some weak)
    simulated_answers = {}
    for i, q in enumerate(quiz['questions']):
        if i < 3:  # First 3 correct
            simulated_answers[q['id']] = "Correct answer"
        else:  # Last 2 incorrect (showing weakness)
            simulated_answers[q['id']] = "Incorrect answer"
    
    print("\n📊 Analyzing results...")
    analyzer = QuizAnalyzer()
    
    analysis = analyzer.analyze_quiz_submission(
        quiz_data=quiz,
        student_answers=simulated_answers,
        student_id=student_id
    )
    
    print(f"   Score: {analysis['overall_metrics']['score']:.1f}/{analysis['overall_metrics']['max_score']}")
    print(f"   Percentage: {analysis['overall_metrics']['percentage']:.1f}%")
    print(f"   Correct answers: {analysis['overall_metrics']['correct_answers']}/{analysis['overall_metrics']['total_questions']}")
    
    if analysis['weak_areas']:
        print(f"   ⚠️ Weak areas detected: {', '.join(analysis['weak_areas'])}")
    
    # Update student profile
    profile_manager = StudentProfileManager()
    profile_manager.add_quiz_attempt(
        student_id=student_id,
        module_name="ML_Basics",
        quiz_id=quiz['quiz_id'],
        score=analysis['overall_metrics']['percentage'],
        max_score=100.0
    )
    
    print("\n✅ Phase 3 Complete: Initial assessment done")
    return analysis


def demo_phase4_curriculum_adaptation(student_id, analysis):
    """Demo Phase 4: Curriculum Adaptation"""
    print_step(4, "CURRICULUM ADAPTATION")
    
    from server.agent.curriculum_adapter import CurriculumAdapter
    
    print(f"\n🎯 Analyzing performance for {student_id}...")
    adapter = CurriculumAdapter()
    
    # Prepare performance data
    performance_data = {
        "average_score": analysis['overall_metrics']['percentage'],
        "weak_topics": analysis['weak_areas'],
        "struggle_count": len(analysis['weak_areas']),
        "performance_trend": "initial_assessment",
        "total_quizzes": 1
    }
    
    current_curriculum = {
        "topics": [
            "Introduction to ML",
            "Supervised Learning",
            "Unsupervised Learning",
            "Neural Networks",
            "Deep Learning"
        ],
        "difficulty": "intermediate"
    }
    
    print("\n🔄 Making adaptation decision...")
    decision = adapter.make_adaptation_decision(
        student_id=student_id,
        module_name="ML_Basics",
        performance_data=performance_data,
        current_curriculum=current_curriculum
    )
    
    print(f"   Decision type: {decision.decision_type}")
    print(f"   Priority: {decision.priority}")
    print(f"   Reasoning: {decision.reasoning}")
    print(f"   Actions planned: {len(decision.actions)}")
    
    for i, action in enumerate(decision.actions, 1):
        print(f"   {i}. {action['action']}")
    
    # Apply adaptation
    print("\n⚙️ Applying curriculum adaptations...")
    updated_curriculum = adapter.apply_adaptation(decision, current_curriculum)
    
    print(f"   ✅ Curriculum adapted")
    print(f"   New difficulty: {updated_curriculum.get('difficulty', 'N/A')}")
    
    if "remedial_content" in updated_curriculum:
        print(f"   💉 Remedial content items: {len(updated_curriculum['remedial_content'])}")
    
    print("\n✅ Phase 4 Complete: Curriculum adapted to student needs")


def demo_phase5_agent_orchestration(student_id):
    """Demo Phase 5: Agent Orchestration"""
    print_step(5, "AGENT ORCHESTRATION")
    
    from server.agent.learning_agent_orchestrator import LearningAgentOrchestrator
    
    print(f"\n🤖 Initializing learning agent for {student_id}...")
    orchestrator = LearningAgentOrchestrator()
    
    print("\n🎯 Agent making decision...")
    decision = orchestrator.make_decision(student_id)
    
    print(f"   Current state: {decision.current_state.value}")
    print(f"   Next state: {decision.next_state.value}")
    print(f"   Recommended action: {decision.action}")
    print(f"   Reasoning: {decision.reasoning}")
    
    print("\n▶️ Executing action...")
    result = orchestrator.execute_action(decision)
    
    print(f"   Status: {'✅ Success' if result['success'] else '❌ Failed'}")
    print(f"   Message: {result['message']}")
    
    print("\n✅ Phase 5 Complete: Agent orchestrating learning path")


def demo_phase6_realtime_monitoring():
    """Demo Phase 6: Real-time Monitoring"""
    print_step(6, "REAL-TIME MONITORING")
    
    from server.events.event_stream import EventStreamHandler
    from server.cache.cache_manager import get_cache_manager
    
    print("\n📊 Initializing monitoring systems...")
    
    # Event stream
    handler = EventStreamHandler(buffer_size=1000, batch_size=10)
    
    print("\n📈 Event Stream Status:")
    stats = handler.get_stats()
    print(f"   Buffer size: {stats['buffer']['current_size']}/{stats['buffer']['max_size']}")
    print(f"   Total events: {stats['buffer']['total_events']}")
    
    # Cache stats
    cache_manager = get_cache_manager()
    
    try:
        cache_stats = cache_manager.get_stats()
        print(f"\n💾 Cache Status:")
        print(f"   Total keys: {cache_stats.get('total_keys', 0)}")
        print(f"   Memory used: {cache_stats.get('memory_used_mb', 0):.2f} MB")
    except:
        print(f"\n💾 Cache Status: Not connected (expected in demo)")
    
    print("\n✅ Phase 6 Complete: Monitoring systems active")


def main():
    """Run complete demo"""
    print_header("🎓 LEARNPRO ADAPTIVE LEARNING SYSTEM - COMPLETE DEMO")
    
    print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nThis demo showcases the end-to-end adaptive learning workflow:")
    print("1. Knowledge base ingestion with vector search")
    print("2. Student enrollment and profile creation")
    print("3. Initial assessment with quiz generation")
    print("4. Real-time curriculum adaptation")
    print("5. AI agent orchestration")
    print("6. Monitoring and analytics")
    
    input("\nPress Enter to start the demo...")
    
    try:
        # Phase 1: Knowledge Base
        demo_phase1_knowledge_base()
        time.sleep(2)
        
        # Phase 2: Student Enrollment
        student_id = demo_phase2_student_enrollment()
        time.sleep(2)
        
        # Phase 3: Initial Assessment
        analysis = demo_phase3_initial_assessment(student_id)
        time.sleep(2)
        
        # Phase 4: Curriculum Adaptation
        demo_phase4_curriculum_adaptation(student_id, analysis)
        time.sleep(2)
        
        # Phase 5: Agent Orchestration
        demo_phase5_agent_orchestration(student_id)
        time.sleep(2)
        
        # Phase 6: Real-time Monitoring
        demo_phase6_realtime_monitoring()
        
        # Summary
        print_header("🎉 DEMO COMPLETE!")
        
        print("\n✅ Successfully demonstrated:")
        print("   • Knowledge base with semantic search")
        print("   • Student profile management")
        print("   • Adaptive quiz generation and analysis")
        print("   • Real-time curriculum adaptation")
        print("   • AI agent decision making")
        print("   • Event streaming and monitoring")
        
        print("\n📊 Next Steps:")
        print("   1. Start the API: uvicorn api.main:app --reload")
        print("   2. Launch dashboard: streamlit run monitoring/dashboard.py")
        print("   3. Try the REST API endpoints at http://localhost:8000/docs")
        print("   4. View metrics at http://localhost:8501")
        
        print(f"\n🎓 LearnPro - Adaptive Learning Powered by AI")
        print(f"Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

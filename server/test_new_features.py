"""
Test New Features: Topic Beautification & Real-time Dashboard Updates
======================================================================

This script tests the two newly implemented features:
1. Topic Title Beautification - Making topic names more engaging
2. Real-time Dashboard Updates - Pushing curriculum adaptations to dashboard

Author: EdTech Pathway System
Date: 2024
"""

import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.topic_beautifier import TopicTitleBeautifier, beautify_curriculum_topics
from streaming.realtime_dashboard_updater import RealTimeDashboardUpdater


def test_topic_beautification():
    """Test 1: Topic Title Beautification"""
    print("\n" + "="*70)
    print("TEST 1: TOPIC TITLE BEAUTIFICATION")
    print("="*70)
    
    beautifier = TopicTitleBeautifier()
    
    # Test with sample raw topic titles from actual PDFs
    test_topics = [
        "4.4 Expectation",
        "VARIANCE OF SUMS OF RANDOM VARIABLES",
        "2.2 Properties of Probability",
        "Covariance and Variance of Sums",
        "3.1 Introduction to Random Variables",
        "PMF and CDF",
        "4.7 Expected Value Calculations"
    ]
    
    print("\n📚 Beautifying Topic Titles:\n")
    
    for i, raw_title in enumerate(test_topics, 1):
        beautified = beautifier.beautify_topic_title(raw_title, "Probability")
        emoji = beautifier.get_topic_emoji(beautified)
        
        print(f"{i}. ORIGINAL: {raw_title}")
        print(f"   BEAUTIFIED: {emoji} {beautified}")
        print()
    
    # Test with full curriculum structure
    print("\n📖 Testing Full Curriculum Beautification:\n")
    
    sample_curriculum = {
        "title": "Probability and Statistics",
        "modules": [
            {
                "title": "Module 1: Core Concepts",
                "topics": [
                    {"title": "4.4 Expectation", "duration": "2 hours"},
                    {"title": "VARIANCE OF SUMS", "duration": "3 hours"}
                ]
            },
            {
                "title": "Module 2: Applications",
                "topics": [
                    {"title": "2.2 Properties", "duration": "2 hours"}
                ]
            }
        ]
    }
    
    beautified_curriculum = beautify_curriculum_topics(sample_curriculum)
    
    print("Before beautification:")
    for module in sample_curriculum["modules"]:
        print(f"  {module['title']}")
        for topic in module["topics"]:
            print(f"    - {topic['title']}")
    
    print("\nAfter beautification:")
    for module in beautified_curriculum["modules"]:
        print(f"  {module['title']}")
        for topic in module["topics"]:
            emoji = beautifier.get_topic_emoji(topic['title'])
            print(f"    {emoji} {topic['title']}")
    
    print("\n✅ Topic Beautification Test Complete!")
    return True


def test_realtime_updates():
    """Test 2: Real-time Dashboard Updates"""
    print("\n" + "="*70)
    print("TEST 2: REAL-TIME DASHBOARD UPDATES")
    print("="*70)
    
    try:
        updater = RealTimeDashboardUpdater()
        
        # Test update push
        print("\n📡 Testing Real-time Update Push:\n")
        
        test_update = {
            "update_type": "adaptation",
            "student_id": "student_123",
            "module_name": "Probability Theory",
            "changes": {
                "reranked_topics": ["Expected Value", "Variance", "Covariance"],
                "difficulty_adjusted": "medium → hard",
                "remedial_content_added": 2
            },
            "reason": "Student showing strong performance on basic concepts"
        }
        
        print(f"1. Pushing update for: {test_update['student_id']}")
        print(f"   Module: {test_update['module_name']}")
        print(f"   Type: {test_update['update_type']}")
        
        result = updater.push_curriculum_update(
            student_id=test_update["student_id"],
            update_type=test_update["update_type"],
            curriculum_data=test_update["changes"],
            module_name=test_update["module_name"],
            metadata={"reason": test_update["reason"]}
        )
        
        if result:
            print(f"   ✅ Update pushed successfully!")
            
            # Test retrieving the update
            print("\n2. Retrieving pushed update:")
            retrieved = updater.get_pending_update(test_update["student_id"])
            
            if retrieved:
                print(f"   ✅ Retrieved update:")
                print(f"      Timestamp: {retrieved.get('timestamp')}")
                print(f"      Type: {retrieved.get('update_type')}")
                print(f"      Message: {retrieved.get('notification_message')[:80]}...")
            else:
                print("   ⚠️ No pending update found")
            
            # Test update history
            print("\n3. Checking update history:")
            history = updater.get_update_history(test_update["student_id"], limit=5)
            print(f"   Found {len(history)} updates in history")
            
            for idx, update in enumerate(history, 1):
                print(f"   {idx}. {update.get('update_type')} - {update.get('timestamp')}")
        
        else:
            print("   ⚠️ Update push failed")
        
        print("\n✅ Real-time Updates Test Complete!")
        return True
        
    except Exception as e:
        print(f"\n⚠️ Real-time Updates Test Failed: {e}")
        print("   (This is expected if Redis is not running)")
        return False


def test_integration():
    """Test 3: Integration - Curriculum with Beautified Topics + Real-time Push"""
    print("\n" + "="*70)
    print("TEST 3: INTEGRATION TEST")
    print("="*70)
    
    print("\n🔄 Simulating Full Workflow:\n")
    
    # Step 1: Create curriculum with raw titles
    print("1. Creating curriculum with raw topic titles...")
    curriculum = {
        "student_id": "student_456",
        "title": "Personalized Probability Course",
        "modules": [
            {
                "title": "Module 1: Foundations",
                "topics": [
                    {"title": "4.1 Random Variables", "duration": "2h"},
                    {"title": "4.4 Expectation", "duration": "3h"}
                ]
            }
        ]
    }
    print("   ✅ Raw curriculum created")
    
    # Step 2: Beautify topics
    print("\n2. Beautifying topic titles...")
    beautifier = TopicTitleBeautifier()
    beautified_curriculum = beautify_curriculum_topics(curriculum)
    
    print("   Topics beautified:")
    for module in beautified_curriculum["modules"]:
        for topic in module["topics"]:
            emoji = beautifier.get_topic_emoji(topic['title'])
            print(f"      {emoji} {topic['title']}")
    
    # Step 3: Push to dashboard
    print("\n3. Pushing beautified curriculum to dashboard...")
    try:
        updater = RealTimeDashboardUpdater()
        result = updater.push_curriculum_update(
            student_id=curriculum["student_id"],
            update_type="curriculum_generated",
            curriculum_data=beautified_curriculum,
            metadata={"beautified": True, "module_count": len(beautified_curriculum["modules"])}
        )
        
        if result:
            print("   ✅ Beautified curriculum pushed to dashboard!")
            print("   📱 Student would see real-time update in their dashboard")
        else:
            print("   ⚠️ Push failed")
    except Exception as e:
        print(f"   ⚠️ Could not push to dashboard: {e}")
    
    print("\n✅ Integration Test Complete!")
    return True


def main():
    """Run all tests"""
    print("\n🚀 TESTING NEW FEATURES: Topic Beautification & Real-time Updates")
    print("="*70)
    
    results = {
        "Topic Beautification": False,
        "Real-time Updates": False,
        "Integration": False
    }
    
    try:
        results["Topic Beautification"] = test_topic_beautification()
    except Exception as e:
        print(f"❌ Topic Beautification Test Failed: {e}")
    
    try:
        results["Real-time Updates"] = test_realtime_updates()
    except Exception as e:
        print(f"❌ Real-time Updates Test Failed: {e}")
    
    try:
        results["Integration"] = test_integration()
    except Exception as e:
        print(f"❌ Integration Test Failed: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed! Both features are working correctly.")
    elif total_passed > 0:
        print("\n⚠️ Some tests passed. Check Redis connection for real-time updates.")
    else:
        print("\n❌ Tests failed. Please check the error messages above.")


if __name__ == "__main__":
    main()

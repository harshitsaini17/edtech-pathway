"""
Quiz Analyzer
=============
Analyzes student quiz responses, calculates performance metrics,
detects weak areas, and computes mastery scores per topic.
"""

import json
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics

from config.settings import settings


@dataclass
class QuizAttempt:
    """Represents a student's quiz attempt"""
    attempt_id: str
    student_id: str
    quiz_id: str
    module_name: str
    started_at: str
    completed_at: str
    time_taken_seconds: int
    score: float
    max_score: float
    percentage: float
    answers: List[Dict[str, Any]]
    analysis: Dict[str, Any]


class QuizAnalyzer:
    """
    Analyzes quiz responses and generates performance insights
    """
    
    def __init__(self):
        """Initialize the quiz analyzer"""
        print("✅ Quiz Analyzer initialized")
    
    def analyze_quiz_submission(
        self,
        student_id: str,
        quiz_data: Dict[str, Any],
        student_answers: Dict[str, Any]
    ) -> QuizAttempt:
        """
        Analyze a student's quiz submission
        
        Args:
            student_id: Student identifier
            quiz_data: Original quiz data with correct answers
            student_answers: Student's submitted answers
            
        Returns:
            QuizAttempt with full analysis
        """
        print(f"\n📊 Analyzing quiz for student: {student_id}")
        
        quiz_id = quiz_data['quiz_id']
        module_name = quiz_data['module_name']
        questions = quiz_data['questions']
        
        # Extract timing info
        started_at = student_answers.get('started_at', datetime.now().isoformat())
        completed_at = student_answers.get('completed_at', datetime.now().isoformat())
        time_taken = student_answers.get('time_taken_seconds', 0)
        
        # Analyze each answer
        analyzed_answers = []
        total_score = 0
        max_score = 0
        
        topic_performance = defaultdict(lambda: {'correct': 0, 'total': 0, 'questions': []})
        difficulty_performance = defaultdict(lambda: {'correct': 0, 'total': 0})
        question_type_performance = defaultdict(lambda: {'correct': 0, 'total': 0})
        
        for i, question in enumerate(questions):
            question_id = question['id']
            student_answer = student_answers.get('answers', {}).get(question_id, '')
            
            # Evaluate answer
            is_correct, points_earned, feedback = self._evaluate_answer(
                question, student_answer
            )
            
            # Update scores
            question_points = question.get('points', 1)
            max_score += question_points
            if is_correct:
                total_score += points_earned
            
            # Track performance by dimensions
            topic = question.get('topic', 'Unknown')
            difficulty = question.get('difficulty', 'medium')
            question_type = question.get('question_type', 'mcq')
            
            topic_performance[topic]['total'] += 1
            topic_performance[topic]['questions'].append(question_id)
            if is_correct:
                topic_performance[topic]['correct'] += 1
            
            difficulty_performance[difficulty]['total'] += 1
            if is_correct:
                difficulty_performance[difficulty]['correct'] += 1
            
            question_type_performance[question_type]['total'] += 1
            if is_correct:
                question_type_performance[question_type]['correct'] += 1
            
            # Store analyzed answer
            analyzed_answers.append({
                'question_id': question_id,
                'question': question['question'],
                'topic': topic,
                'difficulty': difficulty,
                'question_type': question_type,
                'student_answer': student_answer,
                'correct_answer': question.get('correct_answer'),
                'is_correct': is_correct,
                'points_earned': points_earned,
                'max_points': question_points,
                'feedback': feedback,
                'time_spent': student_answers.get('question_times', {}).get(question_id, 0)
            })
        
        # Calculate overall percentage
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        # Generate comprehensive analysis
        analysis = self._generate_analysis(
            analyzed_answers,
            topic_performance,
            difficulty_performance,
            question_type_performance,
            percentage
        )
        
        # Create attempt object
        attempt = QuizAttempt(
            attempt_id=self._generate_attempt_id(student_id, quiz_id),
            student_id=student_id,
            quiz_id=quiz_id,
            module_name=module_name,
            started_at=started_at,
            completed_at=completed_at,
            time_taken_seconds=time_taken,
            score=total_score,
            max_score=max_score,
            percentage=percentage,
            answers=analyzed_answers,
            analysis=analysis
        )
        
        # Save attempt
        self._save_attempt(attempt)
        
        print(f"✅ Analysis complete: {percentage:.1f}% ({total_score}/{max_score})")
        
        return attempt
    
    def _evaluate_answer(
        self,
        question: Dict[str, Any],
        student_answer: Any
    ) -> Tuple[bool, float, str]:
        """
        Evaluate a single answer
        
        Args:
            question: Question data with correct answer
            student_answer: Student's submitted answer
            
        Returns:
            Tuple of (is_correct, points_earned, feedback)
        """
        question_type = question.get('question_type', 'mcq')
        correct_answer = question.get('correct_answer')
        points = question.get('points', 1)
        
        if question_type == 'mcq':
            # MCQ: Exact match required
            is_correct = str(student_answer).strip().upper() == str(correct_answer).strip().upper()
            points_earned = points if is_correct else 0
            feedback = "Correct!" if is_correct else f"Incorrect. The correct answer is {correct_answer}."
            
        elif question_type == 'true_false':
            # True/False: Boolean match
            is_correct = bool(student_answer) == bool(correct_answer)
            points_earned = points if is_correct else 0
            feedback = "Correct!" if is_correct else f"Incorrect. The correct answer is {correct_answer}."
            
        elif question_type == 'short_answer':
            # Short answer: Keyword-based partial credit
            is_correct, points_earned, feedback = self._evaluate_short_answer(
                correct_answer, student_answer, points
            )
            
        elif question_type == 'numerical':
            # Numerical: Within tolerance
            is_correct, points_earned, feedback = self._evaluate_numerical(
                correct_answer, student_answer, points
            )
            
        elif question_type == 'code':
            # Code: Requires manual review or test cases
            # For now, give partial credit if answer is provided
            is_correct = len(str(student_answer).strip()) > 10
            points_earned = points * 0.5 if is_correct else 0
            feedback = "Partial credit. Code requires review."
            
        else:
            is_correct = False
            points_earned = 0
            feedback = "Unknown question type."
        
        return is_correct, points_earned, feedback
    
    def _evaluate_short_answer(
        self,
        correct_answer: str,
        student_answer: str,
        max_points: float
    ) -> Tuple[bool, float, str]:
        """Evaluate short answer with keyword matching"""
        if not student_answer or not correct_answer:
            return False, 0, "No answer provided."
        
        # Extract keywords from correct answer (simple approach)
        keywords = set(correct_answer.lower().split())
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        keywords = keywords - stop_words
        
        # Check keyword presence
        student_words = set(student_answer.lower().split())
        matched_keywords = keywords.intersection(student_words)
        
        if len(keywords) == 0:
            return True, max_points, "Answer accepted."
        
        match_ratio = len(matched_keywords) / len(keywords)
        
        if match_ratio >= 0.8:
            return True, max_points, "Excellent answer!"
        elif match_ratio >= 0.5:
            points_earned = max_points * 0.7
            return False, points_earned, f"Partial credit. Key concepts present."
        elif match_ratio >= 0.3:
            points_earned = max_points * 0.4
            return False, points_earned, f"Some correct elements. Missing key concepts."
        else:
            return False, 0, "Answer lacks key concepts."
    
    def _evaluate_numerical(
        self,
        correct_answer: str,
        student_answer: str,
        max_points: float
    ) -> Tuple[bool, float, str]:
        """Evaluate numerical answer with tolerance"""
        try:
            # Extract numerical value from strings
            import re
            correct_num = float(re.findall(r'-?\d+\.?\d*', str(correct_answer))[0])
            student_num = float(re.findall(r'-?\d+\.?\d*', str(student_answer))[0])
            
            # Allow 1% tolerance
            tolerance = abs(correct_num * 0.01)
            diff = abs(correct_num - student_num)
            
            if diff <= tolerance:
                return True, max_points, "Correct!"
            elif diff <= tolerance * 3:
                return False, max_points * 0.5, f"Close. Correct answer: {correct_answer}"
            else:
                return False, 0, f"Incorrect. Correct answer: {correct_answer}"
                
        except (IndexError, ValueError):
            return False, 0, "Invalid numerical format."
    
    def _generate_analysis(
        self,
        analyzed_answers: List[Dict],
        topic_performance: Dict,
        difficulty_performance: Dict,
        question_type_performance: Dict,
        overall_percentage: float
    ) -> Dict[str, Any]:
        """Generate comprehensive performance analysis"""
        
        # Identify weak areas (topics with < 60% correct)
        weak_topics = []
        strong_topics = []
        
        for topic, perf in topic_performance.items():
            percentage = (perf['correct'] / perf['total'] * 100) if perf['total'] > 0 else 0
            
            topic_analysis = {
                'topic': topic,
                'correct': perf['correct'],
                'total': perf['total'],
                'percentage': percentage,
                'mastery_score': percentage / 100
            }
            
            if percentage < settings.WEAK_AREA_THRESHOLD * 100:
                weak_topics.append(topic_analysis)
            elif percentage >= settings.MASTERY_THRESHOLD * 100:
                strong_topics.append(topic_analysis)
        
        # Sort by performance
        weak_topics.sort(key=lambda x: x['percentage'])
        strong_topics.sort(key=lambda x: x['percentage'], reverse=True)
        
        # Calculate struggle indicators
        struggle_questions = [
            ans for ans in analyzed_answers
            if not ans['is_correct'] and ans['time_spent'] > 120  # > 2 minutes
        ]
        
        # Difficulty analysis
        difficulty_breakdown = {}
        for diff, perf in difficulty_performance.items():
            percentage = (perf['correct'] / perf['total'] * 100) if perf['total'] > 0 else 0
            difficulty_breakdown[diff] = {
                'correct': perf['correct'],
                'total': perf['total'],
                'percentage': percentage
            }
        
        # Question type analysis
        type_breakdown = {}
        for qtype, perf in question_type_performance.items():
            percentage = (perf['correct'] / perf['total'] * 100) if perf['total'] > 0 else 0
            type_breakdown[qtype] = {
                'correct': perf['correct'],
                'total': perf['total'],
                'percentage': percentage
            }
        
        # Overall mastery level
        if overall_percentage >= settings.MASTERY_THRESHOLD * 100:
            mastery_level = "mastered"
            recommendation = "Excellent! Ready to proceed to next module."
        elif overall_percentage >= settings.WEAK_AREA_THRESHOLD * 100:
            mastery_level = "proficient"
            recommendation = "Good progress. Review weak areas before proceeding."
        else:
            mastery_level = "needs_review"
            recommendation = "Additional practice recommended before proceeding."
        
        return {
            'overall_percentage': overall_percentage,
            'mastery_level': mastery_level,
            'recommendation': recommendation,
            'weak_topics': weak_topics,
            'strong_topics': strong_topics,
            'struggle_indicators': {
                'count': len(struggle_questions),
                'questions': [q['question_id'] for q in struggle_questions]
            },
            'difficulty_breakdown': difficulty_breakdown,
            'question_type_breakdown': type_breakdown,
            'topic_mastery_scores': {
                topic: perf['correct'] / perf['total'] if perf['total'] > 0 else 0
                for topic, perf in topic_performance.items()
            }
        }
    
    def _generate_attempt_id(self, student_id: str, quiz_id: str) -> str:
        """Generate unique attempt ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"attempt_{student_id}_{quiz_id}_{timestamp}"
    
    def _save_attempt(self, attempt: QuizAttempt):
        """Save quiz attempt to file"""
        output_dir = f"output/quiz_attempts/{attempt.student_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{output_dir}/{attempt.attempt_id}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(asdict(attempt), f, indent=2, ensure_ascii=False)
        
        print(f"💾 Attempt saved: {filename}")
    
    def get_student_performance_history(
        self,
        student_id: str,
        module_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get performance history for a student
        
        Args:
            student_id: Student identifier
            module_name: Optional module filter
            
        Returns:
            Performance history and trends
        """
        attempts_dir = f"output/quiz_attempts/{student_id}"
        
        if not os.path.exists(attempts_dir):
            return {
                'student_id': student_id,
                'total_attempts': 0,
                'attempts': []
            }
        
        attempts = []
        for filename in os.listdir(attempts_dir):
            if filename.endswith('.json'):
                with open(os.path.join(attempts_dir, filename), 'r') as f:
                    attempt_data = json.load(f)
                    
                    # Filter by module if specified
                    if module_name and attempt_data.get('module_name') != module_name:
                        continue
                    
                    attempts.append(attempt_data)
        
        # Sort by date
        attempts.sort(key=lambda x: x.get('completed_at', ''), reverse=True)
        
        # Calculate trends
        if attempts:
            recent_scores = [a['percentage'] for a in attempts[:5]]
            average_recent = statistics.mean(recent_scores) if recent_scores else 0
            trend = "improving" if len(recent_scores) >= 2 and recent_scores[0] > recent_scores[-1] else "stable"
        else:
            average_recent = 0
            trend = "no_data"
        
        return {
            'student_id': student_id,
            'total_attempts': len(attempts),
            'attempts': attempts,
            'recent_average': average_recent,
            'trend': trend
        }


if __name__ == "__main__":
    # Test the quiz analyzer
    print("🧪 Testing Quiz Analyzer...")
    
    analyzer = QuizAnalyzer()
    
    # Sample quiz data
    quiz_data = {
        'quiz_id': 'quiz_test_123',
        'module_name': 'Introduction to Probability',
        'questions': [
            {
                'id': 'q1',
                'question': 'What is a random variable?',
                'topic': 'Random Variables',
                'difficulty': 'easy',
                'question_type': 'short_answer',
                'correct_answer': 'A variable whose value depends on outcomes of a random phenomenon',
                'points': 2
            },
            {
                'id': 'q2',
                'question': 'The expected value is the average of all possible values.',
                'topic': 'Expected Value',
                'difficulty': 'easy',
                'question_type': 'true_false',
                'correct_answer': True,
                'points': 1
            }
        ]
    }
    
    # Sample student answers
    student_answers = {
        'started_at': datetime.now().isoformat(),
        'completed_at': datetime.now().isoformat(),
        'time_taken_seconds': 180,
        'answers': {
            'q1': 'A variable that depends on random outcomes',
            'q2': True
        },
        'question_times': {
            'q1': 120,
            'q2': 60
        }
    }
    
    # Analyze
    attempt = analyzer.analyze_quiz_submission(
        student_id='student_test_001',
        quiz_data=quiz_data,
        student_answers=student_answers
    )
    
    print(f"\n📊 Analysis Results:")
    print(f"Score: {attempt.score}/{attempt.max_score} ({attempt.percentage:.1f}%)")
    print(f"Mastery Level: {attempt.analysis['mastery_level']}")
    print(f"Weak Topics: {[t['topic'] for t in attempt.analysis['weak_topics']]}")
    
    print("\n✅ Quiz analyzer test complete!")

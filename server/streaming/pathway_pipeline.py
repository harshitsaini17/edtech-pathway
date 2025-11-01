"""
Pathway Streaming Pipeline
===========================
Real-time event streaming and processing for adaptive learning.
Handles student interaction events and computes live performance metrics.
"""

import pathway as pw
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from config.settings import settings


class StudentEventSchema(pw.Schema):
    """Schema for student interaction events"""
    event_id: str
    student_id: str
    event_type: str  # quiz_submit, content_view, time_spent, click, struggle
    timestamp: int
    module_name: str
    topic_name: Optional[str]
    data: pw.Json  # Event-specific data


class QuizResultSchema(pw.Schema):
    """Schema for quiz submission events"""
    student_id: str
    quiz_id: str
    module_name: str
    timestamp: int
    score: float
    max_score: float
    percentage: float
    weak_topics: pw.Json
    time_taken_seconds: int


class PerformanceAggregateSchema(pw.Schema):
    """Schema for aggregated performance metrics"""
    student_id: str
    module_name: str
    total_quizzes: int
    average_score: float
    recent_scores: pw.Json
    weak_topics: pw.Json
    struggle_count: int
    total_time_spent: int
    last_activity: int
    performance_trend: str  # improving, declining, stable


class PathwayPipeline:
    """
    Pathway-based real-time streaming pipeline for adaptive learning
    """
    
    def __init__(self):
        """Initialize the Pathway pipeline"""
        self.input_table: Optional[pw.Table] = None
        self.quiz_results_table: Optional[pw.Table] = None
        self.aggregated_metrics: Optional[pw.Table] = None
        self.curriculum_updates: Optional[pw.Table] = None
        
        print("✅ Pathway Pipeline initialized")
    
    def setup_input_connectors(self, input_mode: str = "python"):
        """
        Setup input connectors for event streams
        
        Args:
            input_mode: 'python' for in-memory, 'kafka' for Kafka, 'csv' for file
        """
        if input_mode == "python":
            # Python connector for in-memory streaming (testing)
            self.input_table = pw.debug.table_from_markdown('''
            event_id | student_id | event_type | timestamp | module_name | topic_name | data
            e1       | s001       | content_view | 1000 | Module1 | Topic1 | {}
            ''', schema=StudentEventSchema)
            
        elif input_mode == "kafka":
            # Kafka connector for production
            self.input_table = pw.io.kafka.read(
                rdkafka_settings={
                    "bootstrap.servers": settings.PATHWAY_KAFKA_BOOTSTRAP_SERVERS,
                    "group.id": "learnpro-consumer",
                    "auto.offset.reset": "earliest"
                },
                topic="student-events",
                schema=StudentEventSchema,
                format="json"
            )
            
        elif input_mode == "csv":
            # CSV connector for batch processing/testing
            self.input_table = pw.io.csv.read(
                "./data/student_events.csv",
                schema=StudentEventSchema,
                mode="streaming"
            )
        
        print(f"✅ Input connector setup: {input_mode}")
        return self.input_table
    
    def filter_quiz_submissions(self, events_table: pw.Table) -> pw.Table:
        """
        Filter quiz submission events from all events
        
        Args:
            events_table: Table of all student events
            
        Returns:
            Table of quiz submissions only
        """
        quiz_events = events_table.filter(events_table.event_type == "quiz_submit")
        
        # Transform to quiz result schema
        quiz_results = quiz_events.select(
            student_id=quiz_events.student_id,
            quiz_id=pw.apply(lambda x: x.get("quiz_id", ""), quiz_events.data),
            module_name=quiz_events.module_name,
            timestamp=quiz_events.timestamp,
            score=pw.apply(lambda x: x.get("score", 0.0), quiz_events.data),
            max_score=pw.apply(lambda x: x.get("max_score", 1.0), quiz_events.data),
            percentage=pw.apply(lambda x: x.get("percentage", 0.0), quiz_events.data),
            weak_topics=pw.apply(lambda x: x.get("weak_topics", []), quiz_events.data),
            time_taken_seconds=pw.apply(lambda x: x.get("time_taken_seconds", 0), quiz_events.data)
        )
        
        return quiz_results
    
    def aggregate_student_performance(
        self,
        quiz_results: pw.Table,
        window_seconds: int = None
    ) -> pw.Table:
        """
        Aggregate student performance metrics using Pathway operations
        
        Args:
            quiz_results: Table of quiz submissions
            window_seconds: Time window for aggregation (None = all time)
            
        Returns:
            Table of aggregated metrics per student-module
        """
        window_seconds = window_seconds or settings.PATHWAY_WINDOW_SIZE
        
        # Group by student and module
        grouped = quiz_results.groupby(
            quiz_results.student_id,
            quiz_results.module_name
        ).reduce(
            student_id=quiz_results.student_id,
            module_name=quiz_results.module_name,
            total_quizzes=pw.reducers.count(),
            average_score=pw.reducers.avg(quiz_results.percentage),
            total_time_spent=pw.reducers.sum(quiz_results.time_taken_seconds),
            last_activity=pw.reducers.max(quiz_results.timestamp)
        )
        
        return grouped
    
    def calculate_performance_trends(
        self,
        aggregated_metrics: pw.Table,
        quiz_results: pw.Table
    ) -> pw.Table:
        """
        Calculate performance trends (improving, declining, stable)
        
        Args:
            aggregated_metrics: Aggregated performance metrics
            quiz_results: Raw quiz results
            
        Returns:
            Table with trend analysis
        """
        # Join to get recent scores
        # For each student-module, get last 5 quiz scores
        
        # This is a simplified version - in production, use windowed operations
        enhanced = aggregated_metrics.select(
            *pw.this,
            performance_trend=pw.apply(
                lambda avg: "stable" if avg > 60 else "needs_review",
                aggregated_metrics.average_score
            )
        )
        
        return enhanced
    
    def detect_struggle_indicators(
        self,
        events_table: pw.Table
    ) -> pw.Table:
        """
        Detect struggle indicators from events
        
        Args:
            events_table: All student events
            
        Returns:
            Table of struggle indicators
        """
        # Filter struggle events (incorrect attempts, long time on content)
        struggle_events = events_table.filter(
            events_table.event_type == "struggle"
        )
        
        # Count struggles per student-topic
        struggle_counts = struggle_events.groupby(
            struggle_events.student_id,
            struggle_events.module_name,
            struggle_events.topic_name
        ).reduce(
            student_id=struggle_events.student_id,
            module_name=struggle_events.module_name,
            topic_name=struggle_events.topic_name,
            struggle_count=pw.reducers.count(),
            total_time=pw.reducers.sum(
                pw.apply(lambda x: x.get("time_spent", 0), struggle_events.data)
            )
        )
        
        return struggle_counts
    
    def detect_anomalies(
        self,
        aggregated_metrics: pw.Table
    ) -> pw.Table:
        """
        Detect anomalies in student performance
        
        Args:
            aggregated_metrics: Aggregated metrics
            
        Returns:
            Table of anomalies
        """
        # Flag anomalies (e.g., sudden drops, excessive time)
        anomalies = aggregated_metrics.select(
            *pw.this,
            is_anomaly=pw.apply(
                lambda avg, time: (
                    avg < 40  # Sudden poor performance
                    or time > 3600 * 3  # More than 3 hours on module
                ),
                aggregated_metrics.average_score,
                aggregated_metrics.total_time_spent
            )
        )
        
        # Filter only anomalies
        return anomalies.filter(anomalies.is_anomaly)
    
    def join_metrics_with_weak_topics(
        self,
        aggregated_metrics: pw.Table,
        quiz_results: pw.Table
    ) -> pw.Table:
        """
        Join aggregated metrics with weak topic information
        
        Args:
            aggregated_metrics: Performance aggregates
            quiz_results: Quiz results with weak topics
            
        Returns:
            Enhanced metrics with weak topic tracking
        """
        # Get latest quiz result for each student-module
        latest_quiz = quiz_results.groupby(
            quiz_results.student_id,
            quiz_results.module_name
        ).reduce(
            student_id=quiz_results.student_id,
            module_name=quiz_results.module_name,
            weak_topics=pw.reducers.latest(quiz_results.weak_topics),
            recent_scores=pw.reducers.latest(quiz_results.percentage)
        )
        
        # Join with aggregated metrics
        enhanced = aggregated_metrics.join(
            latest_quiz,
            aggregated_metrics.student_id == latest_quiz.student_id,
            aggregated_metrics.module_name == latest_quiz.module_name
        ).select(
            *aggregated_metrics,
            weak_topics=latest_quiz.weak_topics,
            recent_scores=latest_quiz.recent_scores
        )
        
        return enhanced
    
    def setup_output_connectors(
        self,
        output_table: pw.Table,
        output_mode: str = "python"
    ):
        """
        Setup output connectors for processed metrics
        
        Args:
            output_table: Table to output
            output_mode: 'python' for callbacks, 'kafka' for Kafka, 'csv' for file
        """
        if output_mode == "python":
            # Python output for in-memory testing
            pw.io.null.write(output_table)
            
        elif output_mode == "kafka":
            # Kafka output for production
            pw.io.kafka.write(
                output_table,
                rdkafka_settings={
                    "bootstrap.servers": settings.PATHWAY_KAFKA_BOOTSTRAP_SERVERS
                },
                topic="curriculum-updates",
                format="json"
            )
            
        elif output_mode == "csv":
            # CSV output for debugging
            pw.io.csv.write(
                output_table,
                "./data/performance_metrics.csv"
            )
        
        print(f"✅ Output connector setup: {output_mode}")
    
    def build_full_pipeline(self, input_mode: str = "python", output_mode: str = "python"):
        """
        Build the complete streaming pipeline
        
        Args:
            input_mode: Input connector type
            output_mode: Output connector type
        """
        print("\n🚀 Building Pathway streaming pipeline...")
        
        # Step 1: Setup inputs
        events = self.setup_input_connectors(input_mode)
        
        # Step 2: Filter quiz submissions
        quiz_results = self.filter_quiz_submissions(events)
        
        # Step 3: Aggregate performance
        aggregated = self.aggregate_student_performance(quiz_results)
        
        # Step 4: Calculate trends
        with_trends = self.calculate_performance_trends(aggregated, quiz_results)
        
        # Step 5: Detect struggles
        struggles = self.detect_struggle_indicators(events)
        
        # Step 6: Join with weak topics
        enhanced = self.join_metrics_with_weak_topics(with_trends, quiz_results)
        
        # Step 7: Detect anomalies
        anomalies = self.detect_anomalies(enhanced)
        
        # Store results
        self.aggregated_metrics = enhanced
        self.curriculum_updates = anomalies
        
        # Step 8: Setup outputs
        self.setup_output_connectors(enhanced, output_mode)
        
        print("✅ Pipeline built successfully!")
        
        return enhanced
    
    def run(self):
        """Run the Pathway computation"""
        print("\n▶️ Starting Pathway computation...")
        pw.run()


class EventPublisher:
    """
    Helper class to publish events to the Pathway pipeline
    """
    
    def __init__(self):
        """Initialize event publisher"""
        self.events: List[Dict[str, Any]] = []
    
    def publish_quiz_submission(
        self,
        student_id: str,
        quiz_id: str,
        module_name: str,
        score: float,
        max_score: float,
        percentage: float,
        weak_topics: List[str],
        time_taken_seconds: int
    ):
        """
        Publish a quiz submission event
        
        Args:
            student_id: Student identifier
            quiz_id: Quiz identifier
            module_name: Module name
            score: Score achieved
            max_score: Maximum possible score
            percentage: Percentage score
            weak_topics: List of weak topics
            time_taken_seconds: Time taken
        """
        event = {
            "event_id": f"quiz_{student_id}_{datetime.now().timestamp()}",
            "student_id": student_id,
            "event_type": "quiz_submit",
            "timestamp": int(datetime.now().timestamp()),
            "module_name": module_name,
            "topic_name": None,
            "data": {
                "quiz_id": quiz_id,
                "score": score,
                "max_score": max_score,
                "percentage": percentage,
                "weak_topics": weak_topics,
                "time_taken_seconds": time_taken_seconds
            }
        }
        
        self.events.append(event)
        print(f"📤 Published quiz submission: {quiz_id} for {student_id}")
    
    def publish_content_view(
        self,
        student_id: str,
        module_name: str,
        topic_name: str,
        time_spent_seconds: int
    ):
        """Publish a content view event"""
        event = {
            "event_id": f"view_{student_id}_{datetime.now().timestamp()}",
            "student_id": student_id,
            "event_type": "content_view",
            "timestamp": int(datetime.now().timestamp()),
            "module_name": module_name,
            "topic_name": topic_name,
            "data": {
                "time_spent_seconds": time_spent_seconds
            }
        }
        
        self.events.append(event)
    
    def publish_struggle_event(
        self,
        student_id: str,
        module_name: str,
        topic_name: str,
        struggle_type: str,
        context: Dict[str, Any]
    ):
        """Publish a struggle indicator event"""
        event = {
            "event_id": f"struggle_{student_id}_{datetime.now().timestamp()}",
            "student_id": student_id,
            "event_type": "struggle",
            "timestamp": int(datetime.now().timestamp()),
            "module_name": module_name,
            "topic_name": topic_name,
            "data": {
                "struggle_type": struggle_type,
                **context
            }
        }
        
        self.events.append(event)
    
    def get_events(self) -> List[Dict[str, Any]]:
        """Get all published events"""
        return self.events
    
    def clear_events(self):
        """Clear event buffer"""
        self.events = []


if __name__ == "__main__":
    # Test the pipeline
    print("🧪 Testing Pathway Pipeline...")
    
    pipeline = PathwayPipeline()
    
    # Build pipeline with test data
    result_table = pipeline.build_full_pipeline(input_mode="python", output_mode="python")
    
    print("\n✅ Pipeline test complete!")
    print("📊 Pipeline ready for real-time processing")
    
    # Test event publisher
    publisher = EventPublisher()
    publisher.publish_quiz_submission(
        student_id="test_student_001",
        quiz_id="quiz_001",
        module_name="Module1",
        score=8.5,
        max_score=10.0,
        percentage=85.0,
        weak_topics=["Topic3"],
        time_taken_seconds=300
    )
    
    print(f"\n📤 Published {len(publisher.get_events())} test events")

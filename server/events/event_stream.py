"""
Real-time Event Streaming
==========================
Captures student learning events and streams them to Pathway pipeline
for real-time curriculum adaptation.
"""

import asyncio
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
from collections import deque
from dataclasses import dataclass, asdict
import logging

from streaming.pathway_pipeline import PathwayPipeline
from config.settings import get_settings

import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
import json
from queue import Queue
from threading import Thread
import time

from config.settings import settings


@dataclass
class StudentEvent:
    """Student interaction event"""
    event_id: str
    student_id: str
    event_type: str  # quiz_submit, content_view, time_spent, click, struggle, module_start, module_complete
    timestamp: int
    module_name: str
    topic_name: Optional[str] = None
    data: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_id": self.event_id,
            "student_id": self.student_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "module_name": self.module_name,
            "topic_name": self.topic_name,
            "data": self.data or {}
        }


class EventBuffer:
    """
    Thread-safe event buffer with backpressure handling
    """
    
    def __init__(self, max_size: int = 10000):
        """
        Initialize event buffer
        
        Args:
            max_size: Maximum buffer size
        """
        self.max_size = max_size
        self.queue = Queue(maxsize=max_size)
        self.dropped_count = 0
        self.total_count = 0
        
    def add(self, event: StudentEvent, block: bool = False, timeout: float = 1.0) -> bool:
        """
        Add event to buffer
        
        Args:
            event: Event to add
            block: Whether to block if buffer is full
            timeout: Timeout for blocking
            
        Returns:
            True if added, False if dropped
        """
        self.total_count += 1
        
        try:
            self.queue.put(event, block=block, timeout=timeout)
            return True
        except:
            self.dropped_count += 1
            return False
    
    def get(self, block: bool = True, timeout: float = None) -> Optional[StudentEvent]:
        """Get event from buffer"""
        try:
            return self.queue.get(block=block, timeout=timeout)
        except:
            return None
    
    def get_batch(self, batch_size: int = 100, timeout: float = 0.1) -> List[StudentEvent]:
        """Get batch of events"""
        batch = []
        
        for _ in range(batch_size):
            event = self.get(block=True, timeout=timeout)
            if event:
                batch.append(event)
            else:
                break
        
        return batch
    
    def size(self) -> int:
        """Get current buffer size"""
        return self.queue.qsize()
    
    def is_full(self) -> bool:
        """Check if buffer is full"""
        return self.queue.full()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics"""
        return {
            "current_size": self.size(),
            "max_size": self.max_size,
            "total_events": self.total_count,
            "dropped_events": self.dropped_count,
            "drop_rate": self.dropped_count / self.total_count if self.total_count > 0 else 0,
            "utilization": self.size() / self.max_size
        }


class EventStreamHandler:
    """
    Main event stream handler that captures interactions and streams to Pathway
    """
    
    def __init__(self, buffer_size: int = 10000, batch_size: int = 100):
        """
        Initialize event stream handler
        
        Args:
            buffer_size: Maximum buffer size
            batch_size: Batch size for processing
        """
        self.buffer = EventBuffer(max_size=buffer_size)
        self.batch_size = batch_size
        self.running = False
        self.worker_thread: Optional[Thread] = None
        self.event_handlers: List[Callable] = []
        self.stats = {
            "events_processed": 0,
            "events_failed": 0,
            "batches_processed": 0,
            "start_time": None
        }
        
        print("✅ Event Stream Handler initialized")
    
    def register_handler(self, handler: Callable[[List[StudentEvent]], None]):
        """
        Register an event handler function
        
        Args:
            handler: Function that takes list of events
        """
        self.event_handlers.append(handler)
        print(f"📝 Registered event handler: {handler.__name__}")
    
    def capture_event(
        self,
        student_id: str,
        event_type: str,
        module_name: str,
        topic_name: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Capture a student interaction event
        
        Args:
            student_id: Student identifier
            event_type: Type of event
            module_name: Module name
            topic_name: Topic name (optional)
            data: Additional event data
            
        Returns:
            True if captured, False if dropped
        """
        event = StudentEvent(
            event_id=f"{event_type}_{student_id}_{int(time.time() * 1000)}",
            student_id=student_id,
            event_type=event_type,
            timestamp=int(time.time()),
            module_name=module_name,
            topic_name=topic_name,
            data=data or {}
        )
        
        # Add to buffer with backpressure handling
        success = self.buffer.add(event, block=False)
        
        if not success:
            print(f"⚠️ Event dropped - buffer full: {event.event_type}")
        
        return success
    
    def capture_quiz_submission(
        self,
        student_id: str,
        quiz_id: str,
        module_name: str,
        score: float,
        max_score: float,
        percentage: float,
        weak_topics: List[str],
        time_taken_seconds: int
    ) -> bool:
        """Capture quiz submission event"""
        return self.capture_event(
            student_id=student_id,
            event_type="quiz_submit",
            module_name=module_name,
            data={
                "quiz_id": quiz_id,
                "score": score,
                "max_score": max_score,
                "percentage": percentage,
                "weak_topics": weak_topics,
                "time_taken_seconds": time_taken_seconds
            }
        )
    
    def capture_content_view(
        self,
        student_id: str,
        module_name: str,
        topic_name: str,
        time_spent_seconds: int
    ) -> bool:
        """Capture content view event"""
        return self.capture_event(
            student_id=student_id,
            event_type="content_view",
            module_name=module_name,
            topic_name=topic_name,
            data={"time_spent_seconds": time_spent_seconds}
        )
    
    def capture_struggle_indicator(
        self,
        student_id: str,
        module_name: str,
        topic_name: str,
        struggle_type: str,
        details: Dict[str, Any]
    ) -> bool:
        """Capture struggle indicator event"""
        return self.capture_event(
            student_id=student_id,
            event_type="struggle",
            module_name=module_name,
            topic_name=topic_name,
            data={
                "struggle_type": struggle_type,
                **details
            }
        )
    
    def capture_module_start(
        self,
        student_id: str,
        module_name: str
    ) -> bool:
        """Capture module start event"""
        return self.capture_event(
            student_id=student_id,
            event_type="module_start",
            module_name=module_name
        )
    
    def capture_module_complete(
        self,
        student_id: str,
        module_name: str,
        final_score: float
    ) -> bool:
        """Capture module completion event"""
        return self.capture_event(
            student_id=student_id,
            event_type="module_complete",
            module_name=module_name,
            data={"final_score": final_score}
        )
    
    def _process_batch(self, batch: List[StudentEvent]):
        """Process a batch of events"""
        if not batch:
            return
        
        # Call all registered handlers
        for handler in self.event_handlers:
            try:
                handler(batch)
                self.stats["events_processed"] += len(batch)
            except Exception as e:
                print(f"❌ Handler {handler.__name__} failed: {e}")
                self.stats["events_failed"] += len(batch)
        
        self.stats["batches_processed"] += 1
    
    def _worker_loop(self):
        """Background worker loop"""
        print("🔄 Event stream worker started")
        
        while self.running:
            # Get batch of events
            batch = self.buffer.get_batch(
                batch_size=self.batch_size,
                timeout=1.0
            )
            
            if batch:
                self._process_batch(batch)
            else:
                # No events - sleep briefly
                time.sleep(0.1)
        
        # Process remaining events on shutdown
        remaining = self.buffer.get_batch(batch_size=self.buffer.size())
        if remaining:
            print(f"🔄 Processing {len(remaining)} remaining events...")
            self._process_batch(remaining)
        
        print("🛑 Event stream worker stopped")
    
    def start(self):
        """Start the event stream handler"""
        if self.running:
            print("⚠️ Event stream handler already running")
            return
        
        self.running = True
        self.stats["start_time"] = datetime.now()
        
        # Start worker thread
        self.worker_thread = Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        print("✅ Event stream handler started")
    
    def stop(self):
        """Stop the event stream handler"""
        if not self.running:
            return
        
        print("🛑 Stopping event stream handler...")
        self.running = False
        
        # Wait for worker thread
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
        
        print("✅ Event stream handler stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics"""
        buffer_stats = self.buffer.get_stats()
        
        runtime = 0
        if self.stats["start_time"]:
            runtime = (datetime.now() - self.stats["start_time"]).total_seconds()
        
        events_per_second = self.stats["events_processed"] / runtime if runtime > 0 else 0
        
        return {
            "handler": {
                "running": self.running,
                "events_processed": self.stats["events_processed"],
                "events_failed": self.stats["events_failed"],
                "batches_processed": self.stats["batches_processed"],
                "runtime_seconds": runtime,
                "events_per_second": events_per_second
            },
            "buffer": buffer_stats,
            "handlers_registered": len(self.event_handlers)
        }


# Global event stream handler instance
_event_stream_handler: Optional[EventStreamHandler] = None


def get_event_stream_handler() -> EventStreamHandler:
    """Get global event stream handler instance"""
    global _event_stream_handler
    
    if _event_stream_handler is None:
        _event_stream_handler = EventStreamHandler(
            buffer_size=settings.PATHWAY_BUFFER_SIZE,
            batch_size=100
        )
    
    return _event_stream_handler


def start_event_stream():
    """Start the global event stream handler"""
    handler = get_event_stream_handler()
    handler.start()


def stop_event_stream():
    """Stop the global event stream handler"""
    handler = get_event_stream_handler()
    handler.stop()


# Example event handlers

def pathway_event_handler(events: List[StudentEvent]):
    """
    Handler that sends events to Pathway pipeline
    """
    print(f"📤 Sending {len(events)} events to Pathway pipeline")
    
    # In production, this would push to Pathway input connector
    # For now, we'll just log
    for event in events:
        event_dict = event.to_dict()
        # pathway_pipeline.input_connector.send(event_dict)
        print(f"  → {event.event_type}: {event.student_id} in {event.module_name}")


def analytics_event_handler(events: List[StudentEvent]):
    """
    Handler that sends events to analytics system
    """
    print(f"📊 Logging {len(events)} events to analytics")
    
    # Count event types
    event_counts = {}
    for event in events:
        event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
    
    print(f"  Event breakdown: {event_counts}")


def persistence_event_handler(events: List[StudentEvent]):
    """
    Handler that persists events to storage
    """
    print(f"💾 Persisting {len(events)} events")
    
    # In production, write to database or file
    # For now, just count
    pass


if __name__ == "__main__":
    # Test the event stream handler
    print("🧪 Testing Event Stream Handler...")
    
    # Create handler
    handler = EventStreamHandler(buffer_size=1000, batch_size=10)
    
    # Register handlers
    handler.register_handler(pathway_event_handler)
    handler.register_handler(analytics_event_handler)
    
    # Start handler
    handler.start()
    
    # Simulate events
    print("\n📤 Simulating student events...")
    
    for i in range(5):
        # Quiz submission
        handler.capture_quiz_submission(
            student_id=f"student_{i % 3}",
            quiz_id=f"quiz_{i}",
            module_name=f"Module_{i % 2 + 1}",
            score=7.5 + i * 0.5,
            max_score=10.0,
            percentage=75.0 + i * 5,
            weak_topics=["Topic 1", "Topic 3"] if i % 2 == 0 else [],
            time_taken_seconds=300 + i * 60
        )
        
        # Content view
        handler.capture_content_view(
            student_id=f"student_{i % 3}",
            module_name=f"Module_{i % 2 + 1}",
            topic_name=f"Topic_{i % 5}",
            time_spent_seconds=120 + i * 30
        )
    
    # Wait for processing
    print("\n⏳ Waiting for event processing...")
    time.sleep(3)
    
    # Get stats
    stats = handler.get_stats()
    print(f"\n📊 Handler Statistics:")
    print(json.dumps(stats, indent=2))
    
    # Stop handler
    handler.stop()
    
    print("\n✅ Event Stream Handler test complete!")

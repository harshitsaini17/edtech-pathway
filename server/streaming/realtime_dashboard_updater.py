"""
Real-Time Dashboard Updater
============================
WebSocket-based real-time curriculum updates for the dashboard.
Pushes curriculum adaptations instantly to connected students.
"""

import json
import asyncio
from typing import Dict, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass, asdict
import redis
from collections import defaultdict


@dataclass
class CurriculumUpdate:
    """Represents a curriculum update"""
    student_id: str
    timestamp: str
    update_type: str  # rerank, inject_remedial, difficulty_adjust, skip_ahead
    message: str
    new_curriculum: Dict[str, Any]
    actions: list
    priority: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class RealTimeDashboardUpdater:
    """
    Manages real-time curriculum updates to dashboard via WebSocket and Redis
    """
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        """
        Initialize the updater
        
        Args:
            redis_host: Redis server host
            redis_port: Redis server port
        """
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
        
        # In-memory storage for WebSocket connections (managed by FastAPI)
        self.websocket_connections: Dict[str, Set] = defaultdict(set)
        
        print("✅ Real-Time Dashboard Updater initialized")
    
    def register_websocket(self, student_id: str, websocket_id: str):
        """
        Register a WebSocket connection for a student
        
        Args:
            student_id: Student identifier
            websocket_id: Unique WebSocket connection ID
        """
        self.websocket_connections[student_id].add(websocket_id)
        print(f"📡 Registered WebSocket for student: {student_id}")
    
    def unregister_websocket(self, student_id: str, websocket_id: str):
        """
        Unregister a WebSocket connection
        
        Args:
            student_id: Student identifier
            websocket_id: Unique WebSocket connection ID
        """
        if student_id in self.websocket_connections:
            self.websocket_connections[student_id].discard(websocket_id)
            if not self.websocket_connections[student_id]:
                del self.websocket_connections[student_id]
        print(f"📡 Unregistered WebSocket for student: {student_id}")
    
    def push_curriculum_update(
        self,
        student_id: str,
        update_type: str,
        message: str,
        new_curriculum: Dict[str, Any],
        actions: list,
        priority: str = "medium"
    ) -> CurriculumUpdate:
        """
        Push curriculum update to student's dashboard
        
        Args:
            student_id: Student identifier
            update_type: Type of update (rerank, inject_remedial, etc.)
            message: Human-readable message
            new_curriculum: Updated curriculum data
            actions: List of actions taken
            priority: Update priority (low, medium, high, critical)
            
        Returns:
            CurriculumUpdate object
        """
        # Create update object
        update = CurriculumUpdate(
            student_id=student_id,
            timestamp=datetime.now().isoformat(),
            update_type=update_type,
            message=message,
            new_curriculum=new_curriculum,
            actions=actions,
            priority=priority
        )
        
        # Store in Redis with TTL (1 hour)
        redis_key = f"curriculum_update:{student_id}"
        self.redis_client.setex(
            redis_key,
            3600,  # 1 hour TTL
            update.to_json()
        )
        
        # Also store in a list for history
        history_key = f"curriculum_updates:history:{student_id}"
        self.redis_client.lpush(history_key, update.to_json())
        self.redis_client.ltrim(history_key, 0, 49)  # Keep last 50 updates
        self.redis_client.expire(history_key, 86400)  # 24 hour expiry
        
        # Publish to Redis pub/sub for WebSocket workers
        channel = f"curriculum_updates:{student_id}"
        self.redis_client.publish(channel, update.to_json())
        
        print(f"📤 Pushed curriculum update for {student_id}: {update_type}")
        
        return update
    
    def get_pending_update(self, student_id: str) -> Optional[CurriculumUpdate]:
        """
        Get pending curriculum update for a student
        
        Args:
            student_id: Student identifier
            
        Returns:
            CurriculumUpdate if available, None otherwise
        """
        redis_key = f"curriculum_update:{student_id}"
        update_json = self.redis_client.get(redis_key)
        
        if update_json:
            update_dict = json.loads(update_json)
            return CurriculumUpdate(**update_dict)
        
        return None
    
    def clear_pending_update(self, student_id: str):
        """
        Clear pending update after it's been consumed
        
        Args:
            student_id: Student identifier
        """
        redis_key = f"curriculum_update:{student_id}"
        self.redis_client.delete(redis_key)
    
    def get_update_history(self, student_id: str, limit: int = 10) -> list:
        """
        Get update history for a student
        
        Args:
            student_id: Student identifier
            limit: Maximum number of updates to return
            
        Returns:
            List of CurriculumUpdate objects
        """
        history_key = f"curriculum_updates:history:{student_id}"
        updates_json = self.redis_client.lrange(history_key, 0, limit - 1)
        
        updates = []
        for update_json in updates_json:
            update_dict = json.loads(update_json)
            updates.append(CurriculumUpdate(**update_dict))
        
        return updates
    
    def create_notification_message(self, update_type: str, actions: list) -> str:
        """
        Create user-friendly notification message
        
        Args:
            update_type: Type of update
            actions: List of actions taken
            
        Returns:
            Formatted message string
        """
        if update_type == "rerank":
            return "🔄 Your learning path has been optimized based on your performance!"
        elif update_type == "inject_remedial":
            num_topics = len([a for a in actions if a.get('action') == 'inject_remedial'])
            return f"💉 Added {num_topics} remedial topics to strengthen your foundation"
        elif update_type == "difficulty_adjust":
            direction = "increased" if any("increase" in str(a) for a in actions) else "decreased"
            return f"🎚️ Content difficulty has been {direction} to match your level"
        elif update_type == "skip_ahead":
            return "⚡ Great job! You're ready to skip ahead to advanced content"
        else:
            return "✨ Your curriculum has been personalized based on your progress"
    
    async def listen_for_updates(self, student_id: str, callback):
        """
        Listen for real-time updates using Redis pub/sub
        
        Args:
            student_id: Student identifier
            callback: Async function to call when update received
        """
        pubsub = self.redis_client.pubsub()
        channel = f"curriculum_updates:{student_id}"
        pubsub.subscribe(channel)
        
        print(f"👂 Listening for updates for student: {student_id}")
        
        try:
            for message in pubsub.listen():
                if message['type'] == 'message':
                    update_dict = json.loads(message['data'])
                    update = CurriculumUpdate(**update_dict)
                    await callback(update)
        except Exception as e:
            print(f"❌ Error listening for updates: {e}")
        finally:
            pubsub.unsubscribe(channel)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about updates"""
        return {
            "active_connections": sum(len(conns) for conns in self.websocket_connections.values()),
            "students_connected": len(self.websocket_connections),
            "redis_connected": self.redis_client.ping()
        }


# Integration helper for CurriculumAdapter
def push_adaptation_to_dashboard(
    student_id: str,
    adaptation_decision: Dict[str, Any],
    updated_curriculum: Dict[str, Any],
    redis_host: str = "localhost",
    redis_port: int = 6379
):
    """
    Helper function to push adaptation decision to dashboard
    
    Args:
        student_id: Student identifier
        adaptation_decision: Decision from CurriculumAdapter
        updated_curriculum: Updated curriculum structure
        redis_host: Redis host
        redis_port: Redis port
    """
    updater = RealTimeDashboardUpdater(redis_host, redis_port)
    
    # Extract info from decision
    update_type = adaptation_decision.get('decision_type', 'adapt')
    actions = adaptation_decision.get('actions', [])
    priority = adaptation_decision.get('priority', 'medium')
    
    # Create user-friendly message
    message = updater.create_notification_message(update_type, actions)
    
    # Push update
    updater.push_curriculum_update(
        student_id=student_id,
        update_type=update_type,
        message=message,
        new_curriculum=updated_curriculum,
        actions=actions,
        priority=priority
    )


if __name__ == "__main__":
    # Test the updater
    print("\n🧪 Testing Real-Time Dashboard Updater\n")
    
    updater = RealTimeDashboardUpdater()
    
    # Test push
    test_curriculum = {
        "modules": [
            {"title": "Module 1", "topics": ["Topic 1", "Topic 2"]}
        ]
    }
    
    update = updater.push_curriculum_update(
        student_id="test_student_001",
        update_type="rerank",
        message="Test update",
        new_curriculum=test_curriculum,
        actions=[{"action": "rerank_topics", "count": 2}],
        priority="high"
    )
    
    print(f"✅ Pushed update: {update.update_type}")
    
    # Test retrieval
    pending = updater.get_pending_update("test_student_001")
    if pending:
        print(f"✅ Retrieved pending update: {pending.message}")
    
    # Test stats
    stats = updater.get_stats()
    print(f"📊 Stats: {stats}")
    
    print("\n✅ Test complete!")

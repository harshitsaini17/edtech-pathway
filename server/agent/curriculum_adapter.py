"""
Curriculum Adapter
===================
Consumes real-time performance data from Pathway and adapts curriculum dynamically.
Handles topic reranking, remedial content injection, and difficulty adjustment.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import os
import sys

from config.settings import settings
from db.vector_store import get_vector_store
from LLM import AdvancedAzureLLM

# Import real-time dashboard updater
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    from streaming.realtime_dashboard_updater import RealTimeDashboardUpdater, push_adaptation_to_dashboard
except ImportError:
    print("⚠️ Warning: Could not import RealTimeDashboardUpdater")
    RealTimeDashboardUpdater = None
    push_adaptation_to_dashboard = None


@dataclass
class AdaptationDecision:
    """Represents a curriculum adaptation decision"""
    student_id: str
    module_name: str
    decision_type: str  # rerank, inject_remedial, adjust_difficulty, skip_ahead
    reasoning: str
    actions: List[Dict[str, Any]]
    timestamp: datetime = field(default_factory=datetime.now)
    priority: str = "medium"  # low, medium, high, critical


@dataclass
class TopicRanking:
    """Represents ranked topics for a student"""
    topic_name: str
    original_position: int
    new_position: int
    priority_score: float
    reason: str


class CurriculumAdapter:
    """
    Dynamically adapts curriculum based on real-time student performance
    """
    
    def __init__(self):
        """Initialize the curriculum adapter"""
        self.vector_store = get_vector_store()
        self.llm = AdvancedAzureLLM()
        self.adaptation_history: Dict[str, List[AdaptationDecision]] = {}
        
        # Initialize real-time dashboard updater
        if RealTimeDashboardUpdater:
            try:
                self.dashboard_updater = RealTimeDashboardUpdater()
                print("✅ Real-time dashboard updater initialized")
            except Exception as e:
                print(f"⚠️ Could not initialize dashboard updater: {e}")
                self.dashboard_updater = None
        else:
            self.dashboard_updater = None
        
        print("✅ Curriculum Adapter initialized")
    
    def analyze_performance_signal(
        self,
        student_id: str,
        module_name: str,
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze incoming performance signal from Pathway
        
        Args:
            student_id: Student identifier
            module_name: Module name
            performance_data: Real-time performance metrics
            
        Returns:
            Analysis result with recommendations
        """
        avg_score = performance_data.get("average_score", 0)
        weak_topics = performance_data.get("weak_topics", [])
        struggle_count = performance_data.get("struggle_count", 0)
        performance_trend = performance_data.get("performance_trend", "stable")
        
        analysis = {
            "needs_remedial": avg_score < 60,
            "needs_reranking": len(weak_topics) > 0,
            "needs_skip_ahead": avg_score > 90 and struggle_count == 0,
            "needs_difficulty_adjustment": struggle_count > 3,
            "weak_topics": weak_topics,
            "performance_level": self._classify_performance(avg_score),
            "trend": performance_trend
        }
        
        print(f"📊 Performance analysis for {student_id}: {analysis['performance_level']}")
        
        return analysis
    
    def _classify_performance(self, avg_score: float) -> str:
        """Classify performance level"""
        if avg_score >= 90:
            return "excellent"
        elif avg_score >= 75:
            return "good"
        elif avg_score >= 60:
            return "satisfactory"
        elif avg_score >= 40:
            return "struggling"
        else:
            return "critical"
    
    def rerank_topics(
        self,
        module_name: str,
        current_topics: List[str],
        weak_topics: List[str],
        performance_data: Dict[str, Any]
    ) -> List[TopicRanking]:
        """
        Rerank topics based on student weaknesses
        
        Args:
            module_name: Module name
            current_topics: Current topic order
            weak_topics: Topics student is weak in
            performance_data: Performance metrics
            
        Returns:
            List of topic rankings with new positions
        """
        rankings: List[TopicRanking] = []
        
        # Create priority scores
        topic_scores = {}
        for i, topic in enumerate(current_topics):
            base_score = 1.0 - (i / len(current_topics))  # Later topics get lower base score
            
            # Boost weak topics
            if topic in weak_topics:
                priority_score = base_score + 0.5  # Strong boost
                reason = "Identified as weak area - prioritizing review"
            else:
                priority_score = base_score
                reason = "Standard progression"
            
            topic_scores[topic] = (priority_score, reason, i)
        
        # Sort by priority score (descending)
        sorted_topics = sorted(
            topic_scores.items(),
            key=lambda x: x[1][0],
            reverse=True
        )
        
        # Create rankings
        for new_pos, (topic, (score, reason, orig_pos)) in enumerate(sorted_topics):
            rankings.append(TopicRanking(
                topic_name=topic,
                original_position=orig_pos,
                new_position=new_pos,
                priority_score=score,
                reason=reason
            ))
        
        print(f"🔄 Reranked {len(rankings)} topics for {module_name}")
        
        return rankings
    
    def inject_remedial_content(
        self,
        student_id: str,
        module_name: str,
        weak_topics: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate remedial content for weak topics
        
        Args:
            student_id: Student identifier
            module_name: Module name
            weak_topics: Topics needing remediation
            
        Returns:
            List of remedial content items
        """
        remedial_items = []
        
        for topic in weak_topics:
            # Search vector store for related concepts
            results = self.vector_store.search_topics(
                query=f"fundamentals and prerequisites for {topic}",
                n_results=3
            )
            
            # Extract topic information from results list
            related_topics = []
            if results:
                for r in results[:2]:
                    if isinstance(r, dict):
                        related_topics.append(r.get('topic', str(r)))
            
            # Generate remedial content using LLM
            prompt = f"""
Generate remedial learning content for a student struggling with: {topic}

Context from related materials:
{json.dumps(related_topics, indent=2)}

Create:
1. A simplified explanation (2-3 paragraphs)
2. 3 prerequisite concepts to review
3. 2 practice problems (easier than normal)
4. Tips for mastery

Format as JSON with keys: explanation, prerequisites, practice_problems, tips
"""
            
            try:
                response = self.llm.generate_response(prompt)
                
                # Try to parse as JSON
                try:
                    content = json.loads(response)
                except:
                    content = {"explanation": response}
                
                remedial_items.append({
                    "topic": topic,
                    "type": "remedial",
                    "content": content,
                    "estimated_time_minutes": 15,
                    "difficulty": "foundational"
                })
                
            except Exception as e:
                print(f"⚠️ Failed to generate remedial content for {topic}: {e}")
        
        print(f"💉 Injected {len(remedial_items)} remedial content items")
        
        return remedial_items
    
    def adjust_difficulty(
        self,
        module_name: str,
        current_difficulty: str,
        performance_data: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Adjust content difficulty based on performance
        
        Args:
            module_name: Module name
            current_difficulty: Current difficulty level
            performance_data: Performance metrics
            
        Returns:
            Tuple of (new_difficulty, reasoning)
        """
        avg_score = performance_data.get("average_score", 0)
        struggle_count = performance_data.get("struggle_count", 0)
        
        difficulty_levels = ["beginner", "intermediate", "advanced", "expert"]
        current_idx = difficulty_levels.index(current_difficulty) if current_difficulty in difficulty_levels else 1
        
        # Decision logic
        if avg_score > 90 and struggle_count == 0:
            # Increase difficulty
            new_idx = min(current_idx + 1, len(difficulty_levels) - 1)
            reasoning = "Excellent performance - increasing challenge"
        elif avg_score < 60 or struggle_count > 3:
            # Decrease difficulty
            new_idx = max(current_idx - 1, 0)
            reasoning = "Struggling detected - simplifying content"
        else:
            # Keep current
            new_idx = current_idx
            reasoning = "Performance stable - maintaining difficulty"
        
        new_difficulty = difficulty_levels[new_idx]
        
        print(f"🎚️ Difficulty adjusted: {current_difficulty} → {new_difficulty}")
        
        return new_difficulty, reasoning
    
    def should_skip_ahead(
        self,
        student_id: str,
        module_name: str,
        performance_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Determine if student should skip ahead in curriculum
        
        Args:
            student_id: Student identifier
            module_name: Module name
            performance_data: Performance metrics
            
        Returns:
            Tuple of (should_skip, reasoning)
        """
        avg_score = performance_data.get("average_score", 0)
        total_quizzes = performance_data.get("total_quizzes", 0)
        struggle_count = performance_data.get("struggle_count", 0)
        
        # Criteria for skipping
        if (
            avg_score >= 95
            and total_quizzes >= 3  # Has taken multiple quizzes
            and struggle_count == 0
        ):
            return True, "Exceptional performance - student ready for advanced material"
        
        return False, "Continue current progression"
    
    def make_adaptation_decision(
        self,
        student_id: str,
        module_name: str,
        performance_data: Dict[str, Any],
        current_curriculum: Dict[str, Any]
    ) -> AdaptationDecision:
        """
        Make comprehensive adaptation decision
        
        Args:
            student_id: Student identifier
            module_name: Module name
            performance_data: Real-time performance data
            current_curriculum: Current curriculum state
            
        Returns:
            Adaptation decision with actions
        """
        # Analyze performance
        analysis = self.analyze_performance_signal(student_id, module_name, performance_data)
        
        actions = []
        decision_type = "maintain"
        reasoning_parts = []
        priority = "medium"
        
        # Decision 1: Remedial content
        if analysis["needs_remedial"]:
            weak_topics = analysis["weak_topics"]
            remedial_items = self.inject_remedial_content(student_id, module_name, weak_topics)
            
            actions.append({
                "action": "inject_remedial",
                "items": remedial_items
            })
            
            decision_type = "inject_remedial"
            reasoning_parts.append(f"Injecting remedial content for {len(weak_topics)} weak topics")
            priority = "high"
        
        # Decision 2: Topic reranking
        if analysis["needs_reranking"]:
            current_topics = current_curriculum.get("topics", [])
            weak_topics = analysis["weak_topics"]
            
            rankings = self.rerank_topics(module_name, current_topics, weak_topics, performance_data)
            
            actions.append({
                "action": "rerank_topics",
                "rankings": [
                    {
                        "topic": r.topic_name,
                        "new_position": r.new_position,
                        "reason": r.reason
                    }
                    for r in rankings
                ]
            })
            
            if decision_type == "maintain":
                decision_type = "rerank"
            
            reasoning_parts.append(f"Reranked topics to prioritize weak areas")
        
        # Decision 3: Difficulty adjustment
        if analysis["needs_difficulty_adjustment"]:
            current_difficulty = current_curriculum.get("difficulty", "intermediate")
            new_difficulty, reason = self.adjust_difficulty(module_name, current_difficulty, performance_data)
            
            actions.append({
                "action": "adjust_difficulty",
                "from": current_difficulty,
                "to": new_difficulty,
                "reason": reason
            })
            
            if decision_type == "maintain":
                decision_type = "adjust_difficulty"
            
            reasoning_parts.append(reason)
        
        # Decision 4: Skip ahead
        should_skip, skip_reason = self.should_skip_ahead(student_id, module_name, performance_data)
        if should_skip:
            actions.append({
                "action": "skip_ahead",
                "reason": skip_reason
            })
            
            decision_type = "skip_ahead"
            reasoning_parts.append(skip_reason)
            priority = "medium"
        
        # Build decision
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No adaptation needed"
        
        decision = AdaptationDecision(
            student_id=student_id,
            module_name=module_name,
            decision_type=decision_type,
            reasoning=reasoning,
            actions=actions,
            priority=priority
        )
        
        # Store in history
        if student_id not in self.adaptation_history:
            self.adaptation_history[student_id] = []
        self.adaptation_history[student_id].append(decision)
        
        print(f"🎯 Adaptation decision made: {decision_type} ({priority} priority)")
        
        return decision
    
    def apply_adaptation(
        self,
        decision: AdaptationDecision,
        curriculum: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply adaptation decision to curriculum
        
        Args:
            decision: Adaptation decision
            curriculum: Current curriculum (with modules structure)
            
        Returns:
            Updated curriculum
        """
        import copy
        updated_curriculum = copy.deepcopy(curriculum)
        
        # Debug: Log original topics structure
        if updated_curriculum.get("modules"):
            for idx, module in enumerate(updated_curriculum["modules"]):
                topics = module.get("topics", [])
                print(f"📋 Module {idx} has {len(topics)} topics before adaptation")
                for t_idx, topic in enumerate(topics[:3]):  # Show first 3
                    if isinstance(topic, dict):
                        title = topic.get('topic_title') or topic.get('topic') or topic.get('title', 'NO_TITLE')
                        print(f"   Topic {t_idx}: {title[:50]}...")
                    else:
                        print(f"   Topic {t_idx}: {str(topic)[:50]}...")
        
        # Find the target module
        target_module_idx = None
        for idx, module in enumerate(updated_curriculum.get("modules", [])):
            if decision.module_name in module.get("title", ""):
                target_module_idx = idx
                break
        
        if target_module_idx is None and updated_curriculum.get("modules"):
            target_module_idx = 0  # Default to first module
        
        for action in decision.actions:
            action_type = action["action"]
            
            if action_type == "inject_remedial":
                # Add remedial content to the target module
                if target_module_idx is not None:
                    module = updated_curriculum["modules"][target_module_idx]
                    
                    # Create remedial topics from items
                    remedial_topics = []
                    for item in action.get("items", []):
                        # Extract topic name from the remedial item dictionary
                        if isinstance(item, dict):
                            topic_name = item.get("topic", "Unknown Topic")
                            remedial_topic = {
                                "title": f"📚 Review: {topic_name}",
                                "topic": f"📚 Review: {topic_name}",
                                "topic_title": f"📚 Review: {topic_name}",
                                "type": "remedial",
                                "content": item.get("content", {}),
                                "description": f"Foundational review of {topic_name}",
                                "estimated_duration": item.get("estimated_time_minutes", 15),
                                "difficulty": item.get("difficulty", "foundational")
                            }
                        else:
                            # Fallback for string items
                            remedial_topic = {
                                "title": f"📚 Review: {item}",
                                "topic": f"📚 Review: {item}",
                                "topic_title": f"📚 Review: {item}",
                                "type": "remedial",
                                "description": f"Foundational review of {item}",
                                "estimated_duration": "30 minutes"
                            }
                        remedial_topics.append(remedial_topic)
                    
                    # Insert at beginning of module topics
                    if "topics" in module:
                        module["topics"] = remedial_topics + module["topics"]
                    else:
                        module["topics"] = remedial_topics
                    
                    print(f"✅ Injected {len(remedial_topics)} remedial topics")
            
            elif action_type == "rerank_topics":
                # Reorder topics within the target module
                if target_module_idx is not None:
                    rankings = action.get("rankings", [])
                    module = updated_curriculum["modules"][target_module_idx]
                    current_topics = module.get("topics", [])
                    
                    if rankings and current_topics:
                        # Create new order based on rankings
                        sorted_rankings = sorted(rankings, key=lambda x: x.get("new_position", 999))
                        new_order = []
                        
                        for rank in sorted_rankings:
                            topic_title = rank.get("topic")
                            # Find matching topic
                            for topic in current_topics:
                                if isinstance(topic, dict) and topic.get("title") == topic_title:
                                    new_order.append(topic)
                                    break
                                elif isinstance(topic, str) and topic == topic_title:
                                    new_order.append(topic)
                                    break
                        
                        # Add any topics not in rankings
                        for topic in current_topics:
                            topic_title = topic.get("title") if isinstance(topic, dict) else topic
                            if topic_title not in [r.get("topic") for r in sorted_rankings]:
                                new_order.append(topic)
                        
                        module["topics"] = new_order
                        print(f"✅ Reranked {len(new_order)} topics")
            
            elif action_type == "adjust_difficulty":
                # Update difficulty level for the target module
                if target_module_idx is not None:
                    updated_curriculum["modules"][target_module_idx]["difficulty"] = action.get("to", "medium")
                    print(f"✅ Adjusted difficulty to {action.get('to')}")
            
            elif action_type == "skip_ahead":
                # Mark module as completed and move to next
                if target_module_idx is not None:
                    updated_curriculum["modules"][target_module_idx]["status"] = "skipped"
                    updated_curriculum["modules"][target_module_idx]["skip_reason"] = action.get("reason", "Performance exceeds requirements")
                    print(f"✅ Marked module as skipped")
        
        # Add metadata
        updated_curriculum["last_adapted"] = datetime.now().isoformat()
        updated_curriculum["adaptation_reason"] = decision.reasoning
        
        # Debug: Log final topics structure
        if updated_curriculum.get("modules"):
            for idx, module in enumerate(updated_curriculum["modules"]):
                topics = module.get("topics", [])
                print(f"📋 Module {idx} has {len(topics)} topics AFTER adaptation")
                for t_idx, topic in enumerate(topics[:5]):  # Show first 5
                    if isinstance(topic, dict):
                        title = topic.get('topic_title') or topic.get('topic') or topic.get('title', 'NO_TITLE')
                        print(f"   Topic {t_idx}: {title[:60]}")
                    else:
                        print(f"   Topic {t_idx}: {str(topic)[:60]}")
        
        print(f"✅ Applied adaptation: {decision.decision_type}")
        
        # Push real-time update to dashboard
        if push_adaptation_to_dashboard:
            try:
                # Convert AdaptationDecision object to dict
                decision_dict = asdict(decision)
                # Convert datetime to ISO string for JSON serialization
                if 'timestamp' in decision_dict and isinstance(decision_dict['timestamp'], datetime):
                    decision_dict['timestamp'] = decision_dict['timestamp'].isoformat()
                
                push_adaptation_to_dashboard(
                    student_id=decision.student_id,
                    adaptation_decision=decision_dict,
                    updated_curriculum=updated_curriculum
                )
                print(f"📡 Pushed real-time update to dashboard for {decision.student_id}")
            except Exception as e:
                print(f"⚠️ Could not push dashboard update: {e}")
        
        return updated_curriculum
    
    def get_adaptation_history(self, student_id: str) -> List[AdaptationDecision]:
        """Get adaptation history for a student"""
        return self.adaptation_history.get(student_id, [])
    
    def save_decision(self, decision: AdaptationDecision, output_dir: str = "./output/adaptations"):
        """Save adaptation decision to file"""
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{decision.student_id}_{decision.module_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump({
                "student_id": decision.student_id,
                "module_name": decision.module_name,
                "decision_type": decision.decision_type,
                "reasoning": decision.reasoning,
                "actions": decision.actions,
                "timestamp": decision.timestamp.isoformat(),
                "priority": decision.priority
            }, f, indent=2)
        
        print(f"💾 Decision saved to {filepath}")


if __name__ == "__main__":
    # Test the curriculum adapter
    print("🧪 Testing Curriculum Adapter...")
    
    adapter = CurriculumAdapter()
    
    # Test scenario: struggling student
    performance_data = {
        "average_score": 55.0,
        "weak_topics": ["Topic 3", "Topic 5"],
        "struggle_count": 4,
        "performance_trend": "declining",
        "total_quizzes": 5
    }
    
    current_curriculum = {
        "topics": ["Topic 1", "Topic 2", "Topic 3", "Topic 4", "Topic 5"],
        "difficulty": "intermediate"
    }
    
    # Make decision
    decision = adapter.make_adaptation_decision(
        student_id="test_student_001",
        module_name="Module1",
        performance_data=performance_data,
        current_curriculum=current_curriculum
    )
    
    print(f"\n📋 Decision: {decision.decision_type}")
    print(f"📝 Reasoning: {decision.reasoning}")
    print(f"⚡ Priority: {decision.priority}")
    print(f"🎬 Actions: {len(decision.actions)}")
    
    # Apply adaptation
    updated_curriculum = adapter.apply_adaptation(decision, current_curriculum)
    
    print(f"\n✅ Updated curriculum:")
    print(json.dumps(updated_curriculum, indent=2, default=str))
    
    # Save decision
    adapter.save_decision(decision)
    
    print("\n✅ Curriculum Adapter test complete!")

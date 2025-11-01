"""
Topic Title Beautifier
======================
LLM-powered topic title beautification for better UX.
Transforms raw PDF titles into student-friendly, engaging titles.
"""

import re
from typing import Optional, List, Dict
import json
from LLM import AdvancedAzureLLM


class TopicTitleBeautifier:
    """LLM-powered topic title beautification for better UX"""
    
    def __init__(self):
        """Initialize beautifier with LLM and cache"""
        self.llm = AdvancedAzureLLM()
        self.cache = {}  # Cache beautified titles
        
        # Common abbreviations to expand
        self.abbreviations = {
            'Pmf': 'Probability Mass Function',
            'Pdf': 'Probability Density Function',
            'Rv': 'Random Variable',
            'Rvs': 'Random Variables',
            'Cdf': 'Cumulative Distribution Function',
            'Mgf': 'Moment Generating Function',
            'Iid': 'Independent and Identically Distributed',
            'Vs': 'Versus',
            'E.G.': 'For Example',
            'I.E.': 'That Is'
        }
        
        print("✅ Topic Title Beautifier initialized")
    
    def beautify_topic_title(
        self, 
        raw_title: str, 
        context: Optional[str] = None,
        module_name: Optional[str] = None
    ) -> str:
        """
        Transform raw topic title into student-friendly, engaging title
        
        Args:
            raw_title: Original title from PDF (e.g., "4.4 Expectation")
            context: Surrounding content for context
            module_name: Module this topic belongs to
            
        Returns:
            Beautified title (e.g., "Understanding Expected Value")
        """
        # Check cache first
        cache_key = f"{raw_title}_{module_name}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # If title is already beautiful (no numbers at start, proper case), keep it
        if not re.match(r'^\d', raw_title) and not raw_title.isupper() and len(raw_title) > 15:
            return raw_title
        
        prompt = f"""Transform this technical topic title into a clear, engaging, student-friendly title.

ORIGINAL TITLE: "{raw_title}"
MODULE CONTEXT: "{module_name or 'General Statistics'}"

REQUIREMENTS:
1. Remove section numbers (e.g., "4.4", "5.2.1")
2. Expand abbreviations (PMF → Probability Mass Function)
3. Make it descriptive and engaging
4. Keep it concise (5-10 words)
5. Use consistent tone (active, clear, educational)
6. Add context if too generic
7. Avoid ALL CAPS or technical jargon
8. Use title case

GOOD EXAMPLES:
- "4.4 Expectation" → "Understanding Expected Value in Probability"
- "VARIANCE OF SUMS" → "Calculating Variance for Combined Variables"
- "The Binomial Random Variable" → "Introduction to Binomial Distribution"
- "5.2.1 Computing Expectations by Conditioning" → "Computing Expected Values Using Conditioning"

BAD EXAMPLES (avoid these):
- "Learn About Expectation" (too vague)
- "Expected Value Calculation Methods and Applications in Statistics" (too long)
- "EV" (too technical/abbreviated)

Return ONLY the beautified title, nothing else:"""
        
        try:
            beautified = self.llm.gpt_5_mini(prompt).strip()
            
            # Remove quotes if LLM added them
            beautified = beautified.strip('"\'')
            
            # Validation checks
            if len(beautified) < 10 or len(beautified) > 100:
                # Fallback: Simple cleanup
                beautified = self._simple_beautify(raw_title)
            
            # Ensure title case
            beautified = self._ensure_title_case(beautified)
            
            # Cache result
            self.cache[cache_key] = beautified
            
            return beautified
            
        except Exception as e:
            print(f"⚠️ Title beautification failed for '{raw_title}': {e}")
            return self._simple_beautify(raw_title)
    
    def _simple_beautify(self, raw_title: str) -> str:
        """Fallback: Rule-based beautification"""
        title = raw_title
        
        # Remove section numbers
        title = re.sub(r'^\d+\.[\d\.]*\s*', '', title)
        title = re.sub(r'^\*\d+\.[\d\.]*\s*', '', title)  # Remove starred sections
        
        # Remove chapter/section prefixes
        title = re.sub(r'^(Chapter|Section|Appendix)\s+\d+\s*[-:]?\s*', '', title, flags=re.IGNORECASE)
        
        # Title case
        title = title.title()
        
        # Expand common abbreviations
        for abbr, full in self.abbreviations.items():
            title = title.replace(abbr, full)
        
        # Clean up extra spaces
        title = ' '.join(title.split())
        
        # Ensure it's not too short
        if len(title) < 10:
            title = f"Understanding {title}"
        
        return title
    
    def _ensure_title_case(self, title: str) -> str:
        """Ensure proper title case"""
        # Words that should stay lowercase
        lowercase_words = {'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'in', 
                          'of', 'on', 'or', 'the', 'to', 'with'}
        
        words = title.split()
        if not words:
            return title
        
        # First word always capitalized
        result = [words[0].capitalize()]
        
        # Process remaining words
        for word in words[1:]:
            if word.lower() in lowercase_words:
                result.append(word.lower())
            else:
                result.append(word.capitalize())
        
        return ' '.join(result)
    
    def beautify_batch(
        self, 
        topics: List[Dict],
        module_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Beautify all topics in a batch for consistency
        
        Args:
            topics: List of topic dictionaries
            module_name: Module name for context
            
        Returns:
            Topics with beautified titles
        """
        print(f"✨ Beautifying {len(topics)} topic titles...")
        
        beautified_count = 0
        for topic in topics:
            original = topic.get('topic', topic.get('title', ''))
            
            if not original:
                continue
            
            # Get module context
            topic_module = topic.get('module_name', module_name)
            
            # Beautify
            beautified = self.beautify_topic_title(
                original,
                context=topic.get('content', ''),
                module_name=topic_module
            )
            
            # Store both for reference
            if beautified != original:
                topic['original_title'] = original
                beautified_count += 1
            
            topic['topic'] = beautified
            topic['title'] = beautified
        
        print(f"✅ Beautified {beautified_count} topic titles")
        return topics
    
    def get_topic_emoji(self, title: str) -> str:
        """
        Add contextual emoji to topics for visual appeal
        
        Args:
            title: Topic title
            
        Returns:
            Appropriate emoji
        """
        title_lower = title.lower()
        
        if 'introduction' in title_lower or 'basics' in title_lower or 'fundamental' in title_lower:
            return '🎯'
        elif 'probability' in title_lower or 'distribution' in title_lower:
            return '🎲'
        elif 'calculation' in title_lower or 'formula' in title_lower or 'computing' in title_lower:
            return '🧮'
        elif 'application' in title_lower or 'practice' in title_lower or 'example' in title_lower:
            return '💡'
        elif 'variance' in title_lower or 'covariance' in title_lower or 'deviation' in title_lower:
            return '📊'
        elif 'test' in title_lower or 'hypothesis' in title_lower:
            return '🔬'
        elif 'expectation' in title_lower or 'expected value' in title_lower:
            return '⭐'
        elif 'random variable' in title_lower:
            return '🎰'
        elif 'theorem' in title_lower or 'proof' in title_lower:
            return '📐'
        elif 'simulation' in title_lower or 'monte carlo' in title_lower:
            return '🎮'
        else:
            return '📚'


def beautify_curriculum_topics(curriculum: Dict) -> Dict:
    """
    Beautify all topic titles in a curriculum
    
    Args:
        curriculum: Curriculum dictionary
        
    Returns:
        Curriculum with beautified topics
    """
    beautifier = TopicTitleBeautifier()
    
    modules = curriculum.get('modules', [])
    
    for module in modules:
        module_name = module.get('title', '')
        topics = module.get('topics', [])
        
        # Beautify each topic
        beautified_topics = []
        for topic in topics:
            if isinstance(topic, str):
                # Simple string topic
                beautified = beautifier.beautify_topic_title(topic, module_name=module_name)
                beautified_topics.append(beautified)
            elif isinstance(topic, dict):
                # Dictionary topic
                original = topic.get('topic', topic.get('title', ''))
                beautified = beautifier.beautify_topic_title(original, module_name=module_name)
                topic['original_title'] = original
                topic['topic'] = beautified
                topic['title'] = beautified
                beautified_topics.append(topic)
            else:
                beautified_topics.append(topic)
        
        module['topics'] = beautified_topics
    
    return curriculum


if __name__ == "__main__":
    # Test the beautifier
    beautifier = TopicTitleBeautifier()
    
    test_titles = [
        "4.4 Expectation",
        "4.7 Covariance and Variance of Sums of Random Variables",
        "5.2.1 The Binomial Random Variable",
        "VARIANCE OF SUMS",
        "8.6 Hypothesis Tests in Bernoulli Populations",
        "Properties of the Expected Value",
        "*3.8 Independent Events"
    ]
    
    print("\n🧪 Testing Topic Title Beautifier\n")
    print("-" * 80)
    
    for title in test_titles:
        beautified = beautifier.beautify_topic_title(title)
        emoji = beautifier.get_topic_emoji(beautified)
        print(f"{emoji} {title:50s} → {beautified}")
    
    print("-" * 80)
    print("✅ Test complete!")

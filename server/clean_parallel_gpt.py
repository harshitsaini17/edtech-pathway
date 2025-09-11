#!/usr/bin/env python3
"""
Clean Parallel GPT Implementation for Topic Filtering
=====================================================
"""

import asyncio
import json
import re
from typing import List, Dict, Tuple

class ParallelGPTFilter:
    """Parallel GPT filtering for educational topics"""
    
    def __init__(self):
        self.system_message = """You are an expert educational content analyzer. Your task is to filter topic titles from educational PDFs and keep only genuine educational topics.

KEEP these types of topics:
- Chapter titles (e.g., "Chapter 1: Introduction to Probability")
- Section headings (e.g., "2.1 Random Variables", "Normal Distribution")
- Mathematical concepts (e.g., "Bayes' Theorem", "Central Limit Theorem")
- Definitions and theorems
- Core educational content titles
- Applications and methods

FILTER OUT (remove) these types of topics:
- Examples with specific numbers/instances (e.g., "Example 2.3", "Problem 4.5")
- Exercise numbers and homework references
- Figure and table captions
- Page headers/footers and navigation text
- References to specific problems or solutions
- Fragmentary or incomplete text
- Non-educational content (acknowledgments, prefaces, etc.)

Return ONLY a JSON array of topic indices (0-based) that should be KEPT. For example: [0, 2, 5, 8, 10]
Do not include explanations, just the JSON array."""

    def filter_topics_parallel(self, topics: List[Dict]) -> List[Dict]:
        """
        Filter topics using GPT-5-mini with parallel processing
        """
        
        if not topics:
            return topics
            
        print(f"🤖 Starting GPT-based parallel filtering for {len(topics)} topics...")
        
        # Initialize LLM client
        try:
            from LLM import AdvancedAzureLLM
            llm = AdvancedAzureLLM()
            llm.switch_model("gpt-5-mini")  # Use GPT-5-mini for efficient filtering
        except Exception as e:
            print(f"⚠️ Could not initialize GPT client: {e}")
            print("📝 Skipping GPT filtering, returning original topics")
            return topics
        
        # Run async processing
        return asyncio.run(self._process_batches_parallel(topics, llm))
    
    async def _process_batches_parallel(self, topics: List[Dict], llm) -> List[Dict]:
        """Process batches in parallel using asyncio"""
        
        # Group topics into smaller batches for better parallelization
        batch_size = 75  # Optimal batch size for parallel processing
        batches = [topics[i:i + batch_size] for i in range(0, len(topics), batch_size)]
        
        print(f"🚀 Processing {len(batches)} batches in parallel...")
        
        # Create tasks for parallel processing
        tasks = []
        for batch_idx, batch in enumerate(batches):
            task = self._process_single_batch(batch, batch_idx, llm)
            tasks.append(task)
        
        # Process all batches concurrently
        print(f"⚡ Launching {len(tasks)} parallel tasks...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect results
        all_filtered_topics = []
        total_kept = 0
        successful_batches = 0
        
        for batch_idx, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"⚠️ Error in batch {batch_idx + 1}: {result}")
                # Fallback: keep all topics in failed batch
                batch = batches[batch_idx]
                for topic_dict in batch:
                    topic_dict['gpt_filtered'] = False
                    topic_dict['batch_id'] = batch_idx + 1
                    all_filtered_topics.append(topic_dict)
                total_kept += len(batch)
            else:
                batch_topics, kept_count = result
                all_filtered_topics.extend(batch_topics)
                total_kept += kept_count
                successful_batches += 1
        
        total_original = len(topics)
        total_filtered = total_original - total_kept
        retention_rate = (total_kept / total_original) * 100 if total_original > 0 else 0
        
        print(f"🎯 Parallel GPT filtering complete:")
        print(f"   📊 Original topics: {total_original}")
        print(f"   🚫 Filtered by GPT: {total_filtered}")
        print(f"   ✅ Topics kept: {total_kept}")
        print(f"   🚀 Successful parallel batches: {successful_batches}/{len(batches)}")
        print(f"   📈 Retention rate: {retention_rate:.1f}%")
        
        return all_filtered_topics
    
    async def _process_single_batch(self, batch: List[Dict], batch_idx: int, llm) -> Tuple[List[Dict], int]:
        """Process a single batch asynchronously"""
        
        print(f"🔄 Processing batch {batch_idx + 1} ({len(batch)} topics)...")
        
        # Create prompt for this batch
        topics_text = ""
        for i, topic_dict in enumerate(batch):
            topic_text = topic_dict['topic']
            page_num = topic_dict.get('page', 'Unknown')
            topics_text += f"{i}: \"{topic_text}\" (Page {page_num})\n"
        
        prompt = f"Filter these {len(batch)} topic titles and return indices of topics to KEEP:\n\n{topics_text}"
        
        try:
            # Use async_generate for parallel processing
            response = await llm.async_generate(prompt, system_message=self.system_message)
            response = response.strip()
            
            # Parse the JSON response
            try:
                if response.startswith('[') and response.endswith(']'):
                    keep_indices = json.loads(response)
                else:
                    # Try to extract JSON from response
                    json_match = re.search(r'\[([\d,\s]+)\]', response)
                    if json_match:
                        keep_indices = json.loads(json_match.group(0))
                    else:
                        print(f"⚠️ Could not parse GPT response for batch {batch_idx + 1}, keeping all topics")
                        keep_indices = list(range(len(batch)))
                
                # Validate indices and add kept topics
                filtered_batch_topics = []
                for idx in keep_indices:
                    if 0 <= idx < len(batch):
                        topic_dict = batch[idx].copy()
                        topic_dict['gpt_filtered'] = True
                        topic_dict['batch_id'] = batch_idx + 1
                        filtered_batch_topics.append(topic_dict)
                
                print(f"✅ Batch {batch_idx + 1}: kept {len(keep_indices)}/{len(batch)} topics")
                return filtered_batch_topics, len(keep_indices)
                
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parsing error for batch {batch_idx + 1}: {e}")
                print(f"📝 GPT response was: {response[:100]}...")
                # Fallback: keep all topics in this batch
                fallback_topics = []
                for topic_dict in batch:
                    topic_dict['gpt_filtered'] = False
                    topic_dict['batch_id'] = batch_idx + 1
                    fallback_topics.append(topic_dict)
                return fallback_topics, len(batch)
                
        except Exception as e:
            print(f"⚠️ Error processing batch {batch_idx + 1}: {e}")
            # Fallback: keep all topics in this batch
            fallback_topics = []
            for topic_dict in batch:
                topic_dict['gpt_filtered'] = False
                topic_dict['batch_id'] = batch_idx + 1
                fallback_topics.append(topic_dict)
            return fallback_topics, len(batch)


# Test the implementation
if __name__ == "__main__":
    # Test sample
    sample_topics = [
        {"topic": "Chapter 1: Introduction to Probability Theory", "page": 1, "confidence": 0.9},
        {"topic": "Example 1.3: Rolling a Six-Sided Die", "page": 8, "confidence": 0.7},
        {"topic": "Definition 1.1: Probability Space", "page": 15, "confidence": 0.9},
        {"topic": "Exercise 1.5", "page": 18, "confidence": 0.5},
        {"topic": "Theorem 1.3: Addition Rule for Probability", "page": 25, "confidence": 0.9},
    ]
    
    print("🧪 Testing Parallel GPT Filtering")
    print("=" * 40)
    
    filter_instance = ParallelGPTFilter()
    filtered = filter_instance.filter_topics_parallel(sample_topics)
    
    print(f"\n📊 Results: {len(filtered)} topics kept from {len(sample_topics)} original topics")
    for topic in filtered:
        print(f"  ✅ {topic['topic']} (Page {topic['page']})")

#!/usr/bin/env python3

"""
Advanced Multi-Strategy Topic Extractor with 2-Stage GPT Filtering
================================================================
Enhanced with negative filters and optimized 2-stage GPT processing
"""

import fitz
import re
import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from collections import Counter
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

@dataclass
class TopicCandidate:
    """Represents a potential topic with confidence scoring"""
    text: str
    page: int
    confidence: float
    extraction_method: str
    context: str
    position: str  # 'header', 'body', 'toc'
    is_filtered: bool = False  # Whether topic was filtered out
    filter_reason: str = ""  # Reason for filtering

class AdvancedMultiStrategyExtractor:
    """
    Advanced topic extraction using multiple strategies and confidence scoring
    """

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.candidates: List[TopicCandidate] = []
        self.final_topics: List[Dict] = []

        # Enhanced keyword-based filtering with expanded coverage
        self.example_keywords = [
            'example', 'for example', 'for instance', 'such as', 'e.g.', 'namely',
            'like', 'including', 'particularly', 'especially', 'consider', 'suppose',
            'let us', 'assume', 'given that', 'say', 'illustration', 'sample',
            'demonstrate', 'exemplify', 'instance of', 'case study', 'scenario'
        ]

        self.concluding_keywords = [
            'however', 'follows', 'shows', 'thus', 'therefore', 'because', 'since', 'consequently',
            'as a result', 'in conclusion', 'finally', 'hence', 'moreover',
            'furthermore', 'nevertheless', 'nonetheless', 'although', 'whereas',
            'meanwhile', 'otherwise', 'accordingly', 'subsequently', 'ultimately',
            'in summary', 'to conclude', 'therefore', 'as we have seen', 'evidently'
        ]

        # Additional exclusion filters for non-educational content
        self.exclusion_phrases = [
            'exercise', 'problem set', 'homework', 'assignment', 'quiz', 'exam',
            'figure', 'table', 'chart', 'graph', 'diagram', 'caption',
            'reference', 'bibliography', 'citation', 'footnote', 'endnote',
            'acknowledgment', 'preface', 'foreword', 'index', 'glossary',
            'copyright', 'isbn', 'publisher', 'printing', 'edition',
            'page header', 'page footer', 'chapter summary', 'review questions',
            'self-test', 'practice problems', 'solutions manual'
        ]

        # Pattern-based exclusion for specific formats
        self.exclusion_patterns = [
            r'^\d+\.\d+[a-z]?\s*$',  # Just numbers like "2.3a"
            r'^(fig|figure|table|chart)\s+\d+',  # Figure/table references
            r'^(problem|exercise|question)\s+\d+',  # Problem numbers
            r'^\d+\s*-\s*\d+$',  # Page ranges like "123-145"
            r'^[A-Z]{2,}\s*\d*$',  # All caps abbreviations
            r'^[a-z]\)\s*',  # Lettered lists like "a) something"
        ]

        # NEW: Advanced negative filters for data fragments and unwanted content
        self.negative_filters = [
            # Data fragments and lists
            r'^\d+\.?\d*\s+[A-Z][a-z]\s+[A-Z][a-z]',  # "51.3 Hi Honolulu"
            r'^\d+\.?\d*\s+[A-Z][a-z]{2}\s+[A-Z]',     # "69.0 Ga Atlanta"
            r'^\d+\.?\d*\s+(Thus|Hence|Therefore|However|Moreover)',  # Sentence starters
            
            # Publication/legal content
            r'(copyright|isbn|©|\(c\)|publisher|edition|printing|elsevier)',
            r'(www\.|http|\.com|\.org|email|@)',
            
            # Figure/table references
            r'(page|fig|figure|table|chart|graph|diagram)\s+\d+',
            r'^\d+\.\d+\s+(figure|table|chart|graph)',
            
            # Short or malformed content
            r'^\d+\s*$',  # Just numbers
            r'^[A-Z]\s*$',  # Single letters
            r'^\w{1,3}$',  # Very short strings
            
            # Sentence fragments (topics shouldn't be sentences)
            r'thus|hence|therefore|however|moreover|furthermore|additionally',
            r'this\s+(book|chapter|section|problem|example)',
            
            # Data tables and measurements
            r'^\d+\.?\d*\s+[A-Z][a-z]{1,20}\.{3,}',  # "51.0 Ca Los Angeles..."
            r'year|month|day|temperature|rainfall|humidity',
        ]

        # Multi-level patterns for comprehensive coverage
        self.extraction_patterns = {
            'numbered_sections': [
                r'(\d{1,2}\.\d{1,2}(?:\.\d{1,2})*)\s+([A-Z][A-Za-z][^.!?]*?)(?=\n|\s{2,}|$)',
                r'(\d{1,2}\.\d{1,2})\s+([A-Z][A-Z\s]{8,50})',  # All caps
                r'(Chapter\s+\d+)\s*[-:.]?\s*([A-Za-z][^.!?]{10,80})',
                r'(Section\s+\d+(?:\.\d+)*)\s+([A-Za-z][^.!?]{8,60})',
                r'(Appendix\s+[A-Z])\s*[-:.]?\s*([A-Za-z][^.!?]{8,60})',
            ],
            'header_detection': [
                r'^([A-Z][A-Z\s]{12,60})$',  # All caps headers
                r'^(\d{1,2}\.\d{1,2}(?:\.\d{1,2})*\s+[A-Z][A-Za-z\s]{8,60})$',
                r'^(EXAMPLE\s+\d+\.\d+[a-z]?\s+[A-Za-z][^.!?]{5,50})$',
                r'^(DEFINITION\s+\d+\.\d+[^.!?]{5,50})$',
                r'^(THEOREM\s+\d+\.\d+[^.!?]{5,50})$',
            ],
            'content_markers': [
                r'(EXAMPLE\s+\d+\.\d+[a-z]?)\s*([A-Za-z][^.!?]{5,50})?',
                r'(SOLUTION\s+\d+\.\d+[a-z]?)\s*([A-Za-z][^.!?]{5,50})?',
                r'(Problem\s+\d+\.\d+)\s*([A-Za-z][^.!?]{5,50})?',
                r'(Exercise\s+\d+\.\d+)\s*([A-Za-z][^.!?]{5,50})?',
            ]
        }

        # Quality scoring keywords
        self.quality_indicators = {
            'high_value': ['introduction', 'theorem', 'definition', 'example',
                          'solution', 'analysis', 'applications', 'method',
                          'algorithm', 'principle', 'theory', 'concept', 'model'],
            'domain_specific': ['probability', 'distribution', 'random', 'variable',
                               'binomial', 'poisson', 'normal', 'variance', 'expectation',
                               'hypothesis', 'test', 'estimation', 'regression',
                               'correlation', 'statistics', 'inference'],
            'structural': ['chapter', 'section', 'appendix', 'summary', 'conclusion',
                          'overview', 'background', 'methodology', 'results']
        }

    def extract_with_multiple_strategies(self) -> List[Dict]:
        """
        Main extraction method using multiple strategies
        """
        print(f"🚀 Starting Advanced Multi-Strategy Extraction")
        print(f"📖 PDF: {os.path.basename(self.pdf_path)} ({len(self.doc)} pages)")

        # Strategy 1: Table of Contents (highest confidence)
        toc_candidates = self._extract_from_toc()

        # Strategy 2: Page-by-page content analysis
        content_candidates = self._extract_from_content()

        # Strategy 3: Font and formatting analysis
        formatting_candidates = self._extract_by_formatting()

        # Strategy 4: Context-aware extraction
        context_candidates = self._extract_with_context()

        # Combine all candidates
        all_candidates = toc_candidates + content_candidates + formatting_candidates + context_candidates

        # Score and filter candidates
        scored_candidates = self._score_candidates(all_candidates)

        # Remove duplicates and create final list
        final_topics = self._deduplicate_and_finalize(scored_candidates)

        # Apply filters in sequence
        final_topics = self._filter_by_keywords(final_topics)
        final_topics = self._filter_by_negative_patterns(final_topics)
        final_topics = self._filter_by_quality(final_topics)

        # NEW: 2-Stage GPT filtering with balanced prompts
        final_topics = self._filter_by_gpt_two_stage_balanced(final_topics)

        print(f"✅ Extraction complete: {len(final_topics)} topics found")
        return final_topics

    def _extract_from_toc(self) -> List[TopicCandidate]:
        """Extract from table of contents with high confidence"""
        candidates = []
        try:
            toc = self.doc.get_toc()
            if toc:
                print(f"📑 Processing TOC with {len(toc)} entries")
                for level, title, page in toc:
                    if title and len(title.strip()) > 2:
                        clean_title = self._clean_topic_text(title)
                        if clean_title:
                            candidates.append(TopicCandidate(
                                text=clean_title,
                                page=page,
                                confidence=0.9,
                                extraction_method='toc',
                                context='table_of_contents',
                                position='toc'
                            ))
        except Exception as e:
            print(f"⚠️ TOC extraction error: {e}")

        print(f"📑 TOC candidates: {len(candidates)}")
        return candidates

    def _extract_from_content(self) -> List[TopicCandidate]:
        """Extract from page content using pattern matching"""
        candidates = []
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            text = page.get_text()
            if not text.strip():
                continue

            # Apply all pattern categories
            for category, patterns in self.extraction_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
                    for match in matches:
                        if len(match.groups()) >= 1:
                            topic_parts = [g for g in match.groups() if g and g.strip()]
                            topic_text = ' '.join(topic_parts).strip()
                            if len(topic_text) > 3:
                                clean_topic = self._clean_topic_text(topic_text)
                                if clean_topic and self._is_valid_topic(clean_topic):
                                    confidence = self._calculate_confidence(clean_topic, category, text)
                                    candidates.append(TopicCandidate(
                                        text=clean_topic,
                                        page=page_num + 1,
                                        confidence=confidence,
                                        extraction_method='content_pattern',
                                        context=category,
                                        position='body'
                                    ))

        print(f"📄 Content candidates: {len(candidates)}")
        return candidates

    def _extract_by_formatting(self) -> List[TopicCandidate]:
        """Extract based on text formatting (font size, bold, etc.)"""
        candidates = []
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if "lines" not in block:
                    continue

                for line in block["lines"]:
                    line_text = ""
                    avg_font_size = 0
                    is_bold = False
                    font_count = 0

                    for span in line["spans"]:
                        line_text += span["text"]
                        avg_font_size += span["size"]
                        is_bold = is_bold or (span["flags"] & 2 ** 4)
                        font_count += 1

                    if font_count > 0:
                        avg_font_size /= font_count

                    line_text = line_text.strip()
                    if (len(line_text) > 3 and len(line_text) < 100 and
                        (avg_font_size > 12 or is_bold) and
                        self._looks_like_header(line_text)):

                        clean_topic = self._clean_topic_text(line_text)
                        if clean_topic and self._is_valid_topic(clean_topic):
                            confidence = min(0.8, 0.5 + (avg_font_size - 10) * 0.05 + (0.2 if is_bold else 0))
                            candidates.append(TopicCandidate(
                                text=clean_topic,
                                page=page_num + 1,
                                confidence=confidence,
                                extraction_method='formatting',
                                context=f'font_size_{avg_font_size:.1f}_bold_{is_bold}',
                                position='header'
                            ))

        print(f"🎨 Formatting candidates: {len(candidates)}")
        return candidates

    def _extract_with_context(self) -> List[TopicCandidate]:
        """Extract using contextual analysis around topic markers"""
        candidates = []
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            text = page.get_text()
            lines = text.split('\n')

            for i, line in enumerate(lines):
                line = line.strip()
                if self._has_topic_indicators(line):
                    context_lines = []
                    for j in range(max(0, i-2), min(len(lines), i+3)):
                        if lines[j].strip():
                            context_lines.append(lines[j].strip())

                    context_text = ' '.join(context_lines)
                    potential_topics = self._extract_topics_from_context(context_text)

                    for topic in potential_topics:
                        clean_topic = self._clean_topic_text(topic)
                        if clean_topic and self._is_valid_topic(clean_topic):
                            confidence = 0.6
                            candidates.append(TopicCandidate(
                                text=clean_topic,
                                page=page_num + 1,
                                confidence=confidence,
                                extraction_method='context',
                                context='contextual_analysis',
                                position='body'
                            ))

        print(f"🔍 Context candidates: {len(candidates)}")
        return candidates

    def _score_candidates(self, candidates: List[TopicCandidate]) -> List[TopicCandidate]:
        """Score candidates based on multiple factors"""
        for candidate in candidates:
            base_confidence = candidate.confidence
            quality_boost = 0
            text_lower = candidate.text.lower()

            for keyword in self.quality_indicators['high_value']:
                if keyword in text_lower:
                    quality_boost += 0.1

            for keyword in self.quality_indicators['domain_specific']:
                if keyword in text_lower:
                    quality_boost += 0.05

            for keyword in self.quality_indicators['structural']:
                if keyword in text_lower:
                    quality_boost += 0.08

            # Reduced length penalty to allow shorter topics
            length_penalty = 0
            if len(candidate.text) < 5:
                length_penalty = 0.1
            elif len(candidate.text) > 80:
                length_penalty = 0.1

            candidate.confidence = min(1.0, base_confidence + quality_boost - length_penalty)

        candidates.sort(key=lambda x: x.confidence, reverse=True)
        return candidates

    def _deduplicate_and_finalize(self, candidates: List[TopicCandidate]) -> List[Dict]:
        """Remove duplicates and create final topic list"""
        seen_topics = set()
        final_topics = []

        for candidate in candidates:
            normalized = re.sub(r'\s+', ' ', candidate.text.lower().strip())
            if normalized not in seen_topics and candidate.confidence >= 0.3:
                seen_topics.add(normalized)
                final_topics.append({
                    'topic': candidate.text,
                    'page': candidate.page,
                    'confidence': round(candidate.confidence, 3),
                    'extraction_method': candidate.extraction_method,
                    'context': candidate.context,
                    'position': candidate.position
                })

        final_topics.sort(key=lambda x: x['page'])
        return final_topics

    def _filter_by_keywords(self, topics: List[Dict]) -> List[Dict]:
        """Enhanced filter topics by removing those containing problematic keywords and phrases"""
        print("🔍 Starting enhanced keyword-based filtering...")
        filtered_topics = []
        filtered_count = {'example': 0, 'concluding': 0, 'excluded': 0, 'pattern': 0, 'kept': 0}

        for topic_dict in topics:
            topic_text = topic_dict['topic'].lower()
            should_filter = False
            filter_reason = ""

            # Check for example keywords
            for keyword in self.example_keywords:
                if keyword.lower() in topic_text:
                    should_filter = True
                    filter_reason = f"contains_example_keyword: '{keyword}'"
                    filtered_count['example'] += 1
                    break

            # Check for concluding keywords if not already filtered
            if not should_filter:
                for keyword in self.concluding_keywords:
                    if keyword.lower() in topic_text:
                        should_filter = True
                        filter_reason = f"contains_concluding_keyword: '{keyword}'"
                        filtered_count['concluding'] += 1
                        break

            # Check for exclusion phrases if not already filtered
            if not should_filter:
                for phrase in self.exclusion_phrases:
                    if phrase.lower() in topic_text:
                        should_filter = True
                        filter_reason = f"contains_exclusion_phrase: '{phrase}'"
                        filtered_count['excluded'] += 1
                        break

            # Check for exclusion patterns if not already filtered
            if not should_filter:
                for pattern in self.exclusion_patterns:
                    if re.match(pattern, topic_text, re.IGNORECASE):
                        should_filter = True
                        filter_reason = f"matches_exclusion_pattern: '{pattern}'"
                        filtered_count['pattern'] += 1
                        break

            if not should_filter:
                filtered_topics.append(topic_dict)
                filtered_count['kept'] += 1

        total_original = len(topics)
        print(f"✅ Enhanced keyword filtering complete:")
        print(f" 📊 Original topics: {total_original}")
        print(f" 🚫 Filtered by example keywords: {filtered_count['example']}")
        print(f" 🚫 Filtered by concluding keywords: {filtered_count['concluding']}")
        print(f" 🚫 Filtered by exclusion phrases: {filtered_count['excluded']}")
        print(f" 🚫 Filtered by exclusion patterns: {filtered_count['pattern']}")
        print(f" ✅ Topics kept: {filtered_count['kept']}")
        print(f" 📈 Retention rate: {(filtered_count['kept']/total_original)*100:.1f}%")

        return filtered_topics

    def _filter_by_negative_patterns(self, topics: List[Dict]) -> List[Dict]:
        """Filter topics using negative patterns for data fragments and unwanted content"""
        print("🚫 Starting negative pattern filtering...")
        filtered_topics = []
        filtered_count = {'negative_pattern': 0, 'kept': 0}

        for topic_dict in topics:
            topic_text = topic_dict['topic']
            should_filter = False
            filter_reason = ""

            # Check for negative patterns
            for pattern in self.negative_filters:
                if re.search(pattern, topic_text, re.IGNORECASE):
                    should_filter = True
                    filter_reason = f"matches_negative_pattern: '{pattern}'"
                    filtered_count['negative_pattern'] += 1
                    break

            if not should_filter:
                filtered_topics.append(topic_dict)
                filtered_count['kept'] += 1

        total_original = len(topics)
        print(f"✅ Negative pattern filtering complete:")
        print(f" 📊 Original topics: {total_original}")
        print(f" 🚫 Filtered by negative patterns: {filtered_count['negative_pattern']}")
        print(f" ✅ Topics kept: {filtered_count['kept']}")
        print(f" 📈 Retention rate: {(filtered_count['kept']/total_original)*100:.1f}%")

        return filtered_topics

    def _filter_by_quality(self, topics: List[Dict]) -> List[Dict]:
        """Additional quality filter based on topic characteristics"""
        print("🎯 Starting quality-based filtering...")
        filtered_topics = []
        filtered_count = {'low_quality': 0, 'kept': 0}

        for topic_dict in topics:
            topic_text = topic_dict['topic']
            should_filter = False
            
            # Filter very short topics (reduced threshold)
            if len(topic_text.strip()) < 4:
                should_filter = True
                filtered_count['low_quality'] += 1
            
            # Filter topics that are mostly numbers or symbols
            elif len(re.sub(r'[^a-zA-Z]', '', topic_text)) < len(topic_text) * 0.4:
                should_filter = True
                filtered_count['low_quality'] += 1
            
            # Filter topics with too many repetitive characters
            elif len(set(topic_text.lower())) < len(topic_text) * 0.25:
                should_filter = True
                filtered_count['low_quality'] += 1

            if not should_filter:
                filtered_topics.append(topic_dict)
                filtered_count['kept'] += 1

        total_original = len(topics)
        print(f"✅ Quality filtering complete:")
        print(f" 📊 Original topics: {total_original}")
        print(f" 🚫 Filtered by quality: {filtered_count['low_quality']}")
        print(f" ✅ Topics kept: {filtered_count['kept']}")
        print(f" 📈 Retention rate: {(filtered_count['kept']/total_original)*100:.1f}%")

        return filtered_topics

    def _filter_by_gpt_two_stage_balanced(self, topics: List[Dict]) -> List[Dict]:
        """
        NEW: 2-Stage GPT filtering with balanced, shorter prompts
        Stage 1: Educational content filtering (keep educational topics)
        Stage 2: Quality refinement filtering (keep high-quality topics)
        """
        if not topics:
            return topics

        print(f"🎯 Starting BALANCED 2-STAGE GPT filtering for {len(topics)} topics...")

        # Stage 1: Educational content filtering
        print(f"\n📚 STAGE 1: Educational Content Filtering")
        print(f"🎯 Goal: Keep educational topics, remove obvious non-topics")
        stage1_topics = self._filter_by_gpt_stage1_balanced(topics)

        if not stage1_topics:
            print(f"⚠️ No topics survived Stage 1 filtering")
            return []

        print(f"\n🎯 Stage 1 Complete: {len(stage1_topics)} educational topics kept")

        # Stage 2: Quality refinement filtering 
        print(f"\n📖 STAGE 2: Quality Refinement Filtering")
        print(f"🎯 Goal: Keep high-quality curriculum topics")
        stage2_topics = self._filter_by_gpt_stage2_balanced(stage1_topics)

        total_original = len(topics)
        total_final = len(stage2_topics)
        stage1_retention = (len(stage1_topics) / total_original) * 100 if total_original > 0 else 0
        overall_retention = (total_final / total_original) * 100 if total_original > 0 else 0

        print(f"\n🏆 BALANCED 2-STAGE GPT FILTERING COMPLETE:")
        print(f"   📊 Original topics: {total_original}")
        print(f"   📚 After Stage 1 (Educational): {len(stage1_topics)} ({stage1_retention:.1f}% retention)")
        print(f"   📖 After Stage 2 (Quality): {total_final} ({overall_retention:.1f}% overall retention)")

        return stage2_topics

    def _filter_by_gpt_stage1_balanced(self, topics: List[Dict]) -> List[Dict]:
        """Stage 1: Balanced educational content filtering"""
        if not topics:
            return topics

        print(f"🤖 Stage 1 GPT filtering for {len(topics)} topics...")

        # Initialize LLM client
        try:
            from LLM import AdvancedAzureLLM
            llm = AdvancedAzureLLM()
            llm.switch_model("gpt-5-mini")
        except Exception as e:
            print(f"⚠️ Could not initialize GPT client: {e}")
            return topics

        return asyncio.run(self._process_stage1_batches(topics, llm))

    def _filter_by_gpt_stage2_balanced(self, topics: List[Dict]) -> List[Dict]:
        """Stage 2: Balanced quality refinement filtering"""
        if not topics:
            return topics

        print(f"🤖 Stage 2 GPT filtering for {len(topics)} topics...")

        # Initialize LLM client
        try:
            from LLM import AdvancedAzureLLM
            llm = AdvancedAzureLLM()
            llm.switch_model("gpt-5-mini")
        except Exception as e:
            print(f"⚠️ Could not initialize GPT client: {e}")
            return topics

        return asyncio.run(self._process_stage2_batches(topics, llm))

    async def _process_stage1_batches(self, topics: List[Dict], llm) -> List[Dict]:
        """Process Stage 1 batches with balanced filtering"""
        batch_size = 50
        batches = [topics[i:i + batch_size] for i in range(0, len(topics), batch_size)]

        print(f"🚀 Stage 1: Processing {len(batches)} batches in parallel...")

        tasks = []
        for batch_idx, batch in enumerate(batches):
            task = self._process_stage1_batch(batch, batch_idx, llm)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        all_filtered_topics = []
        total_kept = 0
        successful_batches = 0

        for batch_idx, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"⚠️ Stage 1 Error in batch {batch_idx + 1}: {result}")
                # Liberal fallback for Stage 1
                batch = batches[batch_idx]
                for topic_dict in batch:
                    topic_dict['gpt_stage1_filtered'] = False
                    topic_dict['stage1_batch_id'] = batch_idx + 1
                    all_filtered_topics.append(topic_dict)
                total_kept += len(batch)
            else:
                filtered_batch_topics, kept_count = result
                all_filtered_topics.extend(filtered_batch_topics)
                total_kept += kept_count
                successful_batches += 1

        total_original = len(topics)
        retention_rate = (total_kept / total_original) * 100 if total_original > 0 else 0

        print(f"🎯 Stage 1 GPT filtering complete:")
        print(f"   📊 Input topics: {total_original}")
        print(f"   ✅ Educational topics kept: {total_kept}")
        print(f"   🚀 Successful batches: {successful_batches}/{len(batches)}")
        print(f"   📈 Retention rate: {retention_rate:.1f}%")

        return all_filtered_topics

    async def _process_stage2_batches(self, topics: List[Dict], llm) -> List[Dict]:
        """Process Stage 2 batches with balanced filtering"""
        batch_size = 40
        batches = [topics[i:i + batch_size] for i in range(0, len(topics), batch_size)]

        print(f"🚀 Stage 2: Processing {len(batches)} batches in parallel...")

        tasks = []
        for batch_idx, batch in enumerate(batches):
            task = self._process_stage2_batch(batch, batch_idx, llm)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        all_filtered_topics = []
        total_kept = 0
        successful_batches = 0

        for batch_idx, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"⚠️ Stage 2 Error in batch {batch_idx + 1}: {result}")
                # Conservative fallback for Stage 2
                batch = batches[batch_idx]
                for topic_dict in batch:
                    if topic_dict.get('confidence', 0) > 0.6:  # Keep higher confidence topics
                        topic_dict['gpt_stage2_filtered'] = False
                        topic_dict['stage2_batch_id'] = batch_idx + 1
                        all_filtered_topics.append(topic_dict)
                        total_kept += 1
            else:
                filtered_batch_topics, kept_count = result
                all_filtered_topics.extend(filtered_batch_topics)
                total_kept += kept_count
                successful_batches += 1

        total_original = len(topics)
        retention_rate = (total_kept / total_original) * 100 if total_original > 0 else 0

        print(f"🎯 Stage 2 GPT filtering complete:")
        print(f"   📊 Input topics: {total_original}")
        print(f"   ✅ High-quality topics kept: {total_kept}")
        print(f"   🚀 Successful batches: {successful_batches}/{len(batches)}")
        print(f"   📈 Retention rate: {retention_rate:.1f}%")

        return all_filtered_topics

    async def _process_stage1_batch(self, batch: List[Dict], batch_idx: int, llm) -> tuple:
        """Process Stage 1 batch: Keep educational content, remove obvious non-topics"""
        print(f"🔄 Stage 1 - Processing batch {batch_idx + 1} ({len(batch)} topics)...")

        topics_text = ""
        for i, topic_dict in enumerate(batch):
            topic_text = topic_dict['topic']
            page_num = topic_dict.get('page', 'Unknown')
            topics_text += f"{i}: \"{topic_text}\" (Page {page_num})\n"

        # BALANCED STAGE 1 PROMPT - Conservative approach
        system_message = """You are an educational content filter. Stage 1: Remove obvious non-topics.

KEEP educational content like:
- Chapter titles, section headings
- Definitions, theorems, concepts  
- Methods, principles, theories
- Educational topics and curriculum content

REMOVE obvious non-topics like:
- Specific examples with data ("Example 3.2a: City populations")
- Figure/table references ("Figure 4.1", "Table 2.3")
- Navigation text, page numbers, headers/footers
- Data fragments, measurement lists
- Publishing information

Be conservative - when uncertain, keep it. Focus on removing clearly non-educational content.

Return JSON array of indices to keep: [0, 2, 5, 8]"""

        prompt = f"Stage 1: Keep educational topics, remove obvious non-topics from these {len(batch)} items:\n\n{topics_text}"

        try:
            response = await llm.async_generate(
                prompt=prompt,
                system_message=system_message,
                model_name="gpt-5-mini"
            )

            response = response.strip()
            
            try:
                if response.startswith('[') and response.endswith(']'):
                    keep_indices = json.loads(response)
                else:
                    json_match = re.search(r'\[([\d,\s]+)\]', response)
                    if json_match:
                        keep_indices = json.loads(json_match.group(0))
                    else:
                        print(f"⚠️ Stage 1: Could not parse response for batch {batch_idx + 1}, keeping all")
                        keep_indices = list(range(len(batch)))

                filtered_batch_topics = []
                for idx in keep_indices:
                    if 0 <= idx < len(batch):
                        topic_dict = batch[idx].copy()
                        topic_dict['gpt_stage1_filtered'] = True
                        topic_dict['stage1_batch_id'] = batch_idx + 1
                        filtered_batch_topics.append(topic_dict)

                print(f"✅ Stage 1 Batch {batch_idx + 1}: kept {len(keep_indices)}/{len(batch)} topics")
                return filtered_batch_topics, len(keep_indices)

            except json.JSONDecodeError as e:
                print(f"⚠️ Stage 1 JSON error for batch {batch_idx + 1}: {e}")
                # Liberal fallback for Stage 1
                fallback_topics = []
                for topic_dict in batch:
                    topic_dict['gpt_stage1_filtered'] = False
                    topic_dict['stage1_batch_id'] = batch_idx + 1
                    fallback_topics.append(topic_dict)
                return fallback_topics, len(batch)

        except Exception as e:
            print(f"⚠️ Stage 1 error processing batch {batch_idx + 1}: {e}")
            fallback_topics = []
            for topic_dict in batch:
                topic_dict['gpt_stage1_filtered'] = False
                topic_dict['stage1_batch_id'] = batch_idx + 1
                fallback_topics.append(topic_dict)
            return fallback_topics, len(batch)

    async def _process_stage2_batch(self, batch: List[Dict], batch_idx: int, llm) -> tuple:
        """Process Stage 2 batch: Keep high-quality curriculum topics"""
        print(f"🔄 Stage 2 - Processing batch {batch_idx + 1} ({len(batch)} topics)...")

        topics_text = ""
        for i, topic_dict in enumerate(batch):
            topic_text = topic_dict['topic']
            page_num = topic_dict.get('page', 'Unknown')
            confidence = topic_dict.get('confidence', 0)
            topics_text += f"{i}: \"{topic_text}\" (Page {page_num}, Conf: {confidence:.2f})\n"

        # BALANCED STAGE 2 PROMPT - Quality focused but reasonable
        system_message = """You are a curriculum quality filter. Stage 2: Select high-quality educational topics.

KEEP high-quality topics like:
- Main chapter/section titles with educational value
- Important definitions, key theorems, core concepts
- Fundamental methods, algorithms, principles
- Topics that would be in a course outline or textbook index
- Essential curriculum content students should learn

REMOVE lower-quality items like:
- Very specific subtopics or minor subsections
- Redundant or repetitive topics
- Topics that are too narrow or specialized
- Implementation details rather than concepts
- Topics with very low confidence scores

Aim for topics that represent the core educational content. Be selective but reasonable.

Return JSON array of indices to keep: [0, 2, 5, 8]"""

        prompt = f"Stage 2: Select high-quality curriculum topics from these {len(batch)} educational items:\n\n{topics_text}"

        try:
            response = await llm.async_generate(
                prompt=prompt,
                system_message=system_message,
                model_name="gpt-5-mini"
            )

            response = response.strip()
            
            try:
                if response.startswith('[') and response.endswith(']'):
                    keep_indices = json.loads(response)
                else:
                    json_match = re.search(r'\[([\d,\s]+)\]', response)
                    if json_match:
                        keep_indices = json.loads(json_match.group(0))
                    else:
                        print(f"⚠️ Stage 2: Could not parse response for batch {batch_idx + 1}, using confidence fallback")
                        # Conservative fallback - keep high confidence topics
                        keep_indices = [i for i, topic in enumerate(batch) if topic.get('confidence', 0) > 0.6]

                filtered_batch_topics = []
                for idx in keep_indices:
                    if 0 <= idx < len(batch):
                        topic_dict = batch[idx].copy()
                        topic_dict['gpt_stage2_filtered'] = True
                        topic_dict['stage2_batch_id'] = batch_idx + 1
                        filtered_batch_topics.append(topic_dict)

                print(f"✅ Stage 2 Batch {batch_idx + 1}: kept {len(keep_indices)}/{len(batch)} topics")
                return filtered_batch_topics, len(keep_indices)

            except json.JSONDecodeError as e:
                print(f"⚠️ Stage 2 JSON error for batch {batch_idx + 1}: {e}")
                # Conservative fallback for Stage 2
                fallback_topics = []
                for i, topic_dict in enumerate(batch):
                    if topic_dict.get('confidence', 0) > 0.6:
                        topic_dict['gpt_stage2_filtered'] = False
                        topic_dict['stage2_batch_id'] = batch_idx + 1
                        fallback_topics.append(topic_dict)
                return fallback_topics, len(fallback_topics)

        except Exception as e:
            print(f"⚠️ Stage 2 error processing batch {batch_idx + 1}: {e}")
            # Conservative fallback for Stage 2
            fallback_topics = []
            for i, topic_dict in enumerate(batch):
                if topic_dict.get('confidence', 0) > 0.6:
                    topic_dict['gpt_stage2_filtered'] = False  
                    topic_dict['stage2_batch_id'] = batch_idx + 1
                    fallback_topics.append(topic_dict)
            return fallback_topics, len(fallback_topics)

    # Helper methods remain the same but with relaxed constraints
    def _clean_topic_text(self, text: str) -> str:
        """Advanced text cleaning"""
        if not text:
            return ""

        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'\s*\(Page\s+\d+\).*$', '', text, re.IGNORECASE)
        text = re.sub(r'\s*\.{3,}.*$', '', text)
        text = re.sub(r'\s*….*$', '', text)
        text = re.sub(r'\s+([,.;:])', r'\1', text)
        text = re.sub(r'([,.;:])\s*$', '', text)

        return text.strip()

    def _is_valid_topic(self, text: str) -> bool:
        """Enhanced topic validation with relaxed constraints"""
        if not text or len(text) < 3 or len(text) > 120:
            return False

        invalid_patterns = [
            r'^\d+\s*$',
            r'^[A-Z]\s*$',
            r'^(page|fig|figure|table|chart)\s+\d+',
            r'^(www\.|http|\.com|\.org|email|@)',
            r'^(copyright|isbn|©|\(c\))',
        ]

        for pattern in invalid_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False

        return True

    def _calculate_confidence(self, text: str, category: str, context: str) -> float:
        """Calculate confidence score for a topic"""
        base_confidence = {
            'numbered_sections': 0.8,
            'header_detection': 0.7,
            'content_markers': 0.6
        }.get(category, 0.5)

        text_lower = text.lower()
        if any(kw in text_lower for kw in self.quality_indicators['high_value']):
            base_confidence += 0.1

        return min(1.0, base_confidence)

    def _looks_like_header(self, text: str) -> bool:
        """Check if text looks like a header"""
        header_patterns = [
            r'^\d+\.\d+',
            r'^(chapter|section|appendix)\s+\d+',
            r'^[A-Z][A-Z\s]{8,}$',
            r'^(example|definition|theorem|problem)\s+\d+',
        ]

        for pattern in header_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True

        return False

    def _has_topic_indicators(self, line: str) -> bool:
        """Check if line contains topic boundary indicators"""
        indicators = [
            'example', 'definition', 'theorem', 'lemma', 'corollary',
            'problem', 'exercise', 'solution', 'proof', 'remark'
        ]

        return any(indicator in line.lower() for indicator in indicators)

    def _extract_topics_from_context(self, context_text: str) -> List[str]:
        """Extract topics from contextual text"""
        topics = []
        patterns = [
            r'(\d+\.\d+[^\n.!?]{8,60})',
            r'(EXAMPLE\s+\d+\.\d+[a-z]?[^\n.!?]{5,60})',
            r'(DEFINITION\s+\d+\.\d+[^\n.!?]{5,60})',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, context_text, re.IGNORECASE)
            topics.extend(matches)

        return topics

    def save_results(self, topics: List[Dict]) -> Dict[str, str]:
        """Save extraction results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)

        json_file = os.path.join(output_dir, f"enhanced_extraction_{timestamp}.json")
        
        result_data = {
            'metadata': {
                'extraction_date': timestamp,
                'source_file': self.pdf_path,
                'total_pages': len(self.doc),
                'total_topics': len(topics),
                'extraction_method': 'enhanced_multi_strategy_with_balanced_2stage_gpt_filtering',
                'strategies_used': ['toc', 'content_pattern', 'formatting', 'context', 
                                  'enhanced_keyword_filtering', 'negative_pattern_filtering',
                                  'quality_filtering', 'balanced_2stage_gpt_filtering'],
                'confidence_threshold': 0.3,
                'filtering_enabled': True,
                'parallel_processing': True,
                'batch_size_stage1': 50,
                'batch_size_stage2': 40
            },
            'topics': topics,
            'statistics': {
                'avg_confidence': sum(t['confidence'] for t in topics) / len(topics) if topics else 0,
                'method_breakdown': Counter(t['extraction_method'] for t in topics),
                'confidence_distribution': {
                    'high (>0.8)': len([t for t in topics if t['confidence'] > 0.8]),
                    'medium (0.6-0.8)': len([t for t in topics if 0.6 <= t['confidence'] <= 0.8]),
                    'low (0.3-0.6)': len([t for t in topics if 0.3 <= t['confidence'] < 0.6])
                }
            }
        }

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Enhanced extraction results saved: {json_file}")
        return {'json_file': json_file}


def main():
    """Main execution"""
    pdf_path = "doc/book2.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return

    print("🚀 Enhanced Advanced Multi-Strategy Topic Extractor with Balanced 2-Stage GPT Processing")
    print("=" * 95)
    print("✅ Enhanced with negative filters, shorter topics support, and balanced 2-stage GPT filtering")
    print()

    extractor = AdvancedMultiStrategyExtractor(pdf_path)
    topics = extractor.extract_with_multiple_strategies()

    if topics:
        files = extractor.save_results(topics)
        print(f"\n🎉 SUCCESS! Extracted {len(topics)} topics")
        print(f"📈 Average confidence: {sum(t['confidence'] for t in topics) / len(topics):.3f}")

        # Show extraction method breakdown
        method_counts = Counter(t['extraction_method'] for t in topics)
        print(f"\n📊 Extraction method breakdown:")
        for method, count in method_counts.items():
            print(f" {method}: {count} topics")

        # Show sample high-confidence topics
        high_conf_topics = [t for t in topics if t['confidence'] > 0.6]
        print(f"\n📋 Sample high-confidence topics ({len(high_conf_topics)} total):")
        for i, topic in enumerate(high_conf_topics[:20], 1):
            print(f" {i:2d}. {topic['topic']} (Page {topic['page']}, Conf: {topic['confidence']:.3f})")

        if len(high_conf_topics) > 20:
            print(f" ... and {len(high_conf_topics) - 20} more high-confidence topics")

    else:
        print("❌ No topics extracted")


if __name__ == "__main__":
    main()

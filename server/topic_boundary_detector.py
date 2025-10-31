#!/usr/bin/env python3
"""
🎯 Topic Boundary Detection System
==================================
Independent system to identify precise topic boundaries in PDF textbooks using vector embeddings.

Features:
- Vector embedding-based similarity analysis
- Semantic topic boundary detection
- Chunk-by-chunk content analysis
- Visual boundary visualization
- Export boundary data for other systems

Dependencies (install if needed):
    pip install sentence-transformers scikit-learn matplotlib seaborn

Usage:
    python topic_boundary_detector.py
"""

import os
import re
import json
import fitz  # PyMuPDF
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
import warnings
warnings.filterwarnings('ignore')

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import matplotlib.pyplot as plt
    import seaborn as sns
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Missing dependencies: {e}")
    print("📦 Install with: pip install sentence-transformers scikit-learn matplotlib seaborn")
    DEPENDENCIES_AVAILABLE = False

# Optional LLM integration
try:
    from LLM import AdvancedAzureLLM
    LLM_AVAILABLE = True
except ImportError:
    print("ℹ️  LLM.py not found - running without AI enhancement")
    LLM_AVAILABLE = False

# Vector Store integration
try:
    from db.vector_store import get_vector_store
    VECTOR_STORE_AVAILABLE = True
except ImportError:
    print("ℹ️  Vector store not available - running without vector storage")
    VECTOR_STORE_AVAILABLE = False

@dataclass
class TopicChunk:
    """Represents a chunk of text within a topic"""
    chunk_id: int
    page_num: int
    start_pos: int
    end_pos: int
    text: str
    clean_text: str
    embedding: Optional[np.ndarray] = None
    similarity_to_prev: Optional[float] = None
    
@dataclass
class TopicBoundary:
    """Represents detected topic boundaries"""
    topic_title: str
    start_page: int
    end_page: int
    start_chunk_id: int
    end_chunk_id: int
    confidence: float
    boundary_type: str  # 'semantic_drop', 'chapter_marker', 'section_header', etc.
    content_summary: str = ""

class TopicBoundaryDetector:
    """
    Advanced topic boundary detection using vector embeddings and semantic analysis
    """
    
    def __init__(self, pdf_path: str, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the boundary detector
        
        Args:
            pdf_path: Path to the PDF file
            model_name: Sentence transformer model to use for embeddings
        """
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("Required dependencies not available. Please install them first.")
            
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.model_name = model_name
        self.embedding_model = None
        
        # Configuration
        self.chunk_size = 300  # Words per chunk
        self.chunk_overlap = 50  # Words overlap between chunks
        self.similarity_threshold = 0.65  # Below this = likely new topic
        self.min_topic_chunks = 3  # Minimum chunks for a topic
        self.page_break_penalty = 0.05  # Reduce similarity across page breaks
        
        # Data storage
        self.chunks: List[TopicChunk] = []
        self.boundaries: List[TopicBoundary] = []
        self.topics_from_extraction: List[Dict] = []
        
        # Optional LLM
        self.llm = None
        if LLM_AVAILABLE:
            try:
                self.llm = AdvancedAzureLLM()
                print("✅ LLM integration enabled for enhanced analysis")
            except Exception as e:
                print(f"⚠️  LLM initialization failed: {e}")
        
        print(f"🎯 Topic Boundary Detector initialized")
        print(f"📖 PDF: {os.path.basename(pdf_path)} ({len(self.doc)} pages)")
        
    def initialize_embedding_model(self):
        """Initialize the sentence transformer model"""
        if self.embedding_model is None:
            print(f"🧠 Loading embedding model: {self.model_name}")
            self.embedding_model = SentenceTransformer(self.model_name)
            print("✅ Embedding model loaded successfully")
            
    def load_extracted_topics(self, topics_file: Optional[str] = None) -> bool:
        """
        Load previously extracted topics to guide boundary detection
        
        Args:
            topics_file: JSON file with extracted topics, or None to find latest
        """
        if topics_file is None:
            # Find the latest topic extraction file
            output_dir = "output"
            if not os.path.exists(output_dir):
                print("⚠️  No output directory found - running without topic guidance")
                return False
                
            topic_files = [f for f in os.listdir(output_dir) 
                          if ('optimized_universal' in f or 'topics' in f) and f.endswith('.json')]
            
            if not topic_files:
                print("⚠️  No topic extraction files found - running without guidance")
                return False
                
            topic_files.sort(reverse=True)
            topics_file = os.path.join(output_dir, topic_files[0])
            
        try:
            with open(topics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Handle different topic file formats
            if 'topics' in data:
                self.topics_from_extraction = data['topics']
            elif isinstance(data, list):
                self.topics_from_extraction = data
            else:
                print(f"⚠️  Unknown topic file format in {topics_file}")
                return False
                
            print(f"📚 Loaded {len(self.topics_from_extraction)} topics from: {os.path.basename(topics_file)}")
            
            # Show sample topics
            if self.topics_from_extraction:
                print("📋 Sample topics for boundary detection:")
                for i, topic in enumerate(self.topics_from_extraction[:5]):
                    title = topic.get('title', topic.get('topic', 'Unknown'))
                    page = topic.get('page', 'Unknown')
                    print(f"   {i+1}. {title} (Page {page})")
                    
            return True
            
        except Exception as e:
            print(f"❌ Error loading topics: {e}")
            return False
            
    def extract_text_chunks(self, start_page: int = 1, end_page: Optional[int] = None) -> List[TopicChunk]:
        """
        Extract text chunks from PDF for boundary analysis
        
        Args:
            start_page: Starting page number (1-indexed)
            end_page: Ending page number (1-indexed), or None for all pages
        """
        if end_page is None:
            end_page = len(self.doc)
            
        print(f"📝 Extracting text chunks from pages {start_page} to {end_page}")
        
        chunks = []
        chunk_id = 0
        
        for page_num in range(start_page - 1, min(end_page, len(self.doc))):
            page = self.doc[page_num]
            full_text = page.get_text()
            
            if not full_text.strip():
                continue
                
            # Clean the text
            clean_text = self.clean_text_for_analysis(full_text)
            words = clean_text.split()
            
            if len(words) < self.chunk_size // 2:
                # Small page, treat as single chunk
                if words:
                    chunk = TopicChunk(
                        chunk_id=chunk_id,
                        page_num=page_num + 1,
                        start_pos=0,
                        end_pos=len(full_text),
                        text=full_text,
                        clean_text=clean_text
                    )
                    chunks.append(chunk)
                    chunk_id += 1
            else:
                # Split into overlapping chunks
                for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
                    chunk_words = words[i:i + self.chunk_size]
                    if len(chunk_words) < 50:  # Skip very small chunks
                        continue
                        
                    chunk_text = ' '.join(chunk_words)
                    
                    chunk = TopicChunk(
                        chunk_id=chunk_id,
                        page_num=page_num + 1,
                        start_pos=i,
                        end_pos=i + len(chunk_words),
                        text=chunk_text,
                        clean_text=chunk_text
                    )
                    chunks.append(chunk)
                    chunk_id += 1
                    
        print(f"✅ Extracted {len(chunks)} text chunks")
        return chunks
        
    def clean_text_for_analysis(self, text: str) -> str:
        """Clean text for better embedding analysis"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers, headers, footers patterns
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^Chapter \d+.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^Page \d+.*$', '', text, flags=re.MULTILINE)
        
        # Remove excessive punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]]+', ' ', text)
        
        # Clean up spacing
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
        
    def compute_embeddings(self, chunks: List[TopicChunk]) -> List[TopicChunk]:
        """Compute embeddings for all chunks"""
        if not chunks:
            return chunks
            
        self.initialize_embedding_model()
        
        print(f"🧮 Computing embeddings for {len(chunks)} chunks...")
        
        # Extract texts for batch processing
        texts = [chunk.clean_text for chunk in chunks]
        
        # Compute embeddings in batches for efficiency
        batch_size = 32
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = self.embedding_model.encode(batch_texts, show_progress_bar=False)
            all_embeddings.extend(batch_embeddings)
            
            if i % (batch_size * 10) == 0 and i > 0:
                print(f"   Processed {i}/{len(texts)} chunks...")
                
        # Assign embeddings to chunks
        for chunk, embedding in zip(chunks, all_embeddings):
            chunk.embedding = embedding
            
        print("✅ Embeddings computed successfully")
        return chunks
        
    def compute_similarities(self, chunks: List[TopicChunk]) -> List[TopicChunk]:
        """Compute similarities between consecutive chunks"""
        print("📊 Computing chunk-to-chunk similarities...")
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            curr_chunk = chunks[i]
            
            if prev_chunk.embedding is not None and curr_chunk.embedding is not None:
                # Compute cosine similarity
                similarity = cosine_similarity(
                    prev_chunk.embedding.reshape(1, -1),
                    curr_chunk.embedding.reshape(1, -1)
                )[0][0]
                
                # Apply page break penalty
                if prev_chunk.page_num != curr_chunk.page_num:
                    similarity -= self.page_break_penalty
                    
                curr_chunk.similarity_to_prev = float(similarity)
            else:
                curr_chunk.similarity_to_prev = 0.0
                
        print("✅ Similarities computed")
        return chunks
        
    def detect_boundaries_from_similarity(self, chunks: List[TopicChunk]) -> List[Dict]:
        """Detect topic boundaries based on similarity drops"""
        print("🎯 Detecting boundaries from similarity analysis...")
        
        boundaries = []
        
        # Find significant similarity drops
        for i in range(1, len(chunks)):
            chunk = chunks[i]
            similarity = chunk.similarity_to_prev or 0.0
            
            if similarity < self.similarity_threshold:
                # Potential boundary detected
                boundary = {
                    'chunk_id': i,
                    'page_num': chunk.page_num,
                    'similarity_drop': self.similarity_threshold - similarity,
                    'confidence': min(1.0, (self.similarity_threshold - similarity) * 2),
                    'type': 'semantic_similarity_drop'
                }
                boundaries.append(boundary)
                
        print(f"🔍 Found {len(boundaries)} potential boundaries from similarity analysis")
        return boundaries
        
    def enhance_boundaries_with_topic_knowledge(self, boundaries: List[Dict]) -> List[Dict]:
        """Enhance boundary detection using known topic information"""
        if not self.topics_from_extraction:
            return boundaries
            
        print("🧠 Enhancing boundaries with topic knowledge...")
        
        enhanced_boundaries = []
        
        for boundary in boundaries:
            enhanced = boundary.copy()
            
            # Check if boundary aligns with known topics
            page_num = boundary['page_num']
            
            # Find topics near this page
            nearby_topics = [
                topic for topic in self.topics_from_extraction
                if abs(topic.get('page', 0) - page_num) <= 2
            ]
            
            if nearby_topics:
                # Boost confidence if near known topic
                enhanced['confidence'] = min(1.0, enhanced['confidence'] + 0.2)
                enhanced['nearby_topics'] = [
                    topic.get('title', topic.get('topic', 'Unknown'))
                    for topic in nearby_topics
                ]
                enhanced['topic_guided'] = True
            else:
                enhanced['topic_guided'] = False
                
            enhanced_boundaries.append(enhanced)
            
        print(f"✅ Enhanced {len(enhanced_boundaries)} boundaries with topic knowledge")
        return enhanced_boundaries
        
    def filter_and_merge_boundaries(self, boundaries: List[Dict]) -> List[Dict]:
        """Filter weak boundaries and merge nearby ones"""
        print("🔧 Filtering and merging boundaries...")
        
        # Sort by chunk ID
        boundaries.sort(key=lambda x: x['chunk_id'])
        
        # Filter by confidence
        high_confidence = [b for b in boundaries if b['confidence'] >= 0.3]
        
        print(f"📊 Filtered to {len(high_confidence)} high-confidence boundaries")
        
        # Merge nearby boundaries (within 5 chunks)
        merged = []
        i = 0
        while i < len(high_confidence):
            current = high_confidence[i]
            
            # Look for nearby boundaries to merge
            merge_candidates = [current]
            j = i + 1
            while (j < len(high_confidence) and 
                   high_confidence[j]['chunk_id'] - current['chunk_id'] <= 5):
                merge_candidates.append(high_confidence[j])
                j += 1
                
            # Create merged boundary
            if len(merge_candidates) > 1:
                # Take the highest confidence boundary from the group
                best = max(merge_candidates, key=lambda x: x['confidence'])
                merged.append(best)
                i = j
            else:
                merged.append(current)
                i += 1
                
        print(f"🔄 Merged to {len(merged)} final boundaries")
        return merged
        
    def create_topic_boundaries(self, filtered_boundaries: List[Dict], chunks: List[TopicChunk]) -> List[TopicBoundary]:
        """Create final topic boundary objects"""
        print("📋 Creating final topic boundary objects...")
        
        topic_boundaries = []
        
        # Add implicit start boundary
        if filtered_boundaries and filtered_boundaries[0]['chunk_id'] > 0:
            start_boundary = {
                'chunk_id': 0,
                'page_num': chunks[0].page_num if chunks else 1,
                'confidence': 1.0,
                'type': 'document_start'
            }
            filtered_boundaries.insert(0, start_boundary)
            
        # Create topic sections
        for i in range(len(filtered_boundaries)):
            start_boundary = filtered_boundaries[i]
            
            if i + 1 < len(filtered_boundaries):
                end_boundary = filtered_boundaries[i + 1]
                end_chunk_id = end_boundary['chunk_id'] - 1
            else:
                end_chunk_id = len(chunks) - 1
                
            start_chunk_id = start_boundary['chunk_id']
            
            if end_chunk_id <= start_chunk_id:
                continue
                
            # Get page range
            start_page = chunks[start_chunk_id].page_num
            end_page = chunks[end_chunk_id].page_num
            
            # Generate topic title
            topic_title = self.generate_topic_title(chunks, start_chunk_id, end_chunk_id)
            
            # Create boundary object
            boundary = TopicBoundary(
                topic_title=topic_title,
                start_page=start_page,
                end_page=end_page,
                start_chunk_id=start_chunk_id,
                end_chunk_id=end_chunk_id,
                confidence=start_boundary['confidence'],
                boundary_type=start_boundary['type'],
                content_summary=self.generate_content_summary(chunks, start_chunk_id, end_chunk_id)
            )
            
            topic_boundaries.append(boundary)
            
        print(f"✅ Created {len(topic_boundaries)} topic boundaries")
        return topic_boundaries
        
    def generate_topic_title(self, chunks: List[TopicChunk], start_id: int, end_id: int) -> str:
        """Generate a title for the topic section"""
        # Look for headers, section titles in the first few chunks
        for i in range(start_id, min(start_id + 3, end_id + 1)):
            if i < len(chunks):
                text = chunks[i].clean_text
                
                # Look for section headers
                lines = text.split('\n')
                for line in lines[:5]:  # Check first 5 lines
                    line = line.strip()
                    if (len(line) > 5 and len(line) < 100 and
                        (line.isupper() or 
                         re.match(r'^\d+\.\d+', line) or
                         re.match(r'^Chapter \d+', line) or
                         line.endswith(':'))):
                        return line
                        
        # Fallback: use page range
        start_page = chunks[start_id].page_num if start_id < len(chunks) else 1
        end_page = chunks[end_id].page_num if end_id < len(chunks) else start_page
        
        if start_page == end_page:
            return f"Topic Section (Page {start_page})"
        else:
            return f"Topic Section (Pages {start_page}-{end_page})"
            
    def generate_content_summary(self, chunks: List[TopicChunk], start_id: int, end_id: int) -> str:
        """Generate a brief summary of the topic content"""
        # Combine first and last chunks for summary
        content_parts = []
        
        if start_id < len(chunks):
            first_chunk = chunks[start_id].clean_text[:200]
            content_parts.append(first_chunk)
            
        if end_id < len(chunks) and end_id != start_id:
            last_chunk = chunks[end_id].clean_text[:100]
            content_parts.append(last_chunk)
            
        summary = " ... ".join(content_parts)
        return summary[:300] + "..." if len(summary) > 300 else summary
        
    def visualize_boundaries(self, chunks: List[TopicChunk], boundaries: List[TopicBoundary], 
                           output_file: Optional[str] = None):
        """Create visualizations of the detected boundaries"""
        if not chunks:
            print("⚠️  No chunks to visualize")
            return
            
        print("📊 Creating boundary visualization...")
        
        # Extract similarity data
        similarities = [chunk.similarity_to_prev or 0.0 for chunk in chunks[1:]]
        chunk_ids = list(range(1, len(chunks)))
        page_nums = [chunk.page_num for chunk in chunks[1:]]
        
        # Create the plot
        plt.figure(figsize=(15, 8))
        
        # Plot similarity scores
        plt.subplot(2, 1, 1)
        plt.plot(chunk_ids, similarities, 'b-', alpha=0.7, linewidth=1)
        plt.axhline(y=self.similarity_threshold, color='r', linestyle='--', 
                   label=f'Threshold ({self.similarity_threshold})')
        
        # Mark detected boundaries
        for boundary in boundaries:
            if boundary.start_chunk_id > 0:  # Skip document start
                plt.axvline(x=boundary.start_chunk_id, color='orange', alpha=0.8, 
                           label=f'Topic Boundary (conf: {boundary.confidence:.2f})')
                
        plt.title('Topic Boundary Detection - Similarity Analysis')
        plt.xlabel('Chunk ID')
        plt.ylabel('Similarity to Previous Chunk')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot page distribution
        plt.subplot(2, 1, 2)
        plt.plot(chunk_ids, page_nums, 'g-', alpha=0.7, linewidth=2)
        
        # Mark boundary pages
        for boundary in boundaries:
            if boundary.start_chunk_id > 0:
                plt.axvline(x=boundary.start_chunk_id, color='orange', alpha=0.8)
                
        plt.title('Page Distribution Across Chunks')
        plt.xlabel('Chunk ID')
        plt.ylabel('Page Number')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save or show
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"📈 Visualization saved: {output_file}")
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_file = f"output/topic_boundaries_visualization_{timestamp}.png"
            os.makedirs("output", exist_ok=True)
            plt.savefig(default_file, dpi=300, bbox_inches='tight')
            print(f"📈 Visualization saved: {default_file}")
            
        plt.close()
        
    def export_boundaries(self, boundaries: List[TopicBoundary], chunks: List[TopicChunk]) -> str:
        """Export detected boundaries to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"output/topic_boundaries_{timestamp}.json"
        os.makedirs("output", exist_ok=True)
        
        export_data = {
            'pdf_file': os.path.basename(self.pdf_path),
            'detection_timestamp': timestamp,
            'model_used': self.model_name,
            'configuration': {
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap,
                'similarity_threshold': self.similarity_threshold,
                'min_topic_chunks': self.min_topic_chunks
            },
            'total_chunks': len(chunks),
            'total_boundaries': len(boundaries),
            'boundaries': [asdict(boundary) for boundary in boundaries],
            'statistics': {
                'avg_confidence': np.mean([b.confidence for b in boundaries]) if boundaries else 0,
                'min_confidence': np.min([b.confidence for b in boundaries]) if boundaries else 0,
                'max_confidence': np.max([b.confidence for b in boundaries]) if boundaries else 0
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
            
        print(f"💾 Boundaries exported: {output_file}")
        return output_file
        
    def print_boundary_summary(self, boundaries: List[TopicBoundary]):
        """Print a summary of detected boundaries"""
        print("\n🎯 TOPIC BOUNDARY DETECTION RESULTS")
        print("=" * 60)
        
        if not boundaries:
            print("❌ No topic boundaries detected")
            return
            
        print(f"📊 Total Topics Detected: {len(boundaries)}")
        print(f"📈 Average Confidence: {np.mean([b.confidence for b in boundaries]):.3f}")
        print()
        
        for i, boundary in enumerate(boundaries, 1):
            print(f"📖 Topic {i}: {boundary.topic_title}")
            print(f"   📄 Pages: {boundary.start_page}-{boundary.end_page}")
            print(f"   🎯 Confidence: {boundary.confidence:.3f}")
            print(f"   🔍 Type: {boundary.boundary_type}")
            print(f"   📝 Content: {boundary.content_summary[:100]}...")
            print()
            
    def run_full_detection(self, start_page: int = 1, end_page: Optional[int] = None) -> List[TopicBoundary]:
        """Run the complete boundary detection workflow"""
        print("\n🚀 Starting Topic Boundary Detection Workflow")
        print("=" * 60)
        
        # Step 1: Load topic knowledge
        self.load_extracted_topics()
        
        # Step 2: Extract chunks
        chunks = self.extract_text_chunks(start_page, end_page)
        if not chunks:
            print("❌ No text chunks extracted")
            return []
            
        self.chunks = chunks
        
        # Step 3: Compute embeddings
        chunks = self.compute_embeddings(chunks)
        
        # Step 4: Compute similarities
        chunks = self.compute_similarities(chunks)
        
        # Step 5: Detect boundaries from similarity
        raw_boundaries = self.detect_boundaries_from_similarity(chunks)
        
        # Step 6: Enhance with topic knowledge
        enhanced_boundaries = self.enhance_boundaries_with_topic_knowledge(raw_boundaries)
        
        # Step 7: Filter and merge
        filtered_boundaries = self.filter_and_merge_boundaries(enhanced_boundaries)
        
        # Step 8: Create final boundary objects
        final_boundaries = self.create_topic_boundaries(filtered_boundaries, chunks)
        
        self.boundaries = final_boundaries
        
        # Step 9: Create visualizations
        self.visualize_boundaries(chunks, final_boundaries)
        
        # Step 10: Export results
        self.export_boundaries(final_boundaries, chunks)
        
        # Step 11: Save to vector store (if available)
        if VECTOR_STORE_AVAILABLE:
            self.save_to_vector_store(final_boundaries, chunks)
        
        # Step 12: Print summary
        self.print_boundary_summary(final_boundaries)
        
        print("\n✅ TOPIC BOUNDARY DETECTION COMPLETE!")
        return final_boundaries
    
    def save_to_vector_store(self, boundaries: List[TopicBoundary], chunks: List[TopicChunk]):
        """
        Save detected topics and their content to the vector store for RAG
        
        Args:
            boundaries: Detected topic boundaries
            chunks: All text chunks
        """
        try:
            vector_store = get_vector_store()
            
            print("\n💾 Saving topics to vector store...")
            
            # Prepare topics for vector store
            topics_to_save = []
            
            for boundary in boundaries:
                # Get content from chunks in this boundary
                boundary_chunks = [
                    chunk for chunk in chunks
                    if boundary.start_chunk_id <= chunk.chunk_id <= boundary.end_chunk_id
                ]
                
                # Combine chunk content
                full_content = "\n\n".join([
                    chunk.clean_text for chunk in boundary_chunks[:5]  # First 5 chunks
                ])
                
                topic_data = {
                    'topic': boundary.topic_title,
                    'page': boundary.start_page,
                    'content': full_content,
                    'source': 'boundary_detection',
                    'confidence': boundary.confidence,
                    'boundary_type': boundary.boundary_type,
                    'start_page': boundary.start_page,
                    'end_page': boundary.end_page,
                    'num_chunks': len(boundary_chunks)
                }
                
                topics_to_save.append(topic_data)
            
            # Add to vector store
            source_doc = os.path.basename(self.pdf_path)
            added_count = vector_store.add_topics(topics_to_save, source_document=source_doc)
            
            print(f"✅ Saved {added_count} topics to vector store")
            
            # Print stats
            stats = vector_store.get_collection_stats()
            print(f"📊 Total topics in vector store: {stats['topics_count']}")
            
        except Exception as e:
            print(f"⚠️  Error saving to vector store: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main execution function"""
    print("🎯 Topic Boundary Detection System")
    print("=" * 50)
    
    if not DEPENDENCIES_AVAILABLE:
        print("\n❌ Required dependencies not available")
        print("📦 Please install them with:")
        print("   pip install sentence-transformers scikit-learn matplotlib seaborn")
        return
        
    # Check for PDF file
    pdf_path = "doc/book2.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        print("📖 Please ensure book2.pdf is in the doc/ folder")
        return
        
    # Initialize detector
    detector = TopicBoundaryDetector(pdf_path)
    
    # Get user input for page range
    print("\n📄 Page Range Selection:")
    print("1. Analyze all pages (may take time)")
    print("2. Analyze first 50 pages (faster)")
    print("3. Custom page range")
    
    choice = input("Select option (1-3): ").strip()
    
    start_page = 1
    end_page = None
    
    if choice == "2":
        end_page = 50
    elif choice == "3":
        try:
            start_page = int(input("Start page: ").strip())
            end_page = int(input("End page: ").strip())
        except ValueError:
            print("❌ Invalid page numbers, using default range")
            
    # Run detection
    boundaries = detector.run_full_detection(start_page, end_page)
    
    if boundaries:
        print(f"\n🎉 Successfully detected {len(boundaries)} topic boundaries!")
        print("📁 Check output/ folder for results and visualizations")
    else:
        print("\n❌ No boundaries detected")


if __name__ == "__main__":
    main()

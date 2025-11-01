"""
Beautiful Minimalistic Learning Dashboard
Single-user interface for personalized learning journey
"""

import streamlit as st
import json
import os
import sys
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import curriculum adapter for real-time adaptation
try:
    from agent.curriculum_adapter import CurriculumAdapter
    from streaming.realtime_dashboard_updater import RealTimeDashboardUpdater
    ADAPTATION_ENABLED = True
except ImportError as e:
    print(f"⚠️ Curriculum adaptation not available: {e}")
    ADAPTATION_ENABLED = False
    CurriculumAdapter = None
    RealTimeDashboardUpdater = None

# Page configuration
st.set_page_config(
    page_title="Learning Journey Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for minimalistic design
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
        --background-color: #f8fafc;
        --card-background: #ffffff;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom card styling */
    .metric-card {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        color: white;
        margin-bottom: 1rem;
    }
    
    .stat-card {
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        border-left: 4px solid var(--primary-color);
        margin-bottom: 1rem;
    }
    
    .success-card {
        border-left-color: var(--success-color);
    }
    
    .warning-card {
        border-left-color: var(--warning-color);
    }
    
    .danger-card {
        border-left-color: var(--danger-color);
    }
    
    /* Typography */
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        line-height: 1;
    }
    
    .metric-label {
        font-size: 0.875rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 1rem;
        border-bottom: 2px solid var(--primary-color);
        padding-bottom: 0.5rem;
    }
    
    /* Progress bar */
    .custom-progress {
        height: 8px;
        background-color: #e2e8f0;
        border-radius: 9999px;
        overflow: hidden;
        margin: 1rem 0;
    }
    
    .custom-progress-bar {
        height: 100%;
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        transition: width 0.3s ease;
    }
    
    /* Quiz question styling */
    .quiz-question {
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    
    .quiz-option {
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border: 2px solid #e2e8f0;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .quiz-option:hover {
        border-color: var(--primary-color);
        background: #f1f5f9;
    }
    
    .quiz-option.correct {
        border-color: var(--success-color);
        background: #ecfdf5;
    }
    
    .quiz-option.incorrect {
        border-color: var(--danger-color);
        background: #fef2f2;
    }
    
    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    
    .badge-success {
        background: #d1fae5;
        color: #065f46;
    }
    
    .badge-warning {
        background: #fef3c7;
        color: #92400e;
    }
    
    .badge-danger {
        background: #fee2e2;
        color: #991b1b;
    }
    
    .badge-info {
        background: #dbeafe;
        color: #1e40af;
    }
    
    /* Theory content styling */
    .theory-content {
        background: var(--card-background);
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        line-height: 1.6;
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: transform 0.2s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

def render_theory_with_mathjax(theory_content: str, topic_title: str = "Theory"):
    """
    Render theory content with MathJax support for LaTeX formulas
    Uses the same styling as theory_viewer.html
    Converts markdown-style content to HTML
    """
    import re
    
    # Convert markdown-style formatting to HTML
    # Handle bold text
    theory_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', theory_content)
    
    # Handle headers
    theory_content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', theory_content, flags=re.MULTILINE)
    theory_content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', theory_content, flags=re.MULTILINE)
    theory_content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', theory_content, flags=re.MULTILINE)
    
    # Handle line breaks
    theory_content = theory_content.replace('\n\n', '</p><p>')
    
    # Wrap in paragraph tags if not already wrapped
    if not theory_content.strip().startswith('<'):
        theory_content = f'<p>{theory_content}</p>'
    
    # Load MathJax
    mathjax_script = """
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <script>
        MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
                processEscapes: true,
                processEnvironments: true
            },
            options: {
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
            }
        };
        
        // Trigger MathJax processing after content loads
        window.addEventListener('load', function() {
            if (window.MathJax && window.MathJax.typesetPromise) {
                window.MathJax.typesetPromise();
            }
        });
    </script>
    """
    
    # Enhanced theory styling matching theory_viewer.html
    theory_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        {mathjax_script}
        <style>
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            body {{
                background: white;
                padding: 20px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.8;
                color: #333;
                overflow-y: auto;
                height: 100vh;
            }}
            .theory-viewer {{
                max-width: 100%;
            }}
            .theory-viewer h1 {{
                color: #0c3c60;
                border-bottom: 3px solid #1e90ff;
                padding-bottom: 15px;
                margin-bottom: 25px;
                margin-top: 0;
                font-size: 24px;
            }}
            .theory-viewer h2 {{
                color: #0c3c60;
                margin-top: 25px;
                margin-bottom: 12px;
                font-size: 20px;
                border-left: 4px solid #1e90ff;
                padding-left: 15px;
            }}
            .theory-viewer h3 {{
                color: #1e90ff;
                margin-top: 20px;
                margin-bottom: 10px;
                font-size: 18px;
            }}
            .theory-viewer p {{
                margin: 12px 0;
                font-size: 15px;
                line-height: 1.7;
            }}
            .theory-viewer strong {{
                color: #0c3c60;
                font-weight: 600;
            }}
            .theory-viewer ul, .theory-viewer ol {{
                margin: 12px 0;
                padding-left: 30px;
            }}
            .theory-viewer li {{
                margin: 6px 0;
            }}
            .theory-viewer code {{
                background: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                color: #d73a49;
            }}
            .theory-viewer pre {{
                background: #f6f8fa;
                border: 1px solid #e1e4e8;
                border-radius: 6px;
                padding: 16px;
                overflow-x: auto;
                margin: 15px 0;
            }}
            .theory-viewer pre code {{
                background: none;
                padding: 0;
                color: #333;
            }}
            .theory-viewer table {{
                border-collapse: collapse;
                width: 100%;
                margin: 15px 0;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .theory-viewer th {{
                background: #0c3c60;
                color: white;
                padding: 10px;
                text-align: left;
                font-weight: 600;
                font-size: 14px;
            }}
            .theory-viewer td {{
                padding: 10px;
                border: 1px solid #ddd;
                font-size: 14px;
            }}
            .theory-viewer tr:nth-child(even) {{
                background: #f9f9f9;
            }}
            .theory-viewer .formula {{
                background: #f0f7ff;
                border-left: 4px solid #1e90ff;
                padding: 15px 20px;
                margin: 15px 0;
                border-radius: 5px;
                overflow-x: auto;
            }}
            .theory-viewer .example {{
                background: #f9f9f9;
                border-left: 4px solid #4caf50;
                padding: 15px 20px;
                margin: 15px 0;
                border-radius: 5px;
            }}
            .theory-viewer .note {{
                background: #fff4e5;
                border-left: 4px solid #ffa726;
                padding: 15px 20px;
                margin: 15px 0;
                border-radius: 5px;
            }}
            .mjx-chtml {{
                font-size: 16px !important;
            }}
        </style>
    </head>
    <body>
        <div class="theory-viewer">
            <h1>📖 {topic_title}</h1>
            {theory_content}
        </div>
    </body>
    </html>
    """
    
    return theory_html

class LearningDashboard:
    """Main dashboard class for learning journey visualization"""
    
    def __init__(self):
        self.output_dir = Path("output/student_journey")
        self.current_journey = None
        self.pdf_dir = Path("doc")
        
        # Initialize curriculum adapter for real-time adaptation
        self.curriculum_adapter = None
        self.dashboard_updater = None
        if ADAPTATION_ENABLED:
            try:
                self.curriculum_adapter = CurriculumAdapter()
                self.dashboard_updater = RealTimeDashboardUpdater()
                print("✅ Curriculum adaptation enabled")
            except Exception as e:
                print(f"⚠️ Could not initialize curriculum adapter: {e}")
        
        # Initialize session state
        if 'selected_pdf' not in st.session_state:
            st.session_state.selected_pdf = None
        if 'curriculum_topic' not in st.session_state:
            st.session_state.curriculum_topic = None
        if 'curriculum_data' not in st.session_state:
            st.session_state.curriculum_data = None
        if 'generated_theories' not in st.session_state:
            st.session_state.generated_theories = {}
        if 'generated_quizzes' not in st.session_state:
            st.session_state.generated_quizzes = {}
        if 'show_journey_mode' not in st.session_state:
            st.session_state.show_journey_mode = False
        if 'quiz_history' not in st.session_state:
            st.session_state.quiz_history = []
        if 'student_id' not in st.session_state:
            st.session_state.student_id = "student_001"  # Default student ID
        if 'adaptation_notifications' not in st.session_state:
            st.session_state.adaptation_notifications = []
        
    def get_available_pdfs(self) -> List[str]:
        """Get list of available PDF files"""
        if not self.pdf_dir.exists():
            return []
        return [f.name for f in self.pdf_dir.glob("*.pdf")]
    
    def generate_curriculum_from_topic(self, pdf_path: str, topic: str):
        """Generate curriculum for a given topic"""
        try:
            from optimized_universal_extractor import OptimizedUniversalExtractor
            from llm_enhanced_curriculum_generator import EnhancedLLMCurriculumGenerator
            
            # First, extract topics and save them so the generator can load them
            st.info("📚 Extracting topics from textbook...")
            extractor = OptimizedUniversalExtractor(pdf_path=pdf_path)
            raw_topics = extractor.extract_topics()
            
            # Convert format: add 'title' field for curriculum generator compatibility
            all_topics = []
            for t in raw_topics:
                topic_entry = {
                    'title': t.get('topic', ''),
                    'topic': t.get('topic', ''),
                    'page': t.get('page', 0),
                    'page_numbers': [t.get('page', 0)],
                    'source': t.get('source', 'content')
                }
                all_topics.append(topic_entry)
            
            # Save extracted topics in the format expected by the generator
            os.makedirs("output", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            topics_file = f"output/topics_{timestamp}.json"
            
            # Wrap topics in a dictionary with 'topics' key
            topics_data = {
                'topics': all_topics,
                'pdf_path': pdf_path,
                'timestamp': timestamp,
                'total_topics': len(all_topics)
            }
            
            with open(topics_file, 'w', encoding='utf-8') as f:
                json.dump(topics_data, f, indent=2, ensure_ascii=False)
            
            st.success(f"✅ Extracted {len(all_topics)} topics from textbook")
            
            # Generate curriculum using the learning query
            st.info("🎯 Generating personalized curriculum...")
            generator = EnhancedLLMCurriculumGenerator()
            curriculum = generator.generate_curriculum(learning_query=topic)
            
            return curriculum
            
        except Exception as e:
            st.error(f"Error generating curriculum: {e}")
            import traceback
            st.error(traceback.format_exc())
            return None
    
    def generate_theory_for_topic(self, topic_data: Dict, pdf_path: str):
        """Generate theory content for a specific topic"""
        try:
            from llm_theory_generator import LLMTheoryGenerator
            
            generator = LLMTheoryGenerator(pdf_path)
            
            topic_title = topic_data.get('topic_title', 'Unknown')
            page_numbers = topic_data.get('page_numbers', [])
            
            if not page_numbers:
                return None
            
            theory = generator.generate_theory_from_pdf(
                topic_title=topic_title,
                page_numbers=page_numbers[:5],  # Limit to first 5 pages
                difficulty_level='intermediate',
                learning_objectives=[]
            )
            
            return theory
        except Exception as e:
            st.error(f"Error generating theory: {e}")
            return None
    
    def generate_quiz_for_topic(self, topic_title: str, theory_content: str):
        """Generate quiz for a specific topic"""
        try:
            from llm_quiz_generator import LLMQuizGenerator
            
            generator = LLMQuizGenerator()
            
            quiz = generator.generate_quiz_from_theory(
                theory_content=theory_content,
                topic_title=topic_title,
                difficulty_level='intermediate',
                num_questions=5
            )
            
            return quiz
        except Exception as e:
            st.error(f"Error generating quiz: {e}")
            return None
    
    def get_latest_journey(self) -> Optional[Path]:
        """Get the most recent learning journey"""
        if not self.output_dir.exists():
            return None
        
        journeys = sorted(self.output_dir.glob("*/COMPLETE_JOURNEY.json"), reverse=True)
        return journeys[0] if journeys else None
    
    def load_journey_data(self, journey_path: Path) -> Dict:
        """Load complete journey data"""
        with open(journey_path, 'r') as f:
            return json.load(f)
    
    def render_header(self):
        """Render dashboard header"""
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown("""
            <div style='text-align: center; padding: 2rem 0;'>
                <h1 style='font-size: 2.5rem; font-weight: 700; 
                           background: linear-gradient(135deg, #667eea, #764ba2);
                           -webkit-background-clip: text;
                           -webkit-text-fill-color: transparent;
                           margin-bottom: 0.5rem;'>
                    🎓 Your Learning Journey
                </h1>
                <p style='color: #64748b; font-size: 1.1rem;'>
                    Track your progress and master new concepts
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button("🔄 Switch Mode", key="mode_switch"):
                st.session_state.show_journey_mode = not st.session_state.show_journey_mode
                st.rerun()
    
    def render_book_selection(self):
        """Render book selection interface"""
        st.markdown("<h2 class='section-title'>📚 Select Your Textbook</h2>", unsafe_allow_html=True)
        
        available_pdfs = self.get_available_pdfs()
        
        if not available_pdfs:
            st.error("⚠️ No PDF files found in the 'doc' directory. Please add PDF textbooks.")
            return
        
        selected_pdf = st.selectbox(
            "Choose a textbook:",
            available_pdfs,
            key="pdf_selector"
        )
        
        if selected_pdf:
            pdf_path = self.pdf_dir / selected_pdf
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"📖 Selected: **{selected_pdf}**")
            with col2:
                if st.button("✓ Confirm Selection", type="primary"):
                    st.session_state.selected_pdf = str(pdf_path)
                    st.success("Book selected! Now enter your curriculum topic.")
                    st.rerun()
    
    def render_curriculum_input(self):
        """Render curriculum topic input"""
        st.markdown("<h2 class='section-title'>📝 Enter Your Learning Topic</h2>", unsafe_allow_html=True)
        
        st.markdown(f"**Selected Book:** {Path(st.session_state.selected_pdf).name}")
        
        topic = st.text_input(
            "What topic would you like to learn?",
            placeholder="e.g., expectation and variance, probability theory, linear algebra",
            key="topic_input"
        )
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if st.button("🚀 Generate Curriculum", type="primary", disabled=not topic):
                with st.spinner("🔍 Analyzing textbook and generating curriculum..."):
                    curriculum = self.generate_curriculum_from_topic(
                        st.session_state.selected_pdf,
                        topic
                    )
                    
                    if curriculum:
                        # Ensure curriculum is a dictionary, not a string
                        if isinstance(curriculum, str):
                            curriculum = json.loads(curriculum)
                        
                        st.session_state.curriculum_topic = topic
                        st.session_state.curriculum_data = curriculum
                        st.success(f"✅ Curriculum generated for '{topic}'!")
                        st.rerun()
                    else:
                        st.error("❌ Could not generate curriculum. Please try a different topic.")
        
        with col2:
            if st.button("← Back to Book Selection"):
                st.session_state.selected_pdf = None
                st.rerun()
    
    def render_curriculum_topics(self):
        """Render curriculum with expandable topics"""
        st.markdown("<h2 class='section-title'>📚 Your Learning Curriculum</h2>", unsafe_allow_html=True)
        
        curriculum = st.session_state.curriculum_data
        
        # Display curriculum info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📖 Topic", curriculum.get('topic', 'N/A').title())
        with col2:
            st.metric("📊 Modules", len(curriculum.get('modules', [])))
        with col3:
            total_topics = sum(len(m.get('topics', [])) for m in curriculum.get('modules', []))
            st.metric("📝 Total Topics", total_topics)
        
        st.markdown("---")
        
        # Render modules and topics
        modules = curriculum.get('modules', [])
        
        for module_idx, module in enumerate(modules):
            module_name = module.get('title', module.get('module_name', f'Module {module_idx + 1}'))
            difficulty = module.get('difficulty', module.get('difficulty_level', 'N/A'))
            duration = module.get('estimated_duration', module.get('estimated_hours', 'N/A'))
            topics = module.get('topics', [])
            pages = module.get('pages', [])
            
            with st.expander(f"📘 {module_name} ({difficulty}, {duration})", expanded=(module_idx == 0)):
                st.markdown(f"**Topics:** {len(topics)} | **Difficulty:** {difficulty}")
                st.markdown("---")
                
                for topic_idx, topic in enumerate(topics):
                    # Handle both string topics and dictionary topics
                    if isinstance(topic, str):
                        topic_title = topic
                        # Get corresponding page if available
                        page_num = pages[topic_idx] if topic_idx < len(pages) else None
                        topic_dict = {
                            'topic_title': topic_title,
                            'topic': topic_title,
                            'page': page_num,
                            'page_numbers': [page_num] if page_num else []
                        }
                    else:
                        topic_title = topic.get('topic_title', topic.get('topic', 'Unknown'))
                        topic_dict = topic
                    
                    topic_key = f"{module_idx}_{topic_idx}"
                    
                    # Topic header with generate button
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.markdown(f"**{topic_idx + 1}. {topic_title}**")
                    
                    with col2:
                        if topic_key not in st.session_state.generated_theories:
                            if st.button("📖 Learn", key=f"gen_{topic_key}"):
                                with st.spinner(f"Generating content for '{topic_title}'..."):
                                    theory = self.generate_theory_for_topic(
                                        topic_dict,
                                        st.session_state.selected_pdf
                                    )
                                    
                                    if theory:
                                        st.session_state.generated_theories[topic_key] = {
                                            'topic_title': topic_title,
                                            'theory': theory,
                                            'topic_data': topic_dict
                                        }
                                        st.rerun()
                        else:
                            st.markdown("✅ *Ready*")
                    
                    # Display generated theory
                    if topic_key in st.session_state.generated_theories:
                        theory_data = st.session_state.generated_theories[topic_key]
                        
                        with st.container():
                            # Theory content in tabs
                            tab1, tab2 = st.tabs(["📖 Theory Content", "❓ Quiz"])
                            
                            with tab1:
                                # Use enhanced HTML rendering with MathJax support
                                theory_html = render_theory_with_mathjax(
                                    theory_data['theory'],
                                    topic_title
                                )
                                # Use increased height for better visibility and scrolling
                                st.components.v1.html(theory_html, height=1000, scrolling=True)
                            
                            with tab2:
                                if topic_key not in st.session_state.generated_quizzes:
                                    if st.button("🎯 Generate Quiz", key=f"quiz_{topic_key}"):
                                        with st.spinner("Creating quiz questions..."):
                                            quiz = self.generate_quiz_for_topic(
                                                topic_title,
                                                theory_data['theory']
                                            )
                                            
                                            if quiz:
                                                st.session_state.generated_quizzes[topic_key] = quiz
                                                st.success("Quiz generated!")
                                                st.rerun()
                                else:
                                    # Display quiz
                                    quiz = st.session_state.generated_quizzes[topic_key]
                                    self.render_topic_quiz(quiz, topic_key)
                        
                        st.markdown("---")
        
        # Navigation buttons
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("← New Topic"):
                st.session_state.curriculum_topic = None
                st.session_state.curriculum_data = None
                st.session_state.generated_theories = {}
                st.session_state.generated_quizzes = {}
                st.rerun()
    
    def render_topic_quiz(self, quiz_questions: List[Dict], topic_key: str):
        """Render quiz for a specific topic"""
        st.markdown("### 📝 Quiz Questions")
        
        # Initialize quiz state
        quiz_state_key = f"quiz_state_{topic_key}"
        if quiz_state_key not in st.session_state:
            st.session_state[quiz_state_key] = {
                'answers': {},
                'submitted': False,
                'score': 0
            }
        
        quiz_state = st.session_state[quiz_state_key]
        
        if not quiz_state['submitted']:
            # Show questions
            for i, question in enumerate(quiz_questions):
                st.markdown(f"**Question {i+1}:** {question.get('question', 'N/A')}")
                
                options = question.get('options', [])
                answer = st.radio(
                    "Select your answer:",
                    options,
                    key=f"quiz_q_{topic_key}_{i}",
                    index=None
                )
                
                if answer:
                    # Store answer as letter (A, B, C, D)
                    quiz_state['answers'][i] = chr(65 + options.index(answer))
                
                st.markdown("---")
            
            # Submit button
            if st.button("✅ Submit Quiz", key=f"submit_{topic_key}"):
                # Calculate score
                correct = 0
                weak_topics = []
                for i, question in enumerate(quiz_questions):
                    student_answer = quiz_state['answers'].get(i)
                    correct_answer = question.get('correct_answer')
                    
                    if student_answer == correct_answer:
                        correct += 1
                    else:
                        # Track weak topics
                        weak_topics.append(question.get('topic', topic_key))
                
                quiz_state['score'] = (correct / len(quiz_questions)) * 100
                quiz_state['submitted'] = True
                quiz_state['timestamp'] = datetime.now().isoformat()
                
                # Add to quiz history
                quiz_record = {
                    'topic': topic_key,
                    'score': quiz_state['score'],
                    'percentage': quiz_state['score'],
                    'total_questions': len(quiz_questions),
                    'correct_answers': correct,
                    'timestamp': quiz_state['timestamp'],
                    'weak_topics': list(set(weak_topics))
                }
                st.session_state.quiz_history.append(quiz_record)
                
                # 🔥 TRIGGER CURRICULUM ADAPTATION
                if self.curriculum_adapter and st.session_state.curriculum_data:
                    try:
                        # Ensure curriculum_data is a dictionary
                        curriculum = st.session_state.curriculum_data
                        if isinstance(curriculum, str):
                            try:
                                curriculum = json.loads(curriculum)
                                st.session_state.curriculum_data = curriculum
                            except json.JSONDecodeError as je:
                                print(f"⚠️ Failed to parse curriculum JSON: {je}")
                                raise ValueError(f"Invalid curriculum format: {je}")
                        
                        if not isinstance(curriculum, dict):
                            raise ValueError(f"Curriculum must be a dictionary, got {type(curriculum)}")
                        
                        # Get current module from curriculum
                        current_module = None
                        modules = curriculum.get('modules', [])
                        
                        if not modules:
                            print("⚠️ No modules found in curriculum")
                            current_module = "Unknown Module"
                        else:
                            for module in modules:
                                if not isinstance(module, dict):
                                    print(f"⚠️ Module is not a dict: {type(module)}")
                                    continue
                                    
                                module_topics = module.get('topics', [])
                                for topic in module_topics:
                                    # Handle both dict and string topics
                                    if isinstance(topic, dict):
                                        topic_title = topic.get('title', '')
                                    elif isinstance(topic, str):
                                        topic_title = topic
                                    else:
                                        continue
                                    
                                    if topic_title == topic_key or topic_key in topic_title:
                                        current_module = module.get('title', 'Unknown Module')
                                        break
                                        
                                if current_module:
                                    break
                        
                        if not current_module:
                            current_module = curriculum.get('modules', [{}])[0].get('title', 'Module 1')
                        
                        # Analyze quiz history for this student
                        recent_scores = [q['score'] for q in st.session_state.quiz_history[-5:]]
                        avg_score = sum(recent_scores) / len(recent_scores) if recent_scores else quiz_state['score']
                        
                        # Count struggles (scores < 60%)
                        struggle_count = sum(1 for s in recent_scores if s < 60)
                        
                        # Determine performance trend
                        if len(recent_scores) >= 3:
                            if recent_scores[-1] > recent_scores[-2] > recent_scores[-3]:
                                trend = "improving"
                            elif recent_scores[-1] < recent_scores[-2] < recent_scores[-3]:
                                trend = "declining"
                            else:
                                trend = "stable"
                        else:
                            trend = "stable"
                        
                        # Build performance data
                        performance_data = {
                            'average_score': avg_score,
                            'weak_topics': weak_topics,
                            'struggle_count': struggle_count,
                            'performance_trend': trend,
                            'recent_quiz_score': quiz_state['score']
                        }
                        
                        # Make adaptation decision
                        with st.spinner("🧠 Analyzing your performance and adapting curriculum..."):
                            decision = self.curriculum_adapter.make_adaptation_decision(
                                student_id=st.session_state.student_id,
                                module_name=current_module,
                                performance_data=performance_data,
                                current_curriculum=curriculum  # Pass the curriculum
                            )
                            
                            # Apply adaptation to curriculum
                            if decision and decision.actions:
                                updated_curriculum = self.curriculum_adapter.apply_adaptation(
                                    decision,
                                    curriculum  # Use the validated dictionary
                                )
                                
                                # Update session state with adapted curriculum
                                st.session_state.curriculum_data = updated_curriculum
                                
                                # Show notification
                                notification_msg = f"🔄 **Curriculum Adapted!** {decision.reasoning}"
                                st.session_state.adaptation_notifications.append({
                                    'message': notification_msg,
                                    'timestamp': datetime.now().isoformat(),
                                    'decision_type': decision.decision_type
                                })
                                
                                st.success(notification_msg)
                    except Exception as e:
                        import traceback
                        error_details = traceback.format_exc()
                        print(f"⚠️ Curriculum adaptation failed: {e}")
                        print(f"Error details:\n{error_details}")
                        st.warning(f"Curriculum adaptation unavailable: {e}")
                
                st.rerun()
        
        else:
            # Show results
            st.success(f"🎉 Quiz Completed! Score: {quiz_state['score']:.1f}%")
            
            # Show detailed results
            for i, question in enumerate(quiz_questions):
                student_ans = quiz_state['answers'].get(i, 'N/A')
                correct_ans = question.get('correct_answer', 'N/A')
                is_correct = student_ans == correct_ans
                
                with st.expander(
                    f"Question {i+1}: {'✅ Correct' if is_correct else '❌ Incorrect'}",
                    expanded=not is_correct
                ):
                    st.markdown(f"**{question.get('question', 'N/A')}**")
                    
                    options = question.get('options', [])
                    for j, option in enumerate(options):
                        option_letter = chr(65 + j)
                        if option_letter == correct_ans:
                            st.markdown(f"✅ **{option_letter}.** {option} *(Correct)*")
                        elif option_letter == student_ans:
                            st.markdown(f"❌ **{option_letter}.** {option} *(Your Answer)*")
                        else:
                            st.markdown(f"○ **{option_letter}.** {option}")
                    
                    st.info(f"**Explanation:** {question.get('explanation', 'N/A')}")
            
            if st.button("🔄 Retake Quiz", key=f"retake_{topic_key}"):
                st.session_state[quiz_state_key] = {
                    'answers': {},
                    'submitted': False,
                    'score': 0
                }
                st.rerun()
    
    def render_header(self):
        """Render dashboard header"""
        st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='font-size: 2.5rem; font-weight: 700; 
                       background: linear-gradient(135deg, #667eea, #764ba2);
                       -webkit-background-clip: text;
                       -webkit-text-fill-color: transparent;
                       margin-bottom: 0.5rem;'>
                🎓 Your Learning Journey
            </h1>
            <p style='color: #64748b; font-size: 1.1rem;'>
                Track your progress and master new concepts
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_overview_metrics(self, journey_data: Dict):
        """Render key metrics in cards"""
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate metrics
        quiz_results = journey_data.get('quiz_results', {})
        score = quiz_results.get('score', 0)
        total_questions = len(quiz_results.get('questions', []))
        correct = int((score / 100) * total_questions) if total_questions > 0 else 0
        
        curriculum = journey_data.get('curriculum', {})
        total_modules = len(curriculum.get('modules', []))
        
        with col1:
            st.markdown(f"""
            <div class='stat-card success-card'>
                <div class='metric-value' style='color: #10b981;'>{score:.1f}%</div>
                <div class='metric-label' style='color: #64748b;'>Quiz Score</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='metric-value' style='color: #667eea;'>{correct}/{total_questions}</div>
                <div class='metric-label' style='color: #64748b;'>Questions Correct</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class='stat-card warning-card'>
                <div class='metric-value' style='color: #f59e0b;'>{total_modules}</div>
                <div class='metric-label' style='color: #64748b;'>Total Modules</div>
            </div>
            """, unsafe_allow_html=True)
        
        performance_level = journey_data.get('personalization', {}).get('performance_level', 'unknown')
        level_colors = {
            'excellent': '#10b981',
            'good': '#3b82f6',
            'needs_improvement': '#f59e0b',
            'unknown': '#64748b'
        }
        
        with col4:
            st.markdown(f"""
            <div class='stat-card'>
                <div style='font-size: 1.2rem; font-weight: 600; color: {level_colors.get(performance_level, "#64748b")};'>
                    {performance_level.replace('_', ' ').title()}
                </div>
                <div class='metric-label' style='color: #64748b;'>Performance Level</div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_progress_chart(self, journey_data: Dict):
        """Render progress visualization"""
        st.markdown("<h3 class='section-title'>📊 Performance Overview</h3>", unsafe_allow_html=True)
        
        quiz_results = journey_data.get('quiz_results', {})
        questions = quiz_results.get('questions', [])
        student_answers = quiz_results.get('student_answers', [])
        correct_answers = quiz_results.get('correct_answers', [])
        
        # Create performance data
        performance_data = []
        for i, (question, student_ans, correct_ans) in enumerate(zip(questions, student_answers, correct_answers)):
            is_correct = student_ans == correct_ans
            performance_data.append({
                'Question': f"Q{i+1}",
                'Concept': question.get('concept', 'Unknown'),
                'Difficulty': question.get('difficulty', 'medium'),
                'Result': 'Correct' if is_correct else 'Incorrect',
                'Value': 1 if is_correct else 0
            })
        
        # Create stacked bar chart
        fig = go.Figure()
        
        correct_data = [1 if p['Result'] == 'Correct' else 0 for p in performance_data]
        incorrect_data = [1 if p['Result'] == 'Incorrect' else 0 for p in performance_data]
        questions_labels = [p['Question'] for p in performance_data]
        
        fig.add_trace(go.Bar(
            name='Correct',
            x=questions_labels,
            y=correct_data,
            marker_color='#10b981',
            hovertemplate='<b>%{x}</b><br>Status: Correct<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            name='Incorrect',
            x=questions_labels,
            y=incorrect_data,
            marker_color='#ef4444',
            hovertemplate='<b>%{x}</b><br>Status: Incorrect<extra></extra>'
        ))
        
        fig.update_layout(
            barmode='stack',
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=False,
                title='Questions'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#e2e8f0',
                title='Result',
                tickvals=[0, 1],
                ticktext=['', '']
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_concept_analysis(self, journey_data: Dict):
        """Render concept strength/weakness analysis"""
        col1, col2 = st.columns(2)
        
        quiz_results = journey_data.get('quiz_results', {})
        strong_concepts = quiz_results.get('strong_concepts', [])
        weak_concepts = quiz_results.get('weak_concepts', [])
        
        with col1:
            st.markdown("<h3 class='section-title'>💪 Strong Concepts</h3>", unsafe_allow_html=True)
            if strong_concepts:
                for concept in strong_concepts[:5]:
                    st.markdown(f"""
                    <div style='padding: 0.75rem; margin: 0.5rem 0; 
                                background: #ecfdf5; border-left: 4px solid #10b981; 
                                border-radius: 8px;'>
                        <span style='color: #065f46; font-weight: 600;'>✓ {concept}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Complete a quiz to see your strong concepts!")
        
        with col2:
            st.markdown("<h3 class='section-title'>🎯 Areas to Improve</h3>", unsafe_allow_html=True)
            if weak_concepts:
                for concept in weak_concepts[:5]:
                    st.markdown(f"""
                    <div style='padding: 0.75rem; margin: 0.5rem 0; 
                                background: #fef2f2; border-left: 4px solid #ef4444; 
                                border-radius: 8px;'>
                        <span style='color: #991b1b; font-weight: 600;'>✗ {concept}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("Great job! No weak areas identified.")
    
    def render_curriculum_modules(self, journey_data: Dict):
        """Render curriculum modules with progress"""
        st.markdown("<h3 class='section-title'>📚 Learning Path</h3>", unsafe_allow_html=True)
        
        curriculum = journey_data.get('curriculum', {})
        modules = curriculum.get('modules', [])
        
        for i, module in enumerate(modules):
            with st.expander(f"**Module {i+1}:** {module.get('module_name', 'Unknown')}", expanded=(i == 0)):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Difficulty:** {module.get('difficulty_level', 'N/A').title()}")
                    st.markdown(f"**Duration:** {module.get('estimated_hours', 0)} hours")
                    st.markdown(f"**Topics:** {len(module.get('topics', []))}")
                    
                    # Show topics
                    topics = module.get('topics', [])
                    if topics:
                        st.markdown("**📖 Topics Covered:**")
                        for topic in topics[:3]:
                            st.markdown(f"- {topic.get('topic_title', 'Unknown')}")
                        if len(topics) > 3:
                            st.markdown(f"*... and {len(topics) - 3} more topics*")
                
                with col2:
                    # Module status badge
                    if i == 0:
                        st.markdown("<span class='badge badge-success'>✓ Completed</span>", unsafe_allow_html=True)
                    elif i == 1:
                        st.markdown("<span class='badge badge-warning'>◷ In Progress</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span class='badge badge-info'>○ Upcoming</span>", unsafe_allow_html=True)
    
    def render_quiz_review(self, journey_data: Dict):
        """Render detailed quiz review"""
        st.markdown("<h3 class='section-title'>📝 Quiz Review</h3>", unsafe_allow_html=True)
        
        quiz_results = journey_data.get('quiz_results', {})
        questions = quiz_results.get('questions', [])
        student_answers = quiz_results.get('student_answers', [])
        correct_answers = quiz_results.get('correct_answers', [])
        
        if not questions:
            st.info("No quiz data available yet.")
            return
        
        for i, (question, student_ans, correct_ans) in enumerate(zip(questions, student_answers, correct_answers)):
            is_correct = student_ans == correct_ans
            
            with st.expander(f"**Question {i+1}:** {question.get('concept', 'Unknown')} {'✓' if is_correct else '✗'}", 
                           expanded=not is_correct):
                
                # Question text
                st.markdown(f"**{question.get('question', 'N/A')}**")
                
                # Difficulty and concept badges
                col1, col2 = st.columns(2)
                with col1:
                    difficulty = question.get('difficulty', 'medium')
                    difficulty_colors = {
                        'easy': 'badge-success',
                        'medium': 'badge-warning',
                        'hard': 'badge-danger'
                    }
                    st.markdown(f"<span class='badge {difficulty_colors.get(difficulty, 'badge-info')}'>{difficulty.upper()}</span>", 
                              unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"<span class='badge badge-info'>{question.get('concept', 'N/A')}</span>", 
                              unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Options
                options = question.get('options', [])
                for j, option in enumerate(options):
                    option_letter = chr(65 + j)  # A, B, C, D
                    
                    if option_letter == correct_ans:
                        st.markdown(f"✅ **{option_letter}.** {option} *(Correct Answer)*")
                    elif option_letter == student_ans:
                        st.markdown(f"❌ **{option_letter}.** {option} *(Your Answer)*")
                    else:
                        st.markdown(f"○ **{option_letter}.** {option}")
                
                # Explanation
                st.markdown("**💡 Explanation:**")
                st.info(question.get('explanation', 'No explanation available.'))
    
    def render_personalized_recommendations(self, journey_data: Dict):
        """Render personalized learning recommendations"""
        st.markdown("<h3 class='section-title'>🎯 Personalized Recommendations</h3>", unsafe_allow_html=True)
        
        personalization = journey_data.get('personalization', {})
        recommendations = personalization.get('recommendations', [])
        focus_areas = personalization.get('focus_areas', [])
        content_adjustments = personalization.get('content_adjustments', {})
        
        if recommendations:
            st.markdown("**📋 Action Items:**")
            for rec in recommendations:
                st.markdown(f"- {rec}")
        
        if focus_areas:
            st.markdown("**🔍 Focus on These Topics:**")
            cols = st.columns(min(3, len(focus_areas)))
            for i, area in enumerate(focus_areas[:6]):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div style='padding: 0.75rem; text-align: center; 
                                background: linear-gradient(135deg, #667eea, #764ba2);
                                color: white; border-radius: 8px; margin: 0.25rem;'>
                        <strong>{area}</strong>
                    </div>
                    """, unsafe_allow_html=True)
        
        if content_adjustments:
            st.markdown("**⚙️ Content Adjustments for Next Module:**")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Difficulty", content_adjustments.get('difficulty', 'N/A').title())
            with col2:
                st.metric("Examples", content_adjustments.get('examples', 'N/A').title())
            with col3:
                st.metric("Practice", content_adjustments.get('practice_problems', 'N/A').replace('_', ' ').title())
            with col4:
                st.metric("Depth", content_adjustments.get('explanation_depth', 'N/A').title())
    
    def render_theory_viewer(self, journey_data: Dict):
        """Render theory content viewer"""
        st.markdown("<h3 class='section-title'>📖 Learning Content</h3>", unsafe_allow_html=True)
        
        theories = journey_data.get('theories', [])
        
        if not theories:
            st.info("No theory content available yet.")
            return
        
        # Theory selector
        theory_titles = [f"{t.get('topic', 'Unknown')}" for t in theories]
        selected_theory_idx = st.selectbox(
            "Select a topic to study:",
            range(len(theory_titles)),
            format_func=lambda x: theory_titles[x]
        )
        
        if selected_theory_idx is not None:
            theory = theories[selected_theory_idx]
            
            # Display theory content
            st.markdown(f"**Topic:** {theory.get('topic', 'Unknown')}")
            st.markdown(f"**Module:** {theory.get('module', 'Unknown')}")
            
            if theory.get('page_references'):
                st.markdown(f"**Reference Pages:** {', '.join(map(str, theory['page_references']))}")
            
            st.markdown("---")
            
            # Theory content in a styled container
            theory_content = theory.get('theory', 'No content available.')
            st.markdown(f"""
            <div class='theory-content'>
                {theory_content}
            </div>
            """, unsafe_allow_html=True)
    
    def run(self):
        """Main dashboard execution"""
        self.render_header()
        
        # Show adaptation notifications at the top
        if st.session_state.adaptation_notifications:
            st.markdown("### 🔔 Curriculum Updates")
            for notification in st.session_state.adaptation_notifications[-3:]:  # Show last 3
                timestamp = datetime.fromisoformat(notification['timestamp'])
                time_str = timestamp.strftime("%H:%M:%S")
                st.info(f"**[{time_str}]** {notification['message']}")
            st.markdown("---")
        
        # Mode selection: Journey Review or Interactive Learning
        if st.session_state.show_journey_mode:
            # Original journey review mode
            st.info("📊 **Journey Review Mode** - Viewing completed learning journeys")
            
            # Load latest journey
            latest_journey = self.get_latest_journey()
            
            if not latest_journey:
                st.warning("⚠️ No learning journey found. Switch to Interactive Learning mode or complete a journey first!")
                return
            
            # Load journey data
            journey_data = self.load_journey_data(latest_journey)
            
            # Sidebar navigation
            with st.sidebar:
                st.markdown("### 🎯 Navigation")
                page = st.radio(
                    "Select View:",
                    ["Overview", "Quiz Review", "Learning Content", "Recommendations"],
                    label_visibility="collapsed"
                )
                
                st.markdown("---")
                
                # Journey info
                st.markdown("### 📅 Journey Info")
                journey_folder = latest_journey.parent.name
                journey_date = datetime.strptime(journey_folder, "%Y%m%d_%H%M%S")
                st.markdown(f"**Date:** {journey_date.strftime('%B %d, %Y')}")
                st.markdown(f"**Time:** {journey_date.strftime('%I:%M %p')}")
                
                curriculum = journey_data.get('curriculum', {})
                st.markdown(f"**Topic:** {curriculum.get('topic', 'N/A').title()}")
                st.markdown(f"**Level:** {curriculum.get('knowledge_level', 'N/A').title()}")
                
                st.markdown("---")
                
                # Quick stats
                st.markdown("### 📊 Quick Stats")
                quiz_results = journey_data.get('quiz_results', {})
                score = quiz_results.get('score', 0)
                
                # Score with color
                score_color = '#10b981' if score >= 80 else '#f59e0b' if score >= 60 else '#ef4444'
                st.markdown(f"<h2 style='color: {score_color}; margin: 0;'>{score:.1f}%</h2>", unsafe_allow_html=True)
                st.markdown("Quiz Score")
            
            # Main content based on selected page
            if page == "Overview":
                self.render_overview_metrics(journey_data)
                st.markdown("---")
                self.render_progress_chart(journey_data)
                st.markdown("---")
                self.render_concept_analysis(journey_data)
                st.markdown("---")
                self.render_curriculum_modules(journey_data)
            
            elif page == "Quiz Review":
                self.render_quiz_review(journey_data)
            
            elif page == "Learning Content":
                self.render_theory_viewer(journey_data)
            
            elif page == "Recommendations":
                self.render_personalized_recommendations(journey_data)
                st.markdown("---")
                self.render_concept_analysis(journey_data)
        
        else:
            # Interactive learning mode
            st.info("🎓 **Interactive Learning Mode** - Generate custom curriculum and learn at your own pace")
            
            # Flow: Book Selection → Curriculum Input → Curriculum Display
            if not st.session_state.selected_pdf:
                self.render_book_selection()
            elif not st.session_state.curriculum_data:
                self.render_curriculum_input()
            else:
                self.render_curriculum_topics()

# Run the dashboard
if __name__ == "__main__":
    dashboard = LearningDashboard()
    dashboard.run()

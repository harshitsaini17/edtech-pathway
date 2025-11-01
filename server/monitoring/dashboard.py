"""
Streamlit Monitoring Dashboard
================================
Real-time visualization of student progress, curriculum adaptation, and system metrics.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import time
import sys
import os

# Add server directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.student_profile import StudentProfileManager
from cache.cache_manager import get_cache_manager
from events.event_stream import get_event_stream_handler
from config.settings import settings


# Page configuration
st.set_page_config(
    page_title="LearnPro - Adaptive Learning Dashboard",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-text {
        color: #28a745;
        font-weight: bold;
    }
    .warning-text {
        color: #ffc107;
        font-weight: bold;
    }
    .danger-text {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# Initialize services
@st.cache_resource
def init_services():
    """Initialize dashboard services"""
    profile_manager = StudentProfileManager()
    cache_manager = get_cache_manager()
    event_handler = get_event_stream_handler()
    
    return profile_manager, cache_manager, event_handler


def render_header():
    """Render dashboard header"""
    st.markdown('<div class="main-header">📚 LearnPro Adaptive Learning Dashboard</div>', unsafe_allow_html=True)
    st.markdown("---")


def render_system_health(cache_manager, event_handler):
    """Render system health metrics"""
    st.header("🏥 System Health")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Cache health
    try:
        cache_health = cache_manager.health_check()
        cache_status = cache_health.get("status", "unknown")
        
        with col1:
            if cache_status == "healthy":
                st.metric("Redis Cache", "🟢 Healthy", delta="Connected")
            else:
                st.metric("Redis Cache", "🔴 Unhealthy", delta="Disconnected")
    except:
        with col1:
            st.metric("Redis Cache", "🔴 Error", delta="Check connection")
    
    # Event stream health
    event_stats = event_handler.get_stats()
    with col2:
        if event_stats["handler"]["running"]:
            st.metric(
                "Event Stream", 
                "🟢 Running",
                delta=f"{event_stats['handler']['events_per_second']:.1f} events/sec"
            )
        else:
            st.metric("Event Stream", "🔴 Stopped", delta="Not running")
    
    # Buffer utilization
    buffer_util = event_stats["buffer"]["utilization"] * 100
    with col3:
        st.metric(
            "Buffer Utilization",
            f"{buffer_util:.1f}%",
            delta=f"{event_stats['buffer']['current_size']} / {event_stats['buffer']['max_size']}"
        )
    
    # Events processed
    with col4:
        st.metric(
            "Events Processed",
            f"{event_stats['handler']['events_processed']:,}",
            delta=f"{event_stats['handler']['batches_processed']} batches"
        )
    
    # Cache statistics
    try:
        cache_stats = cache_manager.get_stats()
        
        st.subheader("Cache Statistics")
        cache_col1, cache_col2, cache_col3 = st.columns(3)
        
        with cache_col1:
            st.metric("Total Keys", cache_stats.get("total_keys", 0))
        with cache_col2:
            st.metric("Memory Used", f"{cache_stats.get('memory_used_mb', 0):.2f} MB")
        with cache_col3:
            st.metric("Hit Rate", f"{cache_stats.get('hit_rate', 0):.1%}")
    except:
        st.info("Cache statistics unavailable")


def render_student_overview(profile_manager):
    """Render student overview"""
    st.header("👥 Student Overview")
    
    # Get all students
    students = profile_manager.get_all_students()
    
    if not students:
        st.info("No students enrolled yet")
        return
    
    # Summary metrics
    total_students = len(students)
    active_students = sum(1 for s in students if s.module_progress)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Students", total_students)
    with col2:
        st.metric("Active Students", active_students)
    with col3:
        completion_rate = sum(1 for s in students if all(m.completed for m in s.module_progress)) / total_students * 100 if total_students > 0 else 0
        st.metric("Completion Rate", f"{completion_rate:.1f}%")
    
    # Student list
    st.subheader("📋 Student List")
    
    student_data = []
    for student in students[:10]:  # Show top 10
        total_modules = len(student.module_progress)
        completed_modules = sum(1 for m in student.module_progress if m.completed)
        avg_score = sum(m.mastery_score for m in student.module_progress) / total_modules * 100 if total_modules > 0 else 0
        
        student_data.append({
            "Student ID": student.student_id,
            "Name": student.name,
            "Current Module": student.current_module,
            "Progress": f"{completed_modules}/{total_modules}",
            "Avg Score": f"{avg_score:.1f}%",
            "Enrolled": student.enrolled_at.strftime("%Y-%m-%d")
        })
    
    if student_data:
        df = pd.DataFrame(student_data)
        st.dataframe(df, use_container_width=True)


def render_student_detail(profile_manager, student_id):
    """Render detailed student view"""
    st.header(f"📊 Student Detail: {student_id}")
    
    profile = profile_manager.get_profile(student_id)
    
    if not profile:
        st.error("Student not found")
        return
    
    # Profile summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Name", profile.name)
    with col2:
        st.metric("Email", profile.email)
    with col3:
        st.metric("Current Module", profile.current_module)
    
    # Module progress
    st.subheader("📚 Module Progress")
    
    if not profile.module_progress:
        st.info("No module progress yet")
        return
    
    # Progress chart
    module_names = [m.module_name for m in profile.module_progress]
    mastery_scores = [m.mastery_score * 100 for m in profile.module_progress]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=module_names,
        y=mastery_scores,
        text=[f"{score:.1f}%" for score in mastery_scores],
        textposition='auto',
        marker_color=['green' if score >= 80 else 'orange' if score >= 60 else 'red' for score in mastery_scores]
    ))
    
    fig.update_layout(
        title="Module Mastery Scores",
        xaxis_title="Module",
        yaxis_title="Mastery Score (%)",
        yaxis_range=[0, 100],
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Weak areas
    st.subheader("⚠️ Weak Areas")
    
    all_weak_areas = []
    for module in profile.module_progress:
        all_weak_areas.extend(module.weak_areas)
    
    if all_weak_areas:
        weak_area_counts = pd.Series(all_weak_areas).value_counts()
        
        fig = px.bar(
            x=weak_area_counts.index,
            y=weak_area_counts.values,
            labels={"x": "Topic", "y": "Frequency"},
            title="Most Common Weak Areas"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("No weak areas identified!")
    
    # Quiz attempts timeline
    st.subheader("📈 Quiz Attempts Timeline")
    
    quiz_data = []
    for module in profile.module_progress:
        for attempt in module.quiz_attempts:
            quiz_data.append({
                "Module": module.module_name,
                "Quiz ID": attempt["quiz_id"],
                "Score": attempt["score"],
                "Timestamp": attempt["timestamp"]
            })
    
    if quiz_data:
        quiz_df = pd.DataFrame(quiz_data)
        quiz_df["Timestamp"] = pd.to_datetime(quiz_df["Timestamp"])
        
        fig = px.line(
            quiz_df,
            x="Timestamp",
            y="Score",
            color="Module",
            markers=True,
            title="Quiz Performance Over Time"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No quiz attempts yet")


def render_curriculum_adaptation():
    """Render curriculum adaptation insights"""
    st.header("🎯 Curriculum Adaptation")
    
    st.info("Curriculum adaptation data will be displayed here when adaptations occur")
    
    # Placeholder for adaptation history
    st.subheader("Recent Adaptations")
    
    # This would load from adaptation_history in production
    st.write("- Topic reranking for struggling students")
    st.write("- Remedial content injection")
    st.write("- Difficulty adjustments")


def render_performance_analytics(profile_manager):
    """Render performance analytics"""
    st.header("📊 Performance Analytics")
    
    students = profile_manager.get_all_students()
    
    if not students:
        st.info("No data available")
        return
    
    # Distribution of scores
    all_scores = []
    for student in students:
        for module in student.module_progress:
            all_scores.append({
                "Student": student.student_id,
                "Module": module.module_name,
                "Score": module.mastery_score * 100
            })
    
    if all_scores:
        score_df = pd.DataFrame(all_scores)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Score distribution
            fig = px.histogram(
                score_df,
                x="Score",
                nbins=20,
                title="Score Distribution",
                labels={"Score": "Mastery Score (%)"}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Module performance
            module_avg = score_df.groupby("Module")["Score"].mean().reset_index()
            fig = px.bar(
                module_avg,
                x="Module",
                y="Score",
                title="Average Score by Module"
            )
            st.plotly_chart(fig, use_container_width=True)


def main():
    """Main dashboard application"""
    
    # Initialize services
    profile_manager, cache_manager, event_handler = init_services()
    
    # Render header
    render_header()
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select View",
        ["System Health", "Student Overview", "Student Detail", "Performance Analytics", "Curriculum Adaptation"]
    )
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto-refresh (10s)", value=False)
    
    if auto_refresh:
        time.sleep(10)
        st.rerun()
    
    # Render selected page
    if page == "System Health":
        render_system_health(cache_manager, event_handler)
    
    elif page == "Student Overview":
        render_student_overview(profile_manager)
    
    elif page == "Student Detail":
        students = profile_manager.get_all_students()
        if students:
            student_ids = [s.student_id for s in students]
            selected_student = st.sidebar.selectbox("Select Student", student_ids)
            render_student_detail(profile_manager, selected_student)
        else:
            st.info("No students available")
    
    elif page == "Performance Analytics":
        render_performance_analytics(profile_manager)
    
    elif page == "Curriculum Adaptation":
        render_curriculum_adaptation()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**LearnPro v1.0**")
    st.sidebar.markdown("Agentic RAG Adaptive Learning")


if __name__ == "__main__":
    main()

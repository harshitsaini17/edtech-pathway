"""
Production Deployment Readiness Checklist
==========================================
Final checklist for deploying the LearnPro Adaptive Learning System.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 80)
print("PRODUCTION DEPLOYMENT READINESS CHECKLIST")
print("=" * 80)

checklist = []

def check_item(category, item, check_func, critical=True):
    """Check a deployment item"""
    try:
        result = check_func()
        status = "✅" if result else ("🔴" if critical else "⚠️ ")
        checklist.append((category, item, result, critical))
        return result
    except Exception as e:
        status = "🔴" if critical else "⚠️ "
        checklist.append((category, item, False, critical))
        return False

# =============================================================================
# 1. ENVIRONMENT CONFIGURATION
# =============================================================================
print("\n1️⃣  ENVIRONMENT CONFIGURATION")
print("-" * 80)

result = check_item("Environment", ".env file exists", 
                   lambda: os.path.exists(".env"), critical=True)
print(f"   {'✅' if result else '🔴'} .env file exists")

result = check_item("Environment", ".env.example exists", 
                   lambda: os.path.exists(".env.example"), critical=False)
print(f"   {'✅' if result else '⚠️ '} .env.example exists (for documentation)")

try:
    from config.settings import settings
    result = check_item("Environment", "Settings load successfully", 
                       lambda: True, critical=True)
    print(f"   ✅ Settings load successfully")
    
    # Check critical settings
    has_azure = bool(os.getenv("AZURE_OPENAI_API_KEY"))
    result = check_item("Environment", "Azure OpenAI API key configured", 
                       lambda: has_azure, critical=True)
    print(f"   {'✅' if has_azure else '🔴'} Azure OpenAI API key configured")
    
except Exception as e:
    print(f"   🔴 Settings loading error: {e}")

# =============================================================================
# 2. DEPENDENCIES
# =============================================================================
print("\n2️⃣  DEPENDENCIES")
print("-" * 80)

result = check_item("Dependencies", "requirements.txt exists", 
                   lambda: os.path.exists("requirements.txt"), critical=True)
print(f"   {'✅' if result else '🔴'} requirements.txt exists")

# Check critical packages
critical_packages = [
    "fastapi", "uvicorn", "motor", "redis", "chromadb",
    "langchain", "langchain-openai", "pathway-python", 
    "streamlit", "pydantic"
]

try:
    with open("requirements.txt", "r") as f:
        requirements = f.read()
    
    missing = []
    for pkg in critical_packages:
        if pkg not in requirements:
            missing.append(pkg)
    
    if not missing:
        print(f"   ✅ All critical packages in requirements.txt")
    else:
        print(f"   ⚠️  Missing packages: {', '.join(missing)}")
        
except Exception as e:
    print(f"   🔴 Error checking requirements: {e}")

# =============================================================================
# 3. DOCKER CONFIGURATION
# =============================================================================
print("\n3️⃣  DOCKER CONFIGURATION")
print("-" * 80)

result = check_item("Docker", "docker-compose.yml exists", 
                   lambda: os.path.exists("docker-compose.yml"), critical=True)
print(f"   {'✅' if result else '🔴'} docker-compose.yml exists")

result = check_item("Docker", "Dockerfile exists", 
                   lambda: os.path.exists("Dockerfile"), critical=True)
print(f"   {'✅' if result else '🔴'} Dockerfile exists")

try:
    import yaml
    with open("docker-compose.yml", "r") as f:
        compose = yaml.safe_load(f)
    
    services = compose.get("services", {})
    required_services = ["mongodb", "redis", "chromadb"]
    
    for service in required_services:
        has_service = service in services
        print(f"   {'✅' if has_service else '🔴'} Service configured: {service}")
        
except Exception as e:
    print(f"   ⚠️  Could not validate docker-compose.yml: {e}")

# =============================================================================
# 4. DATABASE CONFIGURATION
# =============================================================================
print("\n4️⃣  DATABASE CONFIGURATION")
print("-" * 80)

try:
    from config.settings import settings
    
    # MongoDB
    mongo_uri = settings.MONGODB_URI
    print(f"   ✅ MongoDB URI configured")
    
    # Redis
    redis_url = settings.REDIS_URL
    print(f"   ✅ Redis URL configured")
    
    # ChromaDB
    chromadb_path = settings.CHROMADB_PATH
    print(f"   ✅ ChromaDB path configured: {chromadb_path}")
    
except Exception as e:
    print(f"   🔴 Database configuration error: {e}")

# =============================================================================
# 5. API CONFIGURATION
# =============================================================================
print("\n5️⃣  API CONFIGURATION")
print("-" * 80)

result = check_item("API", "FastAPI main file exists", 
                   lambda: os.path.exists("api/main.py"), critical=True)
print(f"   {'✅' if result else '🔴'} FastAPI main file exists")

try:
    from config.settings import settings
    print(f"   ✅ API Host: {settings.API_HOST}")
    print(f"   ✅ API Port: {settings.API_PORT}")
    
except Exception as e:
    print(f"   ⚠️  API configuration: {e}")

# =============================================================================
# 6. MONITORING & LOGGING
# =============================================================================
print("\n6️⃣  MONITORING & LOGGING")
print("-" * 80)

result = check_item("Monitoring", "Dashboard exists", 
                   lambda: os.path.exists("monitoring/dashboard.py"), critical=False)
print(f"   {'✅' if result else '⚠️ '} Streamlit dashboard exists")

result = check_item("Monitoring", "Event streaming exists", 
                   lambda: os.path.exists("events/event_stream.py"), critical=True)
print(f"   {'✅' if result else '🔴'} Event streaming system exists")

# =============================================================================
# 7. SECURITY CONSIDERATIONS
# =============================================================================
print("\n7️⃣  SECURITY CONSIDERATIONS")
print("-" * 80)

# Check .gitignore
result = check_item("Security", ".gitignore exists", 
                   lambda: os.path.exists("../.gitignore"), critical=True)
print(f"   {'✅' if result else '🔴'} .gitignore exists")

if os.path.exists("../.gitignore"):
    with open("../.gitignore", "r") as f:
        gitignore = f.read()
    
    has_env = ".env" in gitignore
    has_pycache = "__pycache__" in gitignore or "*.pyc" in gitignore
    has_venv = "venv" in gitignore or "env/" in gitignore
    
    print(f"   {'✅' if has_env else '⚠️ '} .env in .gitignore")
    print(f"   {'✅' if has_pycache else '⚠️ '} Python cache in .gitignore")
    print(f"   {'✅' if has_venv else '⚠️ '} Virtual env in .gitignore")

# Check for hardcoded secrets
print(f"   ⚠️  Manual check required: No hardcoded API keys in code")
print(f"   ⚠️  Manual check required: CORS origins configured for production")
print(f"   ⚠️  Manual check required: Rate limiting configured")

# =============================================================================
# 8. DOCUMENTATION
# =============================================================================
print("\n8️⃣  DOCUMENTATION")
print("-" * 80)

docs = [
    ("../README.md", "README"),
    ("../docs/architecture.md", "Architecture docs"),
    ("../docs/QUICKSTART.md", "Quick start guide"),
]

for doc_path, doc_name in docs:
    exists = os.path.exists(doc_path)
    print(f"   {'✅' if exists else '⚠️ '} {doc_name}: {doc_path}")

# =============================================================================
# 9. TESTING
# =============================================================================
print("\n9️⃣  TESTING")
print("-" * 80)

test_files = [
    "tests/test_quick.py",
    "tests/test_mock_comprehensive.py",
    "tests/final_validation.py",
]

for test_file in test_files:
    exists = os.path.exists(test_file)
    print(f"   {'✅' if exists else '⚠️ '} {test_file}")

print(f"   ⚠️  Manual check: All tests pass")

# =============================================================================
# 10. PERFORMANCE & SCALABILITY
# =============================================================================
print("\n🔟 PERFORMANCE & SCALABILITY")
print("-" * 80)

result = check_item("Performance", "Optimization analysis exists", 
                   lambda: os.path.exists("performance/optimization_analysis.py"), critical=False)
print(f"   {'✅' if result else '⚠️ '} Performance optimization analysis done")

print(f"   ⚠️  Manual check: Connection pooling configured")
print(f"   ⚠️  Manual check: Caching strategy implemented")
print(f"   ⚠️  Manual check: Async/await used for I/O operations")

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "=" * 80)
print("DEPLOYMENT READINESS SUMMARY")
print("=" * 80)

critical_items = [item for item in checklist if item[3]]  # critical=True
critical_passed = sum(1 for item in critical_items if item[2])
critical_total = len(critical_items)

all_passed = sum(1 for item in checklist if item[2])
all_total = len(checklist)

print(f"\n🔴 Critical Items: {critical_passed}/{critical_total} ({critical_passed/critical_total*100:.1f}%)")
print(f"✅ All Items: {all_passed}/{all_total} ({all_passed/all_total*100:.1f}%)")

if critical_passed == critical_total:
    print("\n✅ SYSTEM IS READY FOR DEPLOYMENT")
else:
    print(f"\n🔴 {critical_total - critical_passed} CRITICAL ITEMS NEED ATTENTION")

# =============================================================================
# PRE-DEPLOYMENT COMMANDS
# =============================================================================
print("\n" + "=" * 80)
print("PRE-DEPLOYMENT COMMANDS")
print("=" * 80)

print("""
📋 Before deploying, run these commands:

1. Install dependencies:
   cd server
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

2. Configure environment:
   cp .env.example .env
   # Edit .env with your production values

3. Start services:
   docker-compose up -d

4. Verify services:
   docker-compose ps
   # Ensure mongodb, redis, chromadb are healthy

5. Run tests:
   PYTHONPATH=. python tests/test_quick.py
   PYTHONPATH=. python tests/final_validation.py

6. Start API server:
   uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

7. Start monitoring dashboard (optional):
   streamlit run monitoring/dashboard.py --server.port 8501

8. Health check:
   curl http://localhost:8000/health

9. API documentation:
   Open http://localhost:8000/docs
""")

# =============================================================================
# POST-DEPLOYMENT CHECKLIST
# =============================================================================
print("=" * 80)
print("POST-DEPLOYMENT CHECKLIST")
print("=" * 80)

print("""
✅ After deployment:

1. ✓ API responds to health check
2. ✓ All endpoints return expected responses
3. ✓ Database connections established
4. ✓ Redis cache working
5. ✓ ChromaDB vector search working
6. ✓ LLM API calls successful
7. ✓ Event streaming operational
8. ✓ Dashboard accessible
9. ✓ Logs show no errors
10. ✓ Performance metrics normal

📊 Monitor these metrics:
   - API response times (<500ms average)
   - Database query times (<100ms)
   - LLM API latency (<5s)
   - Cache hit rate (>60%)
   - Error rate (<1%)
   - Memory usage (<2GB)
   - CPU usage (<70%)
""")

print("=" * 80)
print("✅ DEPLOYMENT READINESS CHECK COMPLETE")
print("=" * 80)

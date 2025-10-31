# LearnPro - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites

- Docker & Docker Compose installed
- Python 3.11+
- Azure OpenAI API key
- 4GB RAM minimum

### Step 1: Clone & Configure

```bash
# Clone repository
git clone https://github.com/your-org/edtech-pathway.git
cd edtech-pathway/server

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required Environment Variables:**
```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/

# Azure OpenAI Deployments
AZURE_OPENAI_DEPLOYMENT_NAME_SYSTEM1=gpt-4
AZURE_OPENAI_DEPLOYMENT_NAME_SYSTEM2=gpt-4

# Database URLs (defaults for Docker)
MONGODB_URL=mongodb://admin:learnpro123@mongodb:27017/learnpro?authSource=admin
REDIS_URL=redis://redis:6379/0
```

### Step 2: Start Services

```bash
# Start all services with Docker Compose
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f api
```

**Services will be available at:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:8501
- MongoDB: localhost:27017
- Redis: localhost:6379
- ChromaDB: localhost:8001

### Step 3: Run Demo

```bash
# Install Python dependencies (if running locally)
pip install -r requirements.txt

# Run the demo script
python demo.py
```

The demo will:
1. ✅ Populate knowledge base with sample topics
2. ✅ Create a demo student profile
3. ✅ Generate and submit a quiz
4. ✅ Adapt curriculum based on performance
5. ✅ Show AI agent decisions
6. ✅ Display monitoring metrics

### Step 4: Explore the API

Open http://localhost:8000/docs for interactive API documentation.

**Try these endpoints:**

```bash
# Health check
curl http://localhost:8000/health

# Create student profile
curl -X POST "http://localhost:8000/api/v1/profile?student_id=alice&name=Alice&email=alice@example.com"

# Get student profile
curl http://localhost:8000/api/v1/profile/alice

# Generate quiz
curl -X POST http://localhost:8000/api/v1/quiz \
  -H "Content-Type: application/json" \
  -d '{"student_id":"alice","module_name":"Module1","num_questions":5}'

# Get next action recommendation
curl http://localhost:8000/api/v1/agent/next-action/alice
```

### Step 5: View Dashboard

Open http://localhost:8501 in your browser to see:
- 📊 System health metrics
- 👥 Student overview
- 📈 Performance analytics
- 🎯 Curriculum adaptations

## 📖 Common Tasks

### Add Educational Content

```bash
# Place PDF in doc/ directory
cp your-textbook.pdf server/doc/

# Extract topics
cd server
PYTHONPATH=/path/to/server python optimized_universal_extractor.py

# This creates topics JSON in output/
```

### Generate Curriculum

```bash
# Use extracted topics to create curriculum
PYTHONPATH=/path/to/server python llm_enhanced_curriculum_generator.py
```

### Generate Theory Content

```bash
# Create theory content for modules
PYTHONPATH=/path/to/server python flexible_module_theory_generator.py
```

### Run Tests

```bash
# Run comprehensive test suite
cd server
PYTHONPATH=/path/to/server python tests/test_all_phases.py

# Run specific phase test
PYTHONPATH=/path/to/server python tests/test_phase1.py
```

## 🔧 Troubleshooting

### Services Won't Start

```bash
# Check Docker status
docker ps -a

# View service logs
docker-compose logs mongodb
docker-compose logs redis
docker-compose logs api

# Restart services
docker-compose restart

# Full reset
docker-compose down -v
docker-compose up -d
```

### Database Connection Issues

```bash
# Test MongoDB connection
docker exec -it learnpro-mongodb mongosh -u admin -p learnpro123

# Test Redis connection
docker exec -it learnpro-redis redis-cli ping
```

### API Returns Errors

```bash
# Check API logs
docker-compose logs -f api

# Test health endpoint
curl http://localhost:8000/health

# Check environment variables
docker exec learnpro-api env | grep AZURE
```

### Cache Not Working

```bash
# Check Redis
docker exec -it learnpro-redis redis-cli

# Inside Redis CLI:
> PING  # Should return PONG
> INFO stats
> KEYS *
```

## 📚 Next Steps

1. **Read Documentation**
   - [Architecture](./architecture.md)
   - [API Documentation](./api_documentation.md)
   - [Deployment Guide](./deployment_guide.md)

2. **Customize**
   - Add your educational content
   - Configure LLM prompts
   - Adjust adaptation thresholds

3. **Integrate**
   - Connect your frontend
   - Setup authentication
   - Configure production databases

4. **Deploy**
   - Setup Kubernetes cluster
   - Configure load balancer
   - Setup monitoring (Prometheus/Grafana)

## 🆘 Getting Help

- **Documentation**: `/docs` directory
- **API Docs**: http://localhost:8000/docs
- **Issues**: GitHub Issues
- **Email**: support@learnpro.ai

## 🎯 Success Criteria

You should now have:
- ✅ All services running
- ✅ API accessible at port 8000
- ✅ Dashboard at port 8501
- ✅ Demo completed successfully
- ✅ Sample student created
- ✅ Quiz generated and analyzed

**Congratulations! Your adaptive learning system is ready!** 🎉

---

**Need more help?** Check out our comprehensive guides in the `/docs` folder.

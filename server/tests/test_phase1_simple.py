"""
Simple Phase 1 Test: Vector Store & Knowledge Base
===================================================
Test ChromaDB vector store setup without complex dependencies.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 80)
print("PHASE 1 TEST: VECTOR STORE & KNOWLEDGE BASE")
print("=" * 80)

print("\n1. Testing vector store import...")
try:
    from db.vector_store import VectorStore
    print("   ✅ VectorStore imported")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n2. Testing vector store initialization...")
try:
    vector_store = VectorStore()
    print("   ✅ Vector store initialized")
    print(f"   Collection name: {vector_store.collection.name}")
except Exception as e:
    print(f"   ❌ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n3. Testing document addition...")
try:
    test_doc = {
        "content": "This is a test document about machine learning basics.",
        "metadata": {
            "source": "test",
            "module": "Test_Module"
        }
    }
    print("   → Adding test document...")
    doc_id = vector_store.add_document(
        content=test_doc["content"],
        metadata=test_doc["metadata"]
    )
    print(f"   ✅ Document added: {doc_id}")
except Exception as e:
    print(f"   ❌ Add failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n4. Testing semantic search...")
try:
    print("   → Searching for 'machine learning'...")
    results = vector_store.search(
        query="machine learning basics",
        limit=5
    )
    print(f"   ✅ Search returned {len(results)} results")
    
    if results:
        print(f"   First result score: {results[0]['score']:.4f}")
        print(f"   First result content (truncated): {results[0]['content'][:50]}...")
except Exception as e:
    print(f"   ❌ Search failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n5. Testing metadata filtering...")
try:
    print("   → Searching with module filter...")
    results = vector_store.search(
        query="test",
        limit=5,
        filter_metadata={"module": "Test_Module"}
    )
    print(f"   ✅ Filtered search returned {len(results)} results")
except Exception as e:
    print(f"   ❌ Filtered search failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n6. Testing collection statistics...")
try:
    count = vector_store.collection.count()
    print(f"   ✅ Collection has {count} documents")
except Exception as e:
    print(f"   ❌ Stats failed: {e}")
    sys.exit(1)

print("\n✅ PHASE 1 TEST PASSED")
print("=" * 80)

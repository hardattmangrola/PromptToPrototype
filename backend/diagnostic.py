#!/usr/bin/env python3
"""
Diagnostic script to test Groq, Gemini, Pinecone, and embedding sync.
Run: python diagnostic.py
"""
import asyncio
import json
import sys
from typing import Any, Dict, Optional

# Load .env
from dotenv import load_dotenv
load_dotenv()

import os
from app.config import get_settings

async def test_groq() -> Dict[str, Any]:
    """Test Groq API connection and basic call."""
    print("\n" + "="*60)
    print("TESTING GROQ API")
    print("="*60)
    
    settings = get_settings()
    
    if not settings.groq_api_key:
        return {"status": "FAILED", "reason": "GROQ_API_KEY not set"}
    
    print(f"API Key: {settings.groq_api_key[:20]}...")
    print(f"Model: {settings.groq_model}")
    
    try:
        from groq import Groq
        client = Groq(api_key=settings.groq_api_key)
        
        resp = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Groq is working' in JSON: {\"status\": \"ok\", \"message\": \"...\"}"}
            ],
            temperature=0.2,
            max_tokens=100,
        )
        
        text = resp.choices[0].message.content or ""
        print(f"Response: {text[:100]}...")
        return {"status": "SUCCESS", "response": text}
    
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: {error_msg}")
        return {"status": "FAILED", "reason": error_msg}

async def test_gemini() -> Dict[str, Any]:
    """Test Gemini API connection and basic call."""
    print("\n" + "="*60)
    print("TESTING GEMINI API")
    print("="*60)
    
    settings = get_settings()
    
    if not settings.gemini_api_key:
        return {"status": "FAILED", "reason": "GEMINI_API_KEY not set"}
    
    print(f"API Key: {settings.gemini_api_key[:20]}...")
    print(f"Model: {settings.gemini_model}")
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(
            settings.gemini_model,
            system_instruction="You are a helpful assistant."
        )
        
        resp = model.generate_content(
            'Say "Gemini is working" in JSON: {"status": "ok", "message": "..."}'
        )
        
        text = resp.text or ""
        print(f"Response: {text[:100]}...")
        return {"status": "SUCCESS", "response": text}
    
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: {error_msg}")
        return {"status": "FAILED", "reason": error_msg}

async def test_pinecone() -> Dict[str, Any]:
    """Test Pinecone connection and index information."""
    print("\n" + "="*60)
    print("TESTING PINECONE CONNECTION")
    print("="*60)
    
    settings = get_settings()
    
    if not settings.pinecone_api_key:
        return {"status": "FAILED", "reason": "PINECONE_API_KEY not set"}
    
    print(f"API Key: {settings.pinecone_api_key[:20]}...")
    print(f"Indexes: dense={settings.pinecone_index_dense}, sparse={settings.pinecone_index_sparse}")
    
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=settings.pinecone_api_key)
        
        # List indexes
        indexes = pc.list_indexes()
        print(f"\nAvailable indexes: {[idx.name for idx in indexes.indexes]}")
        
        # Check dense index
        try:
            dense_idx = pc.Index(settings.pinecone_index_dense)
            stats = dense_idx.describe_index_stats()
            print(f"\nDense Index ({settings.pinecone_index_dense}):")
            print(f"  Dimension: {stats.dimension if hasattr(stats, 'dimension') else 'N/A'}")
            print(f"  Namespaces: {len(stats.namespaces) if hasattr(stats, 'namespaces') else 0}")
            print(f"  Vector count: {stats.total_vector_count if hasattr(stats, 'total_vector_count') else 'N/A'}")
        except Exception as e:
            print(f"Dense index error: {e}")
        
        # Check sparse index
        try:
            sparse_idx = pc.Index(settings.pinecone_index_sparse)
            stats = sparse_idx.describe_index_stats()
            print(f"\nSparse Index ({settings.pinecone_index_sparse}):")
            print(f"  Dimension: {stats.dimension if hasattr(stats, 'dimension') else 'N/A'}")
            print(f"  Namespaces: {len(stats.namespaces) if hasattr(stats, 'namespaces') else 0}")
            print(f"  Vector count: {stats.total_vector_count if hasattr(stats, 'total_vector_count') else 'N/A'}")
        except Exception as e:
            print(f"Sparse index error: {e}")
        
        return {"status": "SUCCESS", "index_names": [idx.name for idx in indexes.indexes]}
    
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: {error_msg}")
        return {"status": "FAILED", "reason": error_msg}

async def test_embeddings() -> Dict[str, Any]:
    """Test embedding generation."""
    print("\n" + "="*60)
    print("TESTING EMBEDDINGS")
    print("="*60)
    
    settings = get_settings()
    
    test_text = "What is the patient's name?"
    
    try:
        from app.services.embeddings import embed_query_dense, embed_query_sparse
        
        # Test dense
        dense = await embed_query_dense(test_text)
        print(f"Dense embedding: {len(dense)} dimensions")
        print(f"  Expected: {settings.dense_embedding_dimension}")
        print(f"  Match: {'✓' if len(dense) == settings.dense_embedding_dimension else '✗ MISMATCH'}")
        
        # Test sparse
        sparse = await embed_query_sparse(test_text)
        print(f"\nSparse embedding: {len(sparse)} dimensions")
        print(f"  Expected: {settings.sparse_embedding_dimension}")
        print(f"  Match: {'✓' if len(sparse) == settings.sparse_embedding_dimension else '✗ MISMATCH'}")
        
        return {
            "status": "SUCCESS",
            "dense_dim": len(dense),
            "sparse_dim": len(sparse),
            "expected_dense": settings.dense_embedding_dimension,
            "expected_sparse": settings.sparse_embedding_dimension,
        }
    
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return {"status": "FAILED", "reason": error_msg}

async def test_mongodb() -> Dict[str, Any]:
    """Test MongoDB connection."""
    print("\n" + "="*60)
    print("TESTING MONGODB")
    print("="*60)
    
    settings = get_settings()
    
    if not settings.mongodb_uri:
        return {"status": "FAILED", "reason": "MONGODB_URI not set"}
    
    print(f"URI: {settings.mongodb_uri[:50]}...")
    print(f"DB: {settings.mongodb_db_name}")
    
    try:
        from motor.motor_asyncio import AsyncClient
        client = AsyncClient(settings.mongodb_uri)
        db = client[settings.mongodb_db_name]
        
        # Try to ping
        await client.admin.command('ping')
        print("Connection: ✓ SUCCESS")
        
        # List collections
        collections = await db.list_collection_names()
        print(f"Collections: {collections}")
        
        return {"status": "SUCCESS", "collections": collections}
    
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: {error_msg}")
        return {"status": "FAILED", "reason": error_msg}

async def main():
    """Run all diagnostics."""
    print("\n" + "="*60)
    print("HEALTHCARE RAG SYSTEM DIAGNOSTICS")
    print("="*60)
    
    results = {
        "groq": await test_groq(),
        "gemini": await test_gemini(),
        "pinecone": await test_pinecone(),
        "embeddings": await test_embeddings(),
        "mongodb": await test_mongodb(),
    }
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for component, result in results.items():
        status = result.get("status", "UNKNOWN")
        emoji = "✓" if status == "SUCCESS" else "✗"
        print(f"{emoji} {component.upper()}: {status}")
        if status == "FAILED":
            print(f"  Reason: {result.get('reason', 'Unknown')}")
    
    # Overall status
    all_success = all(r.get("status") == "SUCCESS" for r in results.values())
    print("\n" + "="*60)
    if all_success:
        print("ALL SYSTEMS OPERATIONAL ✓")
    else:
        print("SOME SYSTEMS HAVE ISSUES ✗")
        print("\nPlease fix the errors above before running the RAG system.")
    print("="*60 + "\n")
    
    return all_success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

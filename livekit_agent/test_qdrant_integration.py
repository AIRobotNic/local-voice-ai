#!/usr/bin/env python3
"""
Simple test to verify Qdrant integration in the agent
"""
import sys
import os

# Add the src directory to the path so we can import the agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from agent import Assistant
    print("✓ Successfully imported Assistant class")
    
    # Test creating an assistant instance
    assistant = Assistant()
    print("✓ Successfully created Assistant instance")
    
    # Test that Qdrant client is initialized
    if hasattr(assistant, 'qdrant_client'):
        print("✓ Qdrant client initialized successfully")
        print(f"✓ Qdrant client host: {assistant.qdrant_client._host}")
        print(f"✓ Qdrant client port: {assistant.qdrant_client._port}")
    else:
        print("✗ Qdrant client not found in assistant")
        sys.exit(1)
        
    # Test that the memory functions exist
    if hasattr(assistant, 'store_memory'):
        print("✓ store_memory function found")
    else:
        print("✗ store_memory function not found")
        sys.exit(1)
        
    if hasattr(assistant, 'retrieve_memory'):
        print("✓ retrieve_memory function found")
    else:
        print("✗ retrieve_memory function not found")
        sys.exit(1)
        
    print("✓ All Qdrant integration tests passed!")
    
except Exception as e:
    print(f"✗ Error during test: {e}")
    sys.exit(1)
A Feynman-Enhanced Learning Agent Using LangGraph
Overview

This notebook presents a structured learning agent implemented using LangGraph. The system guides learners through a sequence of defined but customizable checkpoints, verifying understanding at each step and providing Feynman-style teaching when needed.
Motivation

In traditional educational settings, access to personalized 1:1 tutoring is often limited by cost and availability. This project aims to democratize personalized learning by creating an AI tutor that can:

    Provide individualized attention and feedback 24/7
    Use your own notes and web-retrieved content as context
    Offer patient, simple explanations of complex topics

Key Components

    Learning State Graph: Orchestrates the sequential learning workflow
    Checkpoint System: Defines structured learning milestones
    Web Search Integration: Dynamically retrieves relevant learning materials
    Context Processing: Chunks and processes learning materials
    Question Generation: Creates checkpoint-specific verification questions
    Understanding Verification: Evaluates learner comprehension with a clear threshold (70%)
    Feynman Teaching: Simplifies complex concepts when understanding is insufficient

Method

The system follows a structured learning cycle:
1. Checkpoint Definition

    Generates sequential learning milestones with clear success criteria

2. Context Building

    Processes student-provided materials or retrieves relevant web content

3. Context Validation

    Validates context based on checkpoint criteria
    Performs additional web searches if context doesn't meet checkpoint requirements

4. Embedding Storage

    Stores embeddings for retrieving only relevant chunks during verification

5. Understanding Verification

    Generates checkpoint-specific questions
    Evaluates responses against a 70% understanding threshold
    Provides detailed feedback

6. Progressive Learning

    Advances to the next checkpoint when understanding is verified
    Provides Feynman-style explanations when needed


![image](https://github.com/user-attachments/assets/0e3c6df1-de70-4231-989f-34ac11d83e2d)

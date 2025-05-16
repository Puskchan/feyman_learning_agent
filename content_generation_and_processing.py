import os
from data_models import LearningtState
from dotenv import load_dotenv
from data_models import LearningtState, SearchQuery, Checkpoints, InContext, FeynmanTeaching, QuestionOutput, LearningVerification

from prompts import (
    checkpoint_based_query_generator,
    learning_checkpoints_generator,
    validate_context,
    feynman_teacher,
    question_generator,
    answer_verifier
)

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utils.math import cosine_similarity
from langchain_groq import ChatGroq
from langchain.embeddings import HuggingFaceEmbeddings
from context_storage import ContextStore
from utils import format_checkpoints_as_message, extract_content_from_chunks, generate_checkpoint_message
from langchain_core.messages import HumanMessage, SystemMessage
from semantic_chunker import get_chunker


load_dotenv()

api_key = os.getenv("GROQ_KEY")

tavily_search = TavilySearchResults(max_results=3)
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=api_key)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

context_store = ContextStore()

def generate_query(state: LearningtState):
    """Generates search queries based on learning checkpoints from current state."""
    structured_llm = llm.with_structured_output(SearchQuery) 
    checkpoints_message = HumanMessage(content=format_checkpoints_as_message(state['checkpoints']))  
    messages = [checkpoint_based_query_generator, checkpoints_message]
    search_queries = structured_llm.invoke(messages)
    return {"search_queries": search_queries}

def search_web(state: LearningtState):
    """Retrieves and processes web search results based on search queries."""
    search_queries = state["search_queries"].search_queries
    
    all_search_docs = []
    for query in search_queries:
        search_docs = tavily_search.invoke(query)
        all_search_docs.extend(search_docs)
    
    formatted_search_docs = [
        f'Context: {doc["content"]}\n Source: {doc["url"]}\n'
        for doc in all_search_docs
    ]

    chunk_embeddings = embeddings.embed_documents(formatted_search_docs)
    context_key = context_store.save_context(
        formatted_search_docs,
        chunk_embeddings,
        key=state.get('context_key')
    )
    
    return {"context_chunks": formatted_search_docs}

def generate_checkpoints(state: LearningtState):
    """Creates learning checkpoints based on given topic and goals."""
    structured_llm = llm.with_structured_output(Checkpoints)
    messages = [
        learning_checkpoints_generator,
        SystemMessage(content=f"Topic: {state['topic']}"),
        SystemMessage(content=f"Goals: {', '.join(str(goal) for goal in state['goals'])}")
    ]
    checkpoints = structured_llm.invoke(messages)
    return {"checkpoints": checkpoints}

def chunk_context(state: LearningtState):
    """Splits context into manageable chunks and generates their embeddings."""
    encoder = embeddings
    chunker = get_chunker(
        "gpt-3.5-turbo",
        chunking_type="text",  
        max_tokens=1500,  
        trim=False,  
        overlap=100,
    )
    
    chunks = chunker.chunks([state['context']])
    content = []
    for chunk in chunks:
        content.append(extract_content_from_chunks(chunk))

    chunk_embeddings = embeddings.embed_documents(content)
    context_key = context_store.save_context(
        content,
        chunk_embeddings,
        key=state.get('context_key')
    )
    return {"context_chunks": content, "context_key": context_key}

def context_validation(state: LearningtState):
    """Validates context coverage against checkpoint criteria using stored embeddings."""
    context = context_store.get_context(state['context_key'])
    chunks = context['chunks']
    chunk_embeddings = context['embeddings']
    
    checks = []
    structured_llm = llm.with_structured_output(InContext)
    
    for checkpoint in state['checkpoints'].checkpoints:
        query = embeddings.embed_query(checkpoint.verification)
        
        similarities = cosine_similarity([query], chunk_embeddings)[0]
        top_3_indices = sorted(range(len(similarities)), 
                             key=lambda i: similarities[i], 
                             reverse=True)[:3]
        relevant_chunks = [chunks[i] for i in top_3_indices]
        
        messages = [
            validate_context,
            HumanMessage(content=f"""
            Criteria:
            {chr(10).join(f"- {c}" for c in checkpoint.criteria)}
            
            Context:
            {chr(10).join(relevant_chunks)}
            """)
        ]
        
        response = structured_llm.invoke(messages)
        if response.is_in_context.lower() == "no":
            checks.append(checkpoint)
    
    if checks:
        structured_llm = llm.with_structured_output(SearchQuery)
        checkpoints_message = generate_checkpoint_message(checks)
        
        messages = [checkpoint_based_query_generator, checkpoints_message]
        search_queries = structured_llm.invoke(messages)
        return {"search_queries": search_queries}
    
    return {"search_queries": None}

def generate_question(state: LearningtState):
    """Generates assessment questions based on current checkpoint verification requirements."""
    structured_llm = llm.with_structured_output(QuestionOutput)
    current_checkpoint = state['current_checkpoint']
    checkpoint_info = state['checkpoints'].checkpoints[current_checkpoint]
    
    messages = [
        question_generator,
        HumanMessage(content=f"""
        Checkpoint Description: {checkpoint_info.description}
        Success Criteria:
        {chr(10).join(f"- {c}" for c in checkpoint_info.criteria)}
        Verification Method: {checkpoint_info.verification}
        
        Generate an appropriate verification question.""")
    ]
    
    question_output = structured_llm.invoke(messages)
    return {"current_question": question_output.question}

def verify_answer(state: LearningtState):
    """Evaluates user answers against checkpoint criteria using relevant context chunks."""
    structured_llm = llm.with_structured_output(LearningVerification)
    current_checkpoint = state['current_checkpoint']
    checkpoint_info = state['checkpoints'].checkpoints[current_checkpoint]
    
    context = context_store.get_context(state['context_key'])
    chunks = context['chunks']
    chunk_embeddings = context['embeddings']
    
    query = embeddings.embed_query(checkpoint_info.verification)
    
    similarities = cosine_similarity([query], chunk_embeddings)[0]
    top_3_indices = sorted(range(len(similarities)), 
                         key=lambda i: similarities[i], 
                         reverse=True)[:3]
    relevant_chunks = [chunks[i] for i in top_3_indices]
    
    messages = [
        answer_verifier,
        HumanMessage(content=f"""
        Question: {state['current_question']}
        Answer: {state['current_answer']}
        
        Checkpoint Description: {checkpoint_info.description}
        Success Criteria:
        {chr(10).join(f"- {c}" for c in checkpoint_info.criteria)}
        Verification Method: {checkpoint_info.verification}
        
        Context:
        {chr(10).join(relevant_chunks)}
        
        Assess the answer.""")
    ]
    
    verification = structured_llm.invoke(messages)
    return {"verifications": verification}
    
def teach_concept(state: LearningtState):
    """Creates simplified Feynman-style explanations for concepts that need reinforcement."""
    structured_llm = llm.with_structured_output(FeynmanTeaching)
    current_checkpoint = state['current_checkpoint']
    checkpoint_info = state['checkpoints'].checkpoints[current_checkpoint]
    
    messages = [
        feynman_teacher,
        HumanMessage(content=f"""
        Criteria: {checkpoint_info.criteria}
        Verification: {state['verifications']}
        
        Context:
        {state['context_chunks']}
        
        Create a Feynman teaching explanation.""")
    ]
    
    teaching = structured_llm.invoke(messages)
    return {"teachings": teaching}
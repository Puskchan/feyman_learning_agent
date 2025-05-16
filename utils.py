from langchain_core.messages import HumanMessage
from data_models import Checkpoints, LearningCheckpoint, LearningtState
from typing import List
from langgraph.graph import END


def extract_content_from_chunks(chunks):
    """Extract and combine content from chunks with splits attribute.
    
    Args:
        chunks: List of chunk objects that may contain splits attribute
        
    Returns:
        str: Combined content from all chunks joined with newlines
    """
    content = []
    
    for chunk in chunks:
        if hasattr(chunk, 'splits') and chunk.splits:
            chunk_content = ' '.join(chunk.splits)
            content.append(chunk_content)
    
    return '\n'.join(content)

def format_checkpoints_as_message(checkpoints: Checkpoints) -> str:
    """Convert Checkpoints object to a formatted string for the message.
    
    Args:
        checkpoints (Checkpoints): Checkpoints object containing learning checkpoints
        
    Returns:
        str: Formatted string containing numbered checkpoints with descriptions and criteria
    """
    message = "Here are the learning checkpoints:\n\n"
    for i, checkpoint in enumerate(checkpoints.checkpoints, 1):
        message += f"Checkpoint {i}:\n"
        message += f"Description: {checkpoint.description}\n"
        message += "Success Criteria:\n"
        for criterion in checkpoint.criteria:
            message += f"- {criterion}\n"
    return message

def generate_checkpoint_message(checks: List[LearningCheckpoint]) -> HumanMessage:
    """Generate a formatted message for learning checkpoints that need context.
    
    Args:
        checks (List[LearningCheckpoint]): List of learning checkpoint objects
        
    Returns:
        HumanMessage: Formatted message containing checkpoint descriptions, criteria and 
                     verification methods, ready for context search
    """
    formatted_checks = []
    
    for check in checks:
        checkpoint_text = f"""
        Description: {check.description}
        Success Criteria:
        {chr(10).join(f'- {criterion}' for criterion in check.criteria)}
        Verification Method: {check.verification}
        """
        formatted_checks.append(checkpoint_text)
    
    all_checks = "\n---\n".join(formatted_checks)
    
    checkpoints_message = HumanMessage(content=f"""The following learning checkpoints need additional context:
        {all_checks}
        
        Please generate search queries to find relevant information.""")
    
    return checkpoints_message


# User input handlers
def user_answer(state: LearningtState):
    """Placeholder for handling user's answer input."""
    pass

def next_checkpoint(state: LearningtState):
    """Advances to the next checkpoint in the learning sequence."""
    current_checkpoint = state['current_checkpoint'] + 1
    return {'current_checkpoint': current_checkpoint}

# Routing Logic Functions
def route_context(state: LearningtState):
    """Determines whether to process existing context or generate new search queries."""
    if state.get("context"):
        return 'chunk_context'
    return 'generate_query'

def route_verification(state: LearningtState):
    """Determines next step based on verification results and checkpoint progress."""
    current_checkpoint = state['current_checkpoint']
    
    if state['verifications'].understanding_level < 0.7:
        return 'teach_concept'
        
    if current_checkpoint + 1 < len(state['checkpoints'].checkpoints):
        return 'next_checkpoint'
    
    return END

def route_teaching(state: LearningtState):
    """Routes to next checkpoint or ends session after teaching intervention."""
    current_checkpoint = state['current_checkpoint']
    if current_checkpoint + 1 < len(state['checkpoints'].checkpoints):
        return 'next_checkpoint'
    return END

def route_search(state: LearningtState):
    """Directs flow between question generation and web search based on query status."""
    if state['search_queries'] is None:
        return "generate_question"
    return "search_web"


# Utility Functions
def print_checkpoints(event):
    """Pretty print checkpoints information with improved visual formatting"""
    checkpoints = event.get('checkpoints', '')
    if checkpoints:
        print("\n" + "=" * 80)
        print("🎯 LEARNING CHECKPOINTS OVERVIEW".center(80))
        print("=" * 80 + "\n")
        
        for i, checkpoint in enumerate(checkpoints.checkpoints, 1):
            # Checkpoint header with number
            print(f"📍 CHECKPOINT #{i}".center(80))
            print("─" * 80 + "\n")
            
            # Description section with text wrapping
            print("📝 Description:")
            print("─" * 40)
            words = checkpoint.description.split()
            current_line = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + 1 <= 70:
                    current_line.append(word)
                    current_length += len(word) + 1
                else:
                    print(f"  {' '.join(current_line)}")
                    current_line = [word]
                    current_length = len(word)
            
            if current_line:
                print(f"  {' '.join(current_line)}")
            print()
            
            # Success Criteria section
            print("✅ Success Criteria:")
            print("─" * 40)
            for j, criterion in enumerate(checkpoint.criteria, 1):
                # Wrap each criterion text
                words = criterion.split()
                current_line = []
                current_length = 0
                first_line = True
                
                for word in words:
                    if current_length + len(word) + 1 <= 66:  # Shorter width to account for numbering
                        current_line.append(word)
                        current_length += len(word) + 1
                    else:
                        if first_line:
                            print(f"  {j}. {' '.join(current_line)}")
                            first_line = False
                        else:
                            print(f"     {' '.join(current_line)}")
                        current_line = [word]
                        current_length = len(word)
                
                if current_line:
                    if first_line:
                        print(f"  {j}. {' '.join(current_line)}")
                    else:
                        print(f"     {' '.join(current_line)}")
            print()
            
            # Verification Method section
            print("🔍 Verification Method:")
            print("─" * 40)
            words = checkpoint.verification.split()
            current_line = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + 1 <= 70:
                    current_line.append(word)
                    current_length += len(word) + 1
                else:
                    print(f"  {' '.join(current_line)}")
                    current_line = [word]
                    current_length = len(word)
            
            if current_line:
                print(f"  {' '.join(current_line)}")
            print()
            
            # Separator between checkpoints
            if i < len(checkpoints.checkpoints):
                print("~" * 80 + "\n")
        
        print("=" * 80 + "\n")

def print_verification_results(event):
    """Pretty print verification results with improved formatting"""
    verifications = event.get('verifications', '')
    if verifications:
        print("\n" + "=" * 50)
        print("📊 VERIFICATION RESULTS".center(50))
        print("=" * 50 + "\n")

        # Understanding Level with visual bar
        understanding = verifications.understanding_level
        bar_length = 20
        filled_length = int(understanding * bar_length)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        print(f"📈 Understanding Level: [{bar}] {understanding * 100:.1f}%\n")
        
        # Feedback section
        print("💡 Feedback:")
        print(f"{verifications.feedback}\n")
        
        # Suggestions section
        print("🎯 Suggestions:")
        for i, suggestion in enumerate(verifications.suggestions, 1):
            print(f"  {i}. {suggestion}")
        print()
        
        # Context Alignment
        print("🔍 Context Alignment:")
        print(f"{verifications.context_alignment}\n")
        
        print("-" * 50 + "\n")
def print_teaching_results(event):
    """Pretty print Feynman teaching results with improved formatting"""
    teachings = event.get('teachings', '')
    if teachings:
        print("\n" + "=" * 70)
        print("🎓 FEYNMAN TEACHING EXPLANATION".center(70))
        print("=" * 70 + "\n")

        # Simplified Explanation section
        print("📚 SIMPLIFIED EXPLANATION:")
        print("─" * 30)
        # Split explanation into paragraphs for better readability
        paragraphs = teachings.simplified_explanation.split('\n')
        for paragraph in paragraphs:
            # Wrap text at 60 characters for better readability
            words = paragraph.split()
            lines = []
            current_line = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + 1 <= 60:
                    current_line.append(word)
                    current_length += len(word) + 1
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = len(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            for line in lines:
                print(f"{line}")
            print()
        
        # Key Concepts section
        print("💡 KEY CONCEPTS:")
        print("─" * 30)
        for i, concept in enumerate(teachings.key_concepts, 1):
            print(f"  {i}. {concept}")
        print()
        
        # Analogies section
        print("🔄 ANALOGIES & EXAMPLES:")
        print("─" * 30)
        for i, analogy in enumerate(teachings.analogies, 1):
            print(f"  {i}. {analogy}")
        print()
        
        print("=" * 70 + "\n")
# from utils import print_checkpoints
from langgraph.graph import END, START, StateGraph
from data_models import LearningtState
from context_storage import ContextStore
from langgraph.checkpoint.memory import MemorySaver
from utils import (
    next_checkpoint,
    user_answer,
    route_context,
    route_search,
    route_verification,
    route_teaching
)

from content_generation_and_processing import (
    generate_query,
    search_web,
    chunk_context,
    context_validation,
    generate_checkpoints,
    generate_question,
    verify_answer,
    teach_concept
)

from IPython.display import Image, display


searcher = StateGraph(LearningtState)
memory = MemorySaver()
context_store = ContextStore()

searcher.add_node("generate_query", generate_query)
searcher.add_node("search_web", search_web)
searcher.add_node("chunk_context", chunk_context)
searcher.add_node("context_validation", context_validation)
searcher.add_node("generate_checkpoints", generate_checkpoints)
searcher.add_node("generate_question", generate_question)
searcher.add_node("next_checkpoint", next_checkpoint)
searcher.add_node("user_answer", user_answer)
searcher.add_node("verify_answer", verify_answer)
searcher.add_node("teach_concept", teach_concept)

# Flow
searcher.add_edge(START, "generate_checkpoints")
searcher.add_conditional_edges('generate_checkpoints', route_context,['chunk_context', 'generate_query'])
searcher.add_edge("generate_query", "search_web")
searcher.add_edge("search_web", "generate_question")
searcher.add_edge("chunk_context", 'context_validation')
searcher.add_conditional_edges('context_validation', route_search,['search_web', 'generate_question'])

searcher.add_edge("generate_question", "user_answer")
searcher.add_edge("user_answer", "verify_answer")
searcher.add_conditional_edges(
    "verify_answer",
    route_verification,
    {
        "next_checkpoint": "next_checkpoint",
        "teach_concept": "teach_concept",
        END: END
    }
)

searcher.add_conditional_edges(
    "teach_concept",
    route_teaching,
    {
        "next_checkpoint": "next_checkpoint",
        END: END
    }
)
searcher.add_edge("next_checkpoint", "generate_question")



graph = searcher.compile(interrupt_after=["generate_checkpoints"], interrupt_before=["user_answer"], checkpointer=memory)

display(Image(graph.get_graph(xray=1).draw_mermaid_png()))


note = """Anemia: A Comprehensive Overview
Definition
Anemia is a medical condition characterized by a decrease in the total number of red blood cells (RBCs) or hemoglobin in the blood. This reduction leads to a diminished ability to carry oxygen to the body's tissues, affecting overall body function and health.
Blood Components and Their Role
Red blood cells, also known as erythrocytes, are fundamental components of blood that carry oxygen throughout the body. These cells contain hemoglobin, an iron-containing protein that gives blood its characteristic red color and is responsible for oxygen transport. The typical lifespan of a red blood cell is approximately 120 days, after which it must be replaced by new cells produced in the bone marrow.
Types of Anemia
Iron Deficiency Anemia represents the most prevalent form of anemia worldwide. It occurs due to insufficient iron intake or absorption, particularly affecting pregnant women, growing children, menstruating women, and individuals with poor nutritional intake.
Vitamin Deficiency Anemia develops when the body lacks sufficient amounts of vitamin B12 or folate (vitamin B9). This deficiency can stem from dietary inadequacies or problems with nutrient absorption in the digestive system.
Aplastic Anemia, though rare, presents a serious condition where the bone marrow fails to produce adequate blood cells. This form can be either inherited through genetic factors or acquired through various environmental causes or medical conditions.
Hemolytic Anemia occurs when red blood cells are destroyed at a rate faster than the body can replace them. This condition may be inherited through genetic factors or acquired through various external causes.
Clinical Manifestations
Anemia manifests through various symptoms including persistent fatigue and weakness. Patients often present with pale or yellowish skin, experience shortness of breath, and may suffer from dizziness. Additional symptoms include irregular heartbeat patterns, frequent headaches, cold extremities, and occasional chest pain.
Diagnostic Approach
Diagnosis begins with a thorough physical examination by a healthcare provider. Blood tests form the cornerstone of diagnosis, including a Complete Blood Count (CBC), assessment of iron levels, vitamin B12 measurement, and folate level determination. These tests help identify the specific type of anemia and guide appropriate treatment.
Treatment Strategies
Dietary modification serves as a fundamental treatment approach. This involves increasing consumption of iron-rich foods such as red meat, dark leafy vegetables, legumes, and iron-fortified cereals.
Supplementation often proves necessary and may include iron supplements, vitamin B12, or folic acid, depending on the underlying cause of anemia.
Medical interventions become necessary in severe cases. Blood transfusions may be required for severe anemia, while bone marrow transplantation might be considered for cases of aplastic anemia.
Preventive Measures
Prevention centers on maintaining a balanced diet rich in essential nutrients, particularly iron, vitamin B12, folate, and vitamin C, which enhances iron absorption. Regular medical check-ups allow for early detection and intervention.
Certain populations require special attention regarding prevention. These include pregnant women, menstruating women, growing children, individuals following vegetarian or vegan diets, and athletes who may have increased nutritional demands.
Potential Complications
Untreated anemia can lead to several serious complications. These include severe fatigue that impacts daily activities, complications during pregnancy, cardiovascular problems, depression, and cognitive difficulties that may affect work or school performance.
Clinical Significance
Anemia often serves as an indicator of other underlying medical conditions. Therefore, early detection and appropriate treatment prove crucial for optimal outcomes. Different forms of anemia require specific treatment approaches, and regular monitoring may be necessary to ensure treatment effectiveness."""

initial_input = {
    "topic": "Anemia",
    'goals': ['Im medical student, i want to master the diagnosis of Anemia'],
    'context': note,
    'current_checkpoint': 0}

thread = {"configurable": {"thread_id": "20"}}

for event in graph.stream(initial_input, thread, stream_mode="values"):
    print_checkpoints(event)

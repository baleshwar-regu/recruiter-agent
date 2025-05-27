import time
from typing import List, Tuple
from pydantic_ai.messages import ModelMessage
from agents.interview_agent import interview_agent
from models.agent_dependencies import AgentDependencies
from db.candidate_repository import get_candidate_by_id
from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

PERSONA_RESPONSES = {
    "strong": {
        "Greeting": "I'm doing great, thank you! Yes, this is a good time to speak.",
        "StatusCheck": "No, I have not interviewed with Bain before.",
        "ExperienceYears": "I have 12 years of experience in software engineering.",
        "CurrentProject": "I'm currently leading a CRM system rewrite using C# and Azure.",
        "Responsibilities": "I'm responsible for backend architecture, team mentorship, and code quality.",
        "Architecture": "We use a microservices-based architecture with Azure Functions and Service Bus.",
        "TechChoices": "We picked Azure App Services for cost efficiency and scalability.",
        "TradeOffs": "We traded off flexibility for simplicity by using managed services.",
        "Cloud": "I work extensively with Azure, including Azure DevOps and App Services.",
        "DistributedSystems": "Yes, I've built event-driven platforms using queues and stream processing.",
        "CSharp": "An abstract class can have implementations, fields, and constructors. An interface is purely a contract.",
        "SQL": "To find duplicates, I'd use GROUP BY with HAVING COUNT(*) > 1.",
        "Indexing": "I typically use composite and filtered indexes for performance.",
        "CI_CD": "We use multi-stage YAML pipelines in Azure DevOps with automated testing.",
        "DevOps": "We follow GitFlow, use pull request validation, and deploy using pipelines.",
        "Questions": "What are the next steps in the hiring process?"
    },
    "mediocre": {
        "Greeting": "I'm fine, yeah this works.",
        "StatusCheck": "No, not yet.",
        "ExperienceYears": "About 6 years maybe.",
        "CurrentProject": "Working on an internal tool for task tracking.",
        "Responsibilities": "Mainly writing APIs and fixing bugs.",
        "Architecture": "I think it's a monolith, not sure.",
        "TechChoices": "Used what was already there, like SQL Server and .NET.",
        "TradeOffs": "Not really, we followed what our lead suggested.",
        "Cloud": "I've used Azure a little, like for deployments.",
        "DistributedSystems": "No major work, just basic async processing.",
        "CSharp": "Interfaces and abstract classes are similar, interfaces don't have code.",
        "SQL": "Maybe use DISTINCT or GROUP BY to remove duplicates?",
        "Indexing": "I think indexes help make queries faster.",
        "CI_CD": "Used Jenkins before but not deeply involved.",
        "DevOps": "We push to Git and someone merges it. Then it goes live.",
        "Questions": "Not really, all clear."
    },
    "weak": {
        "Greeting": "Yeah I'm here. Let's go.",
        "StatusCheck": "I think so, not sure.",
        "ExperienceYears": "Been working for a few years.",
        "CurrentProject": "Doing some code for a website.",
        "Responsibilities": "Just writing code when assigned.",
        "Architecture": "No idea, I just write code.",
        "TechChoices": "I don't pick tools, just use what's told.",
        "TradeOffs": "Never thought about that.",
        "Cloud": "Haven't worked on cloud much.",
        "DistributedSystems": "Not really.",
        "CSharp": "Not sure, I usually look it up.",
        "SQL": "I would just check for duplicates manually.",
        "Indexing": "I don't think we use indexing.",
        "CI_CD": "I'm not involved in that part.",
        "DevOps": "We don't have a process, we just push.",
        "Questions": "Nope."
    }
}

async def run_interview_test(persona_name: str) -> List[Tuple[str, str]]:
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    candidate = get_candidate_by_id(candidate_id="1", supabase=supabase_client)

    agent_deps = AgentDependencies(
        supabase=supabase_client,
        candidate=candidate
    )

    responses = PERSONA_RESPONSES[persona_name]
    message_history: List[ModelMessage] = []

    prompts = [
        ("Greeting", "Begin with a greeting, confirm timing, introduce BIGO1 and Bain, and describe the role."),
        ("StatusCheck", "Ask if the candidate has interviewed with Bain."),
        ("ExperienceYears", "Ask about total years of experience."),
        ("CurrentProject", "Ask about their current project."),
        ("Responsibilities", "Ask about their responsibilities."),
        ("Architecture", "Ask about architecture and contributions."),
        ("TechChoices", "Ask about tech/tool choices."),
        ("TradeOffs", "Ask about design trade-offs."),
        ("Cloud", "Ask about cloud platform experience."),
        ("DistributedSystems", "Ask about distributed systems or real-time experience."),
        ("CSharp", "Ask a close-ended C#/.NET question."),
        ("SQL", "Ask a close-ended SQL question."),
        ("Indexing", "Ask a close-ended indexing question."),
        ("CI_CD", "Ask a close-ended CI/CD workflow question."),
        ("DevOps", "Ask about how they manage dev, test, and deployment."),
        ("Questions", "Ask if they have any questions before wrapping up.")
    ]

    start_time = time.time()
    outputs = []

    for key, instruction in prompts:
        elapsed = (time.time() - start_time) / 60
        user_input = responses[key]

        message = f"""
        [Instruction to AI — do not treat this as user input]
        Elapsed time: {elapsed:.1f} minutes

        Candidate: "{user_input}"
        """

        response = await interview_agent.run(
            user_prompt=message,
            deps=agent_deps,
            message_history=message_history
        )
        message_history = response.all_messages()
        outputs.append((instruction, response.output))

    return outputs
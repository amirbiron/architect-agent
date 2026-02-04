"""
Architect Agent - Architectural Patterns Knowledge Base
========================================================
Detailed information about each architectural pattern including
pros, cons, and scoring attributes for the decision matrix.
"""
from typing import Dict, List, Any


# ============================================================
# PATTERN DEFINITIONS
# ============================================================

PATTERNS: Dict[str, Dict[str, Any]] = {
    "monolith": {
        "name": "Monolith",
        "description": "Single deployable unit containing all application logic.",
        "best_for": [
            "Small to medium applications",
            "Early-stage startups / MVPs",
            "Teams under 10 developers",
            "Simple business domains"
        ],
        "pros": [
            "Simple development and deployment",
            "Easy debugging and testing",
            "Lower operational overhead",
            "No network latency between components",
            "Faster time to market"
        ],
        "cons": [
            "Harder to scale specific components",
            "Technology lock-in",
            "Longer build times as app grows",
            "Single point of failure",
            "Team coupling issues at scale"
        ],
        "scoring": {
            "time_to_market": 95,  # Very fast to get started
            "cost": 90,           # Low infrastructure cost
            "scale": 30,          # Limited horizontal scaling
            "reliability": 50,     # SPOF concerns
            "security": 60        # All-or-nothing security
        },
        "tech_recommendations": {
            "backend": ["Python/Django", "Node.js/Express", "Ruby on Rails", "Laravel"],
            "database": ["PostgreSQL", "MySQL", "SQLite"],
            "deployment": ["Render", "Heroku", "Railway", "DigitalOcean App Platform"]
        }
    },

    "modular_monolith": {
        "name": "Modular Monolith",
        "description": "Single deployment with well-defined internal module boundaries.",
        "best_for": [
            "Medium applications planning for growth",
            "Teams 10-30 developers",
            "Complex domains needing structure",
            "Preparing for future microservices"
        ],
        "pros": [
            "Best of both worlds - simplicity + structure",
            "Clear module boundaries",
            "Easier transition to microservices later",
            "Good for medium-sized teams",
            "Maintains deployment simplicity"
        ],
        "cons": [
            "Requires discipline to maintain boundaries",
            "Still single deployment unit",
            "Can devolve into regular monolith",
            "Module coupling can creep in"
        ],
        "scoring": {
            "time_to_market": 80,
            "cost": 85,
            "scale": 50,
            "reliability": 60,
            "security": 65
        },
        "tech_recommendations": {
            "backend": ["Python/FastAPI", "Java/Spring Boot", "C#/.NET Core", "Go"],
            "database": ["PostgreSQL", "MySQL"],
            "deployment": ["Render", "AWS ECS", "Google Cloud Run"]
        }
    },

    "microservices": {
        "name": "Microservices",
        "description": "Distributed system of independently deployable services.",
        "best_for": [
            "Large-scale applications",
            "Teams 30+ developers",
            "Different scaling needs per component",
            "Polyglot technology requirements"
        ],
        "pros": [
            "Independent deployment and scaling",
            "Technology flexibility per service",
            "Team autonomy",
            "Fault isolation",
            "Easier to understand individual services"
        ],
        "cons": [
            "High operational complexity",
            "Network latency and failures",
            "Data consistency challenges",
            "Requires mature DevOps practices",
            "Higher infrastructure costs"
        ],
        "scoring": {
            "time_to_market": 40,  # Slow initial setup
            "cost": 35,           # High infrastructure costs
            "scale": 95,          # Excellent scalability
            "reliability": 80,     # With proper setup
            "security": 75        # Per-service security
        },
        "tech_recommendations": {
            "backend": ["Node.js", "Go", "Python/FastAPI", "Java/Spring Boot"],
            "database": ["PostgreSQL", "MongoDB", "Redis"],
            "messaging": ["RabbitMQ", "Apache Kafka", "AWS SQS"],
            "deployment": ["Kubernetes", "AWS ECS", "Google GKE"]
        }
    },

    "serverless": {
        "name": "Serverless",
        "description": "Event-driven functions with auto-scaling and pay-per-use.",
        "best_for": [
            "Variable/unpredictable workloads",
            "Event-driven applications",
            "Cost optimization for low traffic",
            "Quick prototypes and MVPs"
        ],
        "pros": [
            "Pay only for actual usage",
            "Auto-scaling out of the box",
            "No server management",
            "Great for sporadic workloads",
            "Fast deployment of functions"
        ],
        "cons": [
            "Cold start latency",
            "Vendor lock-in",
            "Limited execution time",
            "Complex debugging",
            "Expensive at high scale"
        ],
        "scoring": {
            "time_to_market": 85,
            "cost": 70,  # Depends heavily on usage pattern
            "scale": 85,
            "reliability": 70,
            "security": 65
        },
        "tech_recommendations": {
            "compute": ["AWS Lambda", "Google Cloud Functions", "Vercel Functions", "Cloudflare Workers"],
            "database": ["DynamoDB", "Firestore", "PlanetScale", "Supabase"],
            "deployment": ["Serverless Framework", "SST", "Pulumi"]
        }
    },

    "event_driven": {
        "name": "Event-Driven Architecture",
        "description": "Loosely coupled services communicating through events.",
        "best_for": [
            "Real-time processing needs",
            "Complex workflows",
            "Audit trail requirements",
            "Decoupled integrations"
        ],
        "pros": [
            "High decoupling between services",
            "Natural audit trail",
            "Easy to add new consumers",
            "Resilient to failures",
            "Supports complex workflows"
        ],
        "cons": [
            "Eventual consistency complexity",
            "Debugging distributed flows",
            "Message ordering challenges",
            "Requires robust monitoring",
            "Learning curve"
        ],
        "scoring": {
            "time_to_market": 50,
            "cost": 55,
            "scale": 90,
            "reliability": 85,
            "security": 70
        },
        "tech_recommendations": {
            "messaging": ["Apache Kafka", "RabbitMQ", "AWS EventBridge", "Redis Streams"],
            "backend": ["Node.js", "Python", "Go"],
            "database": ["PostgreSQL", "MongoDB", "EventStoreDB"]
        }
    },

    "cqrs": {
        "name": "CQRS (Command Query Responsibility Segregation)",
        "description": "Separate models for reading and writing data.",
        "best_for": [
            "Complex domains with different read/write patterns",
            "High-read applications",
            "Event sourcing scenarios",
            "Audit and compliance requirements"
        ],
        "pros": [
            "Optimized read and write models",
            "Better performance for read-heavy apps",
            "Natural fit for event sourcing",
            "Scalable independently",
            "Clear separation of concerns"
        ],
        "cons": [
            "Increased complexity",
            "Eventual consistency",
            "More code to maintain",
            "Steeper learning curve",
            "Overkill for simple apps"
        ],
        "scoring": {
            "time_to_market": 35,
            "cost": 45,
            "scale": 85,
            "reliability": 80,
            "security": 80
        },
        "tech_recommendations": {
            "backend": ["C#/.NET", "Java/Axon", "Python/eventsourcing"],
            "database": {
                "write": ["PostgreSQL", "EventStoreDB"],
                "read": ["Elasticsearch", "Redis", "MongoDB"]
            }
        }
    }
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_pattern(name: str) -> Dict[str, Any]:
    """Get pattern details by name."""
    return PATTERNS.get(name.lower().replace(" ", "_"), {})


def get_all_pattern_names() -> List[str]:
    """Get list of all available pattern names."""
    return list(PATTERNS.keys())


def get_pattern_summary(name: str) -> str:
    """Get a short summary of a pattern."""
    pattern = get_pattern(name)
    if not pattern:
        return f"Unknown pattern: {name}"

    return f"""
**{pattern['name']}**
{pattern['description']}

Best for: {', '.join(pattern['best_for'][:3])}
""".strip()


def compare_patterns(patterns: List[str]) -> str:
    """Generate a comparison table for multiple patterns."""
    headers = ["Aspect"] + [PATTERNS[p]["name"] for p in patterns if p in PATTERNS]

    rows = [
        ["Time to Market"] + [f"{PATTERNS[p]['scoring']['time_to_market']}/100" for p in patterns if p in PATTERNS],
        ["Cost"] + [f"{PATTERNS[p]['scoring']['cost']}/100" for p in patterns if p in PATTERNS],
        ["Scalability"] + [f"{PATTERNS[p]['scoring']['scale']}/100" for p in patterns if p in PATTERNS],
        ["Reliability"] + [f"{PATTERNS[p]['scoring']['reliability']}/100" for p in patterns if p in PATTERNS],
        ["Security"] + [f"{PATTERNS[p]['scoring']['security']}/100" for p in patterns if p in PATTERNS],
    ]

    return {"headers": headers, "rows": rows}

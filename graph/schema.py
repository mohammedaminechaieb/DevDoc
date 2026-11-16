
# graph/schema.py
# Knowledge Graph Schema - DevDoc AI
# Strategy: Hybrid Open-World Schema

# ============================================================
# 1. NODE TYPES
# Categories of entities, NOT a list of all entities.
# New categories can be proposed during extraction.
# ============================================================

NODE_TYPES = {
    "Framework": "Frameworks for building AI applications and agents",
    "Agent": "Autonomous or specialized AI agents",
    "Model": "LLMs and machine learning models",
    "Tool": "External tools or functions used by agents",
    "API": "Application programming interfaces",
    "Protocol": "Communication and integration protocols",
    "Concept": "General AI and Agentic AI concepts",
    "Technique": "Methods, strategies and algorithms",
    "Component": "Architectural and technical components",
    "Architecture": "System and agent architectures",
    "DataStore": "Databases and storage systems",
    "DataStructure": "Data and graph structures",
    "Language": "Programming and query languages",
    "Platform": "Development and execution platforms",
    "Task": "Tasks performed by agents or systems",
    "Metric": "Evaluation and performance metrics",
    "Artifact": "Prompts, outputs and generated artifacts",
    "Dataset": "Datasets used for training or evaluation",
}

# ============================================================
# 2. SEED ENTITIES
# Initial examples only. NOT an exhaustive entity vocabulary.
# ============================================================

SEED_ENTITIES = {
    "Framework": [
        "LangGraph",
        "LangChain",
        "CrewAI",
        "AutoGen",
        "OpenAI Agents SDK"
    ],

    "Concept": [
        "Agentic AI",
        "Multi-Agent System",
        "RAG",
        "GraphRAG",
        "Planning",
        "Memory",
        "Reasoning"
    ],

    "Protocol": [
        "MCP"
    ],

    "Language": [
        "Python"
    ]
}

# ============================================================
# 3. RELATION TYPES
# Canonical relation vocabulary.
# The extractor may propose new predicates.
# ============================================================

RELATION_TYPES = {
    # Usage
    "USES": "Uses a resource or component",
    "INVOKES": "Calls a tool, function or API",

    # Composition
    "HAS": "Has a component or property",
    "CONTAINS": "Contains another entity",
    "PART_OF": "Is part of another entity",

    # Dependencies
    "DEPENDS_ON": "Requires another entity",
    "REQUIRES": "Needs a resource or capability",

    # Architecture
    "IMPLEMENTS": "Implements a concept or specification",
    "EXTENDS": "Extends another framework or component",
    "INHERITS_FROM": "Inherits from another class or component",

    # Communication
    "COMMUNICATES_WITH": "Communicates with another entity",
    "CONNECTS_TO": "Establishes a connection",

    # Agent collaboration
    "DELEGATES_TO": "Delegates a task to another agent",
    "COLLABORATES_WITH": "Collaborates with another entity",

    # Capabilities
    "SUPPORTS": "Supports a feature or capability",
    "PROVIDES": "Provides a functionality",
    "ENABLES": "Makes a capability possible",

    # Data operations
    "STORES": "Stores information",
    "RETRIEVES": "Retrieves information",
    "GENERATES": "Generates an output",
    "TRANSFORMS": "Transforms data",

    # Control flow
    "ROUTES_TO": "Routes execution to another component",
    "TRIGGERS": "Triggers an action",
    "VALIDATES": "Validates data or output",

    # Evaluation
    "EVALUATES": "Evaluates an entity or system",
    "MEASURES": "Measures a property or performance",
    "OPTIMIZES": "Optimizes another entity",

    # Comparison
    "ALTERNATIVE_TO": "Is an alternative to",
    "SIMILAR_TO": "Is similar to",
    "CONTRASTS_WITH": "Contrasts with",

    # General fallback
    "RELATED_TO": "General semantic relationship"
}

# ============================================================
# 4. EXTENSIBLE SCHEMA
# Unknown types and predicates are candidates, not errors.
# They must be reviewed before becoming canonical.
# ============================================================

UNKNOWN_NODE_TYPE = "Unclassified"
UNKNOWN_RELATION_TYPE = "RELATED_TO"

# Preserve the original extracted type/predicate even when
# mapping it to a canonical schema type.
PRESERVE_RAW_LABEL = True
PRESERVE_RAW_PREDICATE = True

# ============================================================
# 5. NODE PROPERTIES
# ============================================================

NODE_PROPERTIES = [
    "name",
    "description",
    "aliases",
    "canonical_type",
    "raw_type",
    "source_documents"
]

# ============================================================
# 6. RELATION PROPERTIES / PROVENANCE
# ============================================================

RELATION_PROPERTIES = [
    "confidence",
    "evidence",
    "source_chunk_id",
    "source_url",
    "document_version",
    "extraction_method",
    "raw_predicate"
]

# ============================================================
# 7. CHUNK NODES
# Each chunk is represented in the graph to preserve provenance.
# ============================================================

CHUNK_LABEL = "Chunk"

CHUNK_PROPERTIES = [
    "chunk_id",
    "url",
    "document",
    "section",
    "framework",
    "version",
    "text"
]

# Provenance relation: Entity -> Chunk
PROVENANCE_RELATION = "MENTIONED_IN"

# ============================================================
# 8. SCHEMA VALIDATION POLICY
# ============================================================

SCHEMA_POLICY = {
    "allow_new_node_types": True,
    "allow_new_relation_types": True,
    "require_evidence_for_relations": True,
    "preserve_unknown_types": True,
    "preserve_original_predicates": True,
    "normalize_relation_types": True,
    "require_entity_resolution": True
}

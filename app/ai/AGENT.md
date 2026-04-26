# AGENT.md

## Overview
This project implements the AI pipeline for a virtual trial system **without using LangGraph**.  
The goal is to build the @./flowchart.png flowchart as a **plain Python state-driven orchestration system** that is easy to understand, debug, and extend later.

Instead of relying on a graph framework, this project uses:

- a central **state object**
- step-based **Python orchestration functions**
- role-based **AI agents**
- **Retrieval-Augmented Generation (RAG, Retrieval-Augmented Generation)** for legal materials
- a final **multi-judge decision synthesis** process

This document defines the implementation direction, architecture, responsibilities, and coding rules for the system.

---

## Core Design Principle
Do **not** start from framework-first design.

Start with a **state machine mindset**:

1. receive case input
2. classify case type
3. retrieve relevant legal materials
4. run role-based agents in sequence
5. repeat argument/rebuttal rounds
6. run judge agents
7. synthesize the final verdict

The orchestration logic should be explicit in Python code so that every transition is easy to inspect and test.

---

## Project Goal
Build a Python-based AI trial simulation pipeline that supports:

- **criminal case flow**
  - prosecutor-side argument
  - defense-side rebuttal
  - repeated exchange rounds
  - judge panel review
  - final verdict

- **civil case flow**
  - plaintiff-side argument
  - defendant-side rebuttal
  - repeated exchange rounds
  - judge panel review
  - final verdict

The first implementation should focus on correctness, traceability, and maintainability rather than framework abstraction.

---

## Architecture

### 1. State-Driven Pipeline
The system must be built around a single shared state object.

All major pipeline functions should follow this shape:

- input: current `TrialState`
- output: updated `TrialState`

This ensures that:
- the entire simulation is reproducible
- debugging is straightforward
- each pipeline step is easy to isolate and test

---

### 2. Main Components

#### State Layer
Responsible for storing:
- case metadata
- case type
- current round number
- retrieved legal documents
- agent messages
- judge opinions
- final verdict and reasoning

#### LLM Service Layer
Responsible for:
- calling the language model
- keeping model invocation logic centralized
- avoiding duplicated API call logic across agents

#### Retrieval Layer
Responsible for:
- embedding generation
- ChromaDB search
- filtering legal materials by case type or category
- returning the most relevant documents for prompting

#### Agent Layer
Responsible for:
- prosecutor logic (형사 공격 측)
- plaintiff logic (민사 공격 측)
- criminal defense logic (형사 방어 측)
- civil defense logic (민사 방어 측)
- judge logic (원칙주의 / 형평주의 / 여론반영)
- master judge logic

Each agent should focus on **its legal role only** and should not manage orchestration.

#### Orchestration Layer
Responsible for:
- controlling pipeline order
- managing round progression
- deciding which agents run for criminal vs civil cases
- invoking final judge synthesis

---

## Recommended Directory Structure

```text
app/
├─ main.py
├─ models/
│  ├─ state.py
│  └─ schemas.py
├─ services/
│  ├─ llm_service.py
│  ├─ retrieval_service.py
│  ├─ case_classifier.py
│  └─ simulation_service.py
├─ agents/
│  ├─ prosecutor.py
│  ├─ criminal_defense.py
│  ├─ plaintiff.py
│  ├─ civil_defense.py
│  ├─ judge_principle.py
│  ├─ judge_equity.py
│  ├─ judge_public.py
│  └─ judge_master.py
└─ prompts/
   ├─ prosecutor.txt
   ├─ defense.txt
   ├─ judge_originalist.txt
   ├─ judge_pragmatic.txt
   └─ judge_public.txt
```

## Implementation Rules

### Rule 1. State Comes First
Before implementing any agent logic, define the central state model.

At minimum, the state should contain:

- `case_id`
- `case_type`
- `case_summary`
- `facts`
- `round_limit`
- `current_round`
- `retrieved_docs`
- `messages`
- `judge_opinions`
- `final_verdict`
- `final_reasoning`

The state model should use a structured schema system such as Pydantic.

### Rule 2. Keep Orchestration Explicit
Do not hide control flow behind decorators or heavy abstractions.

The trial pipeline should be readable from top to bottom in plain Python.  
A developer should be able to open `simulation_service.py` and understand:

- what happens first
- what repeats
- where branching occurs
- how the final decision is produced

### Rule 3. Agents Should Not Control the Pipeline
Agents are not orchestrators.

Each agent module should only:

- build prompts
- consume relevant state
- generate its output
- append its result to the shared state

Agents should never decide:

- how many rounds to run
- what the next agent is
- whether the case is criminal or civil

That logic belongs to the orchestration layer.

### Rule 4. Use Structured Outputs
Agent responses should not be stored as raw unstructured paragraphs only.

Whenever possible, require JSON-style structured outputs with fields such as:

- `summary`
- `key_points`
- `cited_rules`
- `position`
- `next_action`

This makes it much easier to:

- store messages
- feed previous outputs into later prompts
- build a frontend
- debug inconsistent reasoning

### Rule 5. Retrieval Should Be Simple at First
The first version of RAG should be minimal and stable.

Recommended legal collections:

- `cases` for precedents
- `statutes` for laws and legal provisions
- `sentencing` for sentencing guidelines

The initial retrieval flow should be:

1. embed the query
2. search ChromaDB
3. apply basic filtering
4. return top-k documents
5. inject only the most relevant documents into prompts

Do not over-engineer ranking in the first implementation.

### Rule 6. Prefer Synchronous Execution First
The first version should use synchronous Python logic.

Reason:

- easier debugging
- simpler error handling
- clearer state transitions

Parallel execution can be added later for:

- multiple judges
- multiple retrieval branches
- multiple independent agent evaluations

### Rule 7. Log Everything Important
The system should be traceable.

At minimum, log:

- case classification result
- retrieval queries
- retrieved document titles
- agent prompt inputs
- agent outputs
- round transitions
- judge reasoning
- final synthesis result

A trial simulation system without logs becomes difficult to inspect and trust.

---

## Suggested Development Order

### Phase 1. Minimal Single-Round Prototype
Implement:

- case input
- case type classification
- retrieval
- one prosecution or plaintiff argument
- one defense response
- one judge decision

Goal: verify the basic pipeline works end-to-end.

### Phase 2. Multi-Round Debate
Extend to repeated rounds.

Recommended default:

- 3 rounds

For each round:

- generate argument
- generate rebuttal
- store outputs in state
- optionally re-run retrieval based on the latest message

Goal: make the simulation reflect the repeated exchange in the flowchart.

### Phase 3. Multi-Judge Panel
Add three judge personas, for example:

- originalist judge
- equity-focused judge
- public-opinion-aware judge

Each judge should independently read:

- the case summary
- the debate history
- the retrieved legal materials

Then produce:

- reasoning
- interim verdict

### Phase 4. Master Judge Synthesis
After all judges respond, run a final master judge step.

The master judge should:

- compare all judge opinions
- identify overlapping reasoning
- resolve conflicts
- produce the final verdict
- produce the final explanation

### Phase 5. Criminal / Civil Branching
After the core pipeline works, add separate orchestration for:

#### Criminal
- prosecutor
- defense lawyer
- defendant-side rebuttal
- prosecution rebuttal

#### Civil
- plaintiff lawyer
- defendant lawyer
- co-defendant or secondary defense if needed
- plaintiff rebuttal

The branch should be selected only after case-type classification.

---

## Recommended Trial Flow

### Criminal Case
- receive case input
- classify as criminal
- retrieve legal materials
- prosecutor argument
- defense lawyer rebuttal
- defendant-side response
- prosecutor rebuttal
- repeat for 3 rounds
- run judge panel
- run master judge
- output final verdict

### Civil Case
- receive case input
- classify as civil
- retrieve legal materials
- plaintiff argument
- defendant rebuttal
- additional defense response if needed
- plaintiff rebuttal
- repeat for 3 rounds
- run judge panel
- run master judge
- output final verdict

---

## State Model Expectations

A `TrialState` model should be able to answer all of the following:

- What type of case is this?
- What round are we currently in?
- What messages have already been generated?
- What legal documents have been retrieved?
- What did each judge conclude?
- What is the final verdict?
- Why was that verdict produced?

If the state cannot answer these questions, the schema is incomplete.

---

## Agent Design Expectations

### Prosecutor / Plaintiff Agent
Must focus on:

- legal liability
- evidence structure
- persuasive accusation or claim
- weaknesses in the opposing side

### Defense Agent
Must focus on:

- rebuttal
- legal defenses
- evidentiary weakness
- procedural or interpretive counterpoints

### Judge Agent
Must focus on:

- neutrality
- weighing both sides
- interpreting law and facts
- producing a reasoned conclusion

### Master Judge Agent
Must focus on:

- synthesis across judge outputs
- conflict resolution
- consistent final verdict generation

---

## Prompt Design Guidance

Prompts should be stored separately from business logic whenever possible.

Each prompt should clearly define:

- the role of the agent
- the legal objective
- what context is provided
- what output format is required

Prompt files should remain easy to update without changing orchestration code.

---

## What Not to Do

### Do Not Start with LangGraph
This project is intentionally designed to begin without LangGraph.

The goal is to understand and validate:

- state transitions
- agent responsibilities
- retrieval timing
- debate loop structure

A graph framework may be considered later only after the plain Python design is stable.

### Do Not Mix Responsibilities
Avoid putting:

- retrieval logic inside agents
- pipeline control inside prompts
- final verdict logic inside intermediate debate agents

Each layer should remain cleanly separated.

### Do Not Optimize Too Early
Do not begin with:

- async orchestration
- parallel agent execution
- advanced reranking
- complex memory graphs
- excessive abstraction

First make the system correct and inspectable.

---

## Minimum Viable Target

The first milestone should be a runnable script that can:

- accept a case summary
- classify case type
- retrieve legal materials
- run one complete debate cycle
- run judge evaluation
- return a final verdict

Only after this works should the full 3-round multi-agent structure be expanded.

---

## Long-Term Extension Path

After the Python-first version is stable, the system can later evolve into:

- FastAPI service integration
- frontend connection
- persistent trial history storage
- stronger legal retrieval pipelines
- evaluation framework for verdict quality
- LangGraph migration if state flow becomes too complex

But the first version must remain simple, explicit, and testable.

---

## Final Guidance

When implementing this project, always prioritize:

- clarity over abstraction
- explicit state over hidden flow
- modularity over monolithic scripts
- reproducibility over convenience
- structured outputs over free-form text

The best starting point is:

1. define `TrialState`
2. implement `LLMService`
3. implement `retrieve_legal_docs()`
4. implement `run_trial()`
5. add agents one by one
6. expand to multi-round and multi-judge flow

This is the recommended foundation for building the AI pipeline shown in the flowchart using plain Python.
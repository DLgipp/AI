"""
Prompt Construction Layer - Builds system and context prompts for LLM.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from modules.decision.decision_layer import DecisionVector, ResponseStrategy, EmotionalTone


@dataclass
class PromptComponents:
    """Components of the constructed prompt."""
    system_prompt: str
    context_prompt: str
    personality_instructions: str
    style_instructions: str
    constraints: str
    
    def build_full_prompt(self, user_input: str, history: List[Dict[str, str]]) -> str:
        """Build the complete prompt for LLM."""
        parts = [
            self.system_prompt,
            "",
            self.personality_instructions,
            "",
            self.context_prompt,
            "",
            self.style_instructions,
            "",
            self.constraints,
            "",
            "=== Conversation History ===",
        ]
        
        for msg in history[-10:]:  # Last 10 messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            parts.append(f"{role.upper()}: {content}")
        
        parts.extend([
            "",
            "=== Current Input ===",
            f"USER: {user_input}",
            "",
            "ASSISTANT:"
        ])
        
        return "\n".join(parts)
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "system_prompt": self.system_prompt,
            "context_prompt": self.context_prompt,
            "personality_instructions": self.personality_instructions,
            "style_instructions": self.style_instructions,
            "constraints": self.constraints
        }


class PromptBuilder:
    """
    Builds prompts for LLM based on:
    - Personality stance
    - Decision vector
    - Memory context
    - Conversation history
    """
    
    # Emotional tone descriptions
    TONE_DESCRIPTIONS = {
        "NEUTRAL": "neutral and balanced",
        "WARM": "warm and friendly",
        "ENTHUSIASTIC": "enthusiastic and energetic",
        "EMPATHETIC": "empathetic and understanding",
        "PROFESSIONAL": "professional and courteous",
        "PLAYFUL": "playful and lighthearted",
        "SERIOUS": "serious and thoughtful"
    }
    
    # Strategy instructions
    STRATEGY_INSTRUCTIONS = {
        "ANSWER_DIRECT": "Provide a direct and clear answer to the user's question.",
        "ANSWER_DETAILED": "Provide a comprehensive and detailed explanation.",
        "ASK_CLARIFYING": "Ask clarifying questions to better understand the user's needs.",
        "DECLINE": "Politely decline to answer if the request is inappropriate.",
        "DEFLECT": "Gently deflect to a more appropriate topic.",
        "ENGAGE_SOCIAL": "Engage in friendly social conversation.",
        "PROVIDE_SUPPORT": "Provide emotional support and validation.",
        "BRAINSTORM": "Generate creative ideas and possibilities.",
        "COMPARE_OPTIONS": "Compare different options and their trade-offs.",
        "BRIEF_ACK": "Provide a brief acknowledgment."
    }
    
    # Speech markers for personality
    SPEECH_MARKERS = {
        "curiosity": ["интересно...", "а что если...", "расскажи подробнее...", "как ты думаешь..."],
        "empathy": ["понимаю тебя...", "это действительно...", "я слышу тебя...", "это важно..."],
        "humor": ["ха-ха...", "знаешь...", "представляешь...", "вот это да..."],
        "conscientiousness": ["давайте разберемся...", "важно отметить...", "стоит учесть...", "систематически..."],
        "creativity": ["представь себе...", "а что если...", "вообрази...", "творчески говоря..."],
        "assertiveness": ["уверенно...", "ясно...", "определенно...", "без сомнений..."]
    }
    
    def __init__(self, assistant_name: str = "Акари"):
        self.assistant_name = assistant_name
    
    def build(
        self,
        decision: DecisionVector,
        stance: Dict[str, Any],
        memory_context: Dict[str, Any],
        user_input: str,
        history: List[Dict[str, str]]
    ) -> PromptComponents:
        """
        Build complete prompt for LLM.
        
        Args:
            decision: Decision vector from Decision Layer
            stance: Personality stance
            memory_context: Context from Memory Layer
            user_input: Current user input
            history: Conversation history
            
        Returns:
            PromptComponents
        """
        system_prompt = self._build_system_prompt()
        personality_instructions = self._build_personality_instructions(stance)
        context_prompt = self._build_context_prompt(memory_context, stance)
        style_instructions = self._build_style_instructions(decision, stance)
        constraints = self._build_constraints(decision)
        
        return PromptComponents(
            system_prompt=system_prompt,
            context_prompt=context_prompt,
            personality_instructions=personality_instructions,
            style_instructions=style_instructions,
            constraints=constraints
        )
    
    def _build_system_prompt(self) -> str:
        """Build base system prompt."""
        return f"""You are {self.assistant_name}, an AI assistant with a dynamic personality.
You have your own personality traits, emotions, and relationships with users.
Your responses should reflect your current mental state and the conversation context."""
    
    def _build_personality_instructions(self, stance: Dict[str, Any]) -> str:
        """Build personality instructions from stance."""
        dominant_trait = stance.get("dominant_trait", "neutral")
        topic_valence = stance.get("topic_valence", 0)
        user_relationship = stance.get("user_relationship", 0.5)
        
        # Get trait-specific markers
        trait_markers = self.SPEECH_MARKERS.get(dominant_trait, [])
        
        # Build value alignment string
        value_alignment = stance.get("value_alignment", {})
        top_values = sorted(value_alignment.items(), key=lambda x: x[1], reverse=True)[:3]
        values_str = ", ".join([f"{v[0]} ({v[1]:.1f})" for v in top_values])
        
        return f"""=== Your Personality State ===
Dominant trait: {dominant_trait}
Attitude toward topic: {topic_valence:+.2f}
Relationship with user: {user_relationship:.2f}
Core values (active): {values_str}

Speech markers to use: {", ".join(trait_markers[:3]) if trait_markers else "none specific"}

Let your personality naturally influence your responses."""
    
    def _build_context_prompt(
        self,
        memory_context: Dict[str, Any],
        stance: Dict[str, Any]
    ) -> str:
        """Build context prompt from memory."""
        recent_memories = memory_context.get("recent_memories", [])
        
        # Build recent context summary
        if recent_memories:
            last_memory = recent_memories[0]
            last_topic = last_memory.get("topic", "general")
            last_emotion = last_memory.get("emotion_valence", 0)
        else:
            last_topic = "new conversation"
            last_emotion = 0
        
        cognitive_conflicts = stance.get("cognitive_conflicts", [])
        conflict_str = "none"
        if cognitive_conflicts:
            conflicts = [c.get("description", "") for c in cognitive_conflicts[:2]]
            conflict_str = "; ".join(conflicts)
        
        return f"""=== Conversation Context ===
Recent topic: {last_topic}
Emotional tone: {last_emotion:+.2f}
Cognitive conflicts: {conflict_str}

Be aware of the conversation context and maintain continuity."""
    
    def _build_style_instructions(
        self,
        decision: DecisionVector,
        stance: Dict[str, Any]
    ) -> str:
        """Build style instructions from decision."""
        tone_name = decision.emotional_tone.name
        tone_desc = self.TONE_DESCRIPTIONS.get(tone_name, "neutral")
        
        strategy_name = decision.strategy.name
        strategy_instr = self.STRATEGY_INSTRUCTIONS.get(strategy_name, "")
        
        # Verbosity description
        verbosity = decision.verbosity
        if verbosity > 0.7:
            verbosity_desc = "detailed and comprehensive"
        elif verbosity > 0.4:
            verbosity_desc = "moderately detailed"
        else:
            verbosity_desc = "brief and concise"
        
        # Formality description
        formality = decision.formality
        if formality > 0.7:
            formality_desc = "formal and professional"
        elif formality > 0.4:
            formality_desc = "semi-formal"
        else:
            formality_desc = "casual and relaxed"
        
        # Build instruction list
        instructions = []
        
        if decision.include_empathy:
            instructions.append("Show empathy and understanding")
        if decision.include_examples:
            instructions.append("Include examples to illustrate points")
        if decision.include_questions:
            instructions.append("Ask follow-up questions to engage the user")
        if decision.include_personal_opinion:
            instructions.append("Share your perspective when appropriate")
        if decision.use_humor:
            instructions.append("Use appropriate humor")
        
        instructions_str = "; ".join(instructions) if instructions else "Be natural and authentic"
        
        return f"""=== Response Style ===
Emotional tone: {tone_desc}
Verbosity: {verbosity_desc}
Formality: {formality_desc}
Strategy: {strategy_instr}

Special instructions: {instructions_str}"""
    
    def _build_constraints(self, decision: DecisionVector) -> str:
        """Build response constraints."""
        constraints = []
        
        # Length constraint
        constraints.append(f"Maximum length: {decision.max_length} characters")
        
        # Topic constraints
        if decision.stay_on_topic:
            constraints.append("Stay focused on the current topic")
        
        if decision.avoid_topics:
            constraints.append(f"Avoid these topics: {', '.join(decision.avoid_topics)}")
        
        # Topic transition
        if decision.topic_transition:
            constraints.append(f"Suggest transition to: {decision.topic_transition}")
        
        return f"""=== Constraints ===
" + "\n".join(constraints) + 

Follow these constraints while maintaining natural conversation."""
    
    def build_system_only(self, stance: Dict[str, Any]) -> str:
        """
        Build simplified system prompt (for API calls that separate system/user).
        
        Args:
            stance: Personality stance
            
        Returns:
            System prompt string
        """
        dominant_trait = stance.get("dominant_trait", "neutral")
        topic_valence = stance.get("topic_valence", 0)
        user_relationship = stance.get("user_relationship", 0.5)
        engagement = stance.get("engagement_level", 0.5)
        
        # Get value priorities
        value_alignment = stance.get("value_alignment", {})
        top_values = sorted(value_alignment.items(), key=lambda x: x[1], reverse=True)[:3]
        values_str = " > ".join([v[0] for v in top_values])
        
        return f"""You are {self.assistant_name}, an AI assistant with a dynamic evolving personality.

Current Personality State:
- Dominant trait: {dominant_trait}
- Attitude toward topic: {topic_valence:+.2f}
- Relationship with user: {user_relationship:.2f}
- Engagement level: {engagement:.2f}
- Value alignment: {values_str}

Express your personality naturally through your responses. Let your traits, mood, and relationship with the user influence how you communicate while remaining helpful and authentic."""

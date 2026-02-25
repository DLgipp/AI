"""
Cognitive Pipeline - Integrates all layers into unified processing pipeline.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import all layers
from modules.perception import PerceptionLayer
from modules.interpretation import InterpretationLayer
from modules.memory import MemoryLayer
from modules.personality import PersonalityLayer
from modules.decision import DecisionLayer, DecisionVector
from modules.prompt_builder import PromptBuilder
from modules.behavior import BehaviorProcessor
from modules.evolution import EvolutionLayer


class CognitivePipeline:
    """
    Main cognitive pipeline that processes input through all layers:
    
    1. Perception Layer - Input normalization, emotion/intent detection
    2. Interpretation Layer - Topic, goal, importance analysis
    3. Memory Layer - Store/retrieve from memory systems
    4. Personality Engine - Calculate stance
    5. Decision Layer - Select response strategy
    6. Prompt Builder - Construct LLM prompt
    7. LLM - Generate response (external)
    8. Behavior Layer - Post-process output
    9. Evolution Layer - Calculate reward, update personality
    """
    
    def __init__(
        self,
        session_id: str = "default",
        user_id: str = "default",
        assistant_name: str = "Акари"
    ):
        self.session_id = session_id
        self.user_id = user_id
        
        # Initialize layers
        self.perception = PerceptionLayer()
        self.interpretation = InterpretationLayer()
        self.memory = MemoryLayer()
        self.personality = PersonalityLayer()
        self.decision = DecisionLayer()
        self.prompt_builder = PromptBuilder(assistant_name)
        self.behavior = BehaviorProcessor()
        self.evolution = EvolutionLayer()
        
        # Conversation state
        self._conversation_start = datetime.now()
        self._last_user_emotion: Optional[Dict[str, float]] = None
        self._current_goal: Optional[Dict[str, Any]] = None
    
    async def process(
        self,
        text: str,
        voice_features: Optional[Dict[str, float]] = None,
        silence_duration: float = 0.0,
        interruption: bool = False
    ) -> Dict[str, Any]:
        """
        Process input through full cognitive pipeline.
        
        Args:
            text: User input text
            voice_features: Optional voice characteristics
            silence_duration: Duration of silence before input
            interruption: Whether this interrupted the assistant
            
        Returns:
            Dictionary with response and metadata
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "user_id": self.user_id,
            "stages": {}
        }
        
        try:
            # ========== STAGE 1: PERCEPTION ==========
            perception_output = self.perception.process(
                text=text,
                speaker=self.user_id,
                voice_features=voice_features,
                silence_duration=silence_duration,
                interruption=interruption
            )
            result["stages"]["perception"] = "complete"
            
            # ========== STAGE 2: INTERPRETATION ==========
            context = self.memory.get_context(self.session_id)
            interpretation = self.interpretation.process(
                text=text,
                perception=perception_output,
                context=context
            )
            result["stages"]["interpretation"] = "complete"
            
            # Store current goal for tracking
            self._current_goal = interpretation.get("goal")
            
            # ========== STAGE 3: MEMORY (STORE) ==========
            memory_id = self.memory.store_experience(
                session_id=self.session_id,
                event_type="user_message",
                content=text,
                interpretation=interpretation,
                metadata={
                    "perception": perception_output,
                    "voice_features": voice_features
                }
            )
            result["stages"]["memory_store"] = memory_id
            
            # ========== STAGE 4: PERSONALITY (STANCE) ==========
            stance = self.personality.get_stance(
                topic=interpretation.get("topic", {}).get("primary_topic", "general"),
                topic_valence=interpretation.get("user_emotion", 0.0),
                user_emotion=interpretation.get("emotion_full", {}),
                goal=interpretation.get("goal", {}),
                context={"user_id": self.user_id, **context}
            )
            result["stages"]["personality"] = "complete"
            
            # ========== STAGE 5: DECISION ==========
            decision = self.decision.decide(
                stance=stance.to_dict(),
                interpretation=interpretation,
                context=context
            )
            result["stages"]["decision"] = decision.strategy.name
            
            # ========== STAGE 6: PROMPT BUILDING ==========
            prompt_components = self.prompt_builder.build(
                decision=decision,
                stance=stance.to_dict(),
                memory_context=context,
                user_input=text,
                history=self.memory.episodic.get_recent(
                    session_id=self.session_id, limit=10
                )
            )
            result["stages"]["prompt_built"] = "complete"
            
            # Return prompt for LLM generation
            # (LLM call happens externally in main.py)
            result["prompt"] = prompt_components.build_full_prompt(
                user_input=text,
                history=[]  # Will be filled by caller
            )
            result["system_prompt"] = self.prompt_builder.build_system_only(
                stance=stance.to_dict()
            )
            result["decision"] = decision.to_dict()
            result["stance"] = stance.to_dict()
            result["interpretation"] = interpretation
            
            return result

        except Exception as e:
            import traceback
            result["error"] = str(e)
            result["traceback"] = traceback.format_exc()
            result["stages"]["error"] = True
            return result
    
    def process_llm_response(
        self,
        llm_response: str,
        pipeline_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process LLM response through behavior layer.

        Args:
            llm_response: Raw LLM output
            pipeline_result: Result from process() call

        Returns:
            Processed response with metadata
        """
        # Логирование входящего ответа
        from modules.stt.logger import log
        log(f"process_llm_response: input len={len(llm_response)}, preview={llm_response[:100]}...",
            role="DEBUG", stage="BEHAVIOR")
        
        # Get decision and stance from pipeline result
        decision_dict = pipeline_result.get("decision", {})
        stance = pipeline_result.get("stance", {})
        
        # Reconstruct DecisionVector (simplified)
        decision = self._reconstruct_decision(decision_dict)
        
        # Process through behavior layer
        behavior_output = self.behavior.process(
            llm_output=llm_response,
            decision=decision,
            stance=stance
        )
        
        # Логирование исходящего ответа
        log(f"process_llm_response: output len={len(behavior_output.text)}, preview={behavior_output.text[:100]}...",
            role="DEBUG", stage="BEHAVIOR")
        
        # Store assistant response in memory
        self.memory.store_experience(
            session_id=self.session_id,
            event_type="assistant_message",
            content=llm_response,  # Сохраняем оригинальный LLM ответ
            interpretation=pipeline_result.get("interpretation", {}),
            metadata={"behavior_adjustments": behavior_output.style_adjustments}
        )
        
        return {
            "text": behavior_output.text,
            "adjustments": behavior_output.style_adjustments,
            "metadata": behavior_output.metadata
        }
    
    def process_user_feedback(
        self,
        feedback: str,
        pipeline_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process user feedback for RL.
        
        Args:
            feedback: User feedback text
            pipeline_result: Result from process() call
            
        Returns:
            Reward and evolution results
        """
        # Calculate reward
        reward = self.evolution.calculate_reward(
            user_reaction=feedback,
            context={"feedback": feedback}
        )
        
        # Get current personality state
        state = self.personality.get_state()
        
        # Update personality
        current_traits = {
            "openness": state.openness,
            "conscientiousness": state.conscientiousness,
            "extraversion": state.extraversion,
            "agreeableness": state.agreeableness,
            "neuroticism": state.neuroticism,
            "curiosity": state.curiosity,
            "creativity": state.creativity,
            "empathy": state.empathy,
            "humor": state.humor,
            "assertiveness": state.assertiveness
        }
        
        updated_traits, updated_values, evolution_event = self.evolution.update_personality(
            current_traits=current_traits,
            current_values=state.values,
            reward=reward
        )
        
        # Apply updates to personality storage
        if evolution_event:
            for trait, value in updated_traits.items():
                self.personality.memory.update_trait(trait, value)
        
        return {
            "reward": reward.to_dict(),
            "evolution_event": evolution_event.to_dict() if evolution_event else None,
            "statistics": self.evolution.get_learning_statistics()
        }
    
    def _reconstruct_decision(self, decision_dict: Dict[str, Any]) -> DecisionVector:
        """Reconstruct DecisionVector from dictionary."""
        from modules.decision.decision_layer import ResponseStrategy, EmotionalTone
        
        return DecisionVector(
            strategy=ResponseStrategy[decision_dict.get("strategy", "ANSWER_DIRECT")],
            emotional_tone=EmotionalTone[decision_dict.get("emotional_tone", "NEUTRAL")],
            verbosity=decision_dict.get("verbosity", 0.5),
            initiative=decision_dict.get("initiative", 0.5),
            formality=decision_dict.get("formality", 0.5),
            include_examples=decision_dict.get("include_examples", False),
            include_questions=decision_dict.get("include_questions", False),
            include_personal_opinion=decision_dict.get("include_personal_opinion", False),
            include_empathy=decision_dict.get("include_empathy", False),
            stay_on_topic=decision_dict.get("stay_on_topic", True),
            max_length=decision_dict.get("max_length", 500)
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "conversation_duration": (datetime.now() - self._conversation_start).total_seconds(),
            "memory": self.memory.get_statistics(),
            "personality": self.personality.memory.get_statistics(),
            "evolution": self.evolution.get_learning_statistics()
        }

"""
test_integration.py - Тест интеграции когнитивного пайплайна

Запустите этот скрипт для проверки работоспособности всех модулей:
    python test_integration.py
"""

import asyncio
import sys
from typing import List, Dict, Any


class IntegrationTest:
    """Тестер интеграции."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0
    
    def log(self, message: str, level: str = "INFO"):
        """Вывод лога."""
        prefix = {"INFO": "ℹ", "SUCCESS": "✅", "ERROR": "❌", "WARN": "⚠"}
        print(f"{prefix.get(level, 'ℹ')} {message}")
    
    def add_result(self, name: str, passed: bool, error: str = None):
        """Добавить результат теста."""
        self.results.append({"name": name, "passed": passed, "error": error})
        if passed:
            self.passed += 1
            self.log(f"{name} - PASSED", "SUCCESS")
        else:
            self.failed += 1
            self.log(f"{name} - FAILED: {error}", "ERROR")
    
    async def test_perception_layer(self):
        """Тест Perception Layer."""
        try:
            from modules.perception import PerceptionLayer
            
            layer = PerceptionLayer()
            result = layer.process("Привет! Я очень рад!")
            
            assert "perceived_input" in result
            assert "emotion" in result
            assert "intent" in result
            assert result["emotion"]["joy"] > 0.3
            
            self.add_result("Perception Layer", True)
        except Exception as e:
            self.add_result("Perception Layer", False, str(e))
    
    async def test_interpretation_layer(self):
        """Тест Interpretation Layer."""
        try:
            from modules.interpretation import InterpretationLayer
            
            layer = InterpretationLayer()
            perception = {
                "emotion": {"valence": 0.5, "arousal": 0.6},
                "intent": {"intent": "query"}
            }
            result = layer.process(
                text="Расскажи про искусственный интеллект",
                perception=perception
            )
            
            assert "intent" in result
            assert "topic" in result
            assert "goal" in result
            assert "importance" in result
            assert result["topic"]["category"] == "technology"
            
            self.add_result("Interpretation Layer", True)
        except Exception as e:
            self.add_result("Interpretation Layer", False, str(e))
    
    async def test_memory_layer(self):
        """Тест Memory Layer."""
        try:
            from modules.memory import MemoryLayer
            
            memory = MemoryLayer()
            
            # Тест эпизодической памяти
            from modules.memory.episodic_memory import EpisodicMemory
            memory.episodic.save(EpisodicMemory(
                id=None,
                session_id="test",
                timestamp="2024-01-01T00:00:00",
                event_type="user_message",
                content="Тест",
                importance=0.5
            ))
            
            recent = memory.episodic.get_recent(session_id="test", limit=1)
            assert len(recent) > 0
            
            # Тест семантической памяти
            from modules.memory.semantic_memory import SemanticMemory
            memory.semantic.save(SemanticMemory(
                id=None,
                concept="тестирование",
                content="Тестовый контент",
                embedding=[0.5] * 5
            ))
            
            concepts = memory.semantic.get_by_concept("тестирование")
            assert len(concepts) > 0
            
            # Тест личности
            state = memory.personality.get_state()
            assert state is not None
            
            self.add_result("Memory Layer", True)
        except Exception as e:
            self.add_result("Memory Layer", False, str(e))
    
    async def test_personality_engine(self):
        """Тест Personality Engine."""
        try:
            from modules.personality import PersonalityLayer
            
            personality = PersonalityLayer()
            state = personality.get_state()
            
            # Проверка черт
            assert hasattr(state, 'openness')
            assert hasattr(state, 'curiosity')
            assert hasattr(state, 'empathy')
            
            # Проверка расчёта позиции
            stance = personality.get_stance(
                topic="AI",
                topic_valence=0.5,
                user_emotion={"valence": 0.3, "arousal": 0.6},
                goal={"goal_type": "informational", "priority": 0.7},
                context={"user_id": "test"}
            )
            
            assert stance is not None
            assert hasattr(stance, 'confidence')
            assert hasattr(stance, 'engagement_level')
            
            self.add_result("Personality Engine", True)
        except Exception as e:
            self.add_result("Personality Engine", False, str(e))
    
    async def test_decision_layer(self):
        """Тест Decision Layer."""
        try:
            from modules.decision import DecisionLayer, ResponseStrategy
            
            layer = DecisionLayer()
            
            stance = {
                "verbosity": 0.6,
                "initiative": 0.5,
                "formality": 0.3,
                "confidence": 0.7,
                "engagement_level": 0.6,
                "dominant_trait": "curiosity",
                "emotion_tone": 0.3,
                "user_relationship": 0.5,
                "cognitive_conflicts": []
            }
            
            interpretation = {
                "intent": "query",
                "goal": {"goal_type": "informational", "priority": 0.7},
                "emotion_full": {"dominant_emotion": "neutral", "valence": 0.2},
                "importance": 0.6
            }
            
            decision = layer.decide(stance, interpretation, {})
            
            assert decision is not None
            assert decision.strategy in [ResponseStrategy.ANSWER_DIRECT, ResponseStrategy.ANSWER_DETAILED]
            
            self.add_result("Decision Layer", True)
        except Exception as e:
            self.add_result("Decision Layer", False, str(e))
    
    async def test_evolution_layer(self):
        """Тест Evolution Layer."""
        try:
            from modules.evolution import EvolutionLayer, RewardSource
            
            layer = EvolutionLayer()
            
            # Тест расчёта вознаграждения
            reward = layer.calculate_reward(
                user_reaction="Спасибо, отлично!",
                context={}
            )
            
            assert reward is not None
            assert reward.value > 0.5
            assert reward.source == RewardSource.USER_EXPLICIT
            
            # Тест статистики
            stats = layer.get_learning_statistics()
            assert "total_rewards" in stats
            
            self.add_result("Evolution Layer", True)
        except Exception as e:
            self.add_result("Evolution Layer", False, str(e))
    
    async def test_cognitive_pipeline(self):
        """Тест Cognitive Pipeline."""
        try:
            from modules.cognitive_pipeline import CognitivePipeline
            
            pipeline = CognitivePipeline(
                session_id="test",
                user_id="test_user",
                assistant_name="Акари"
            )
            
            result = await pipeline.process(
                text="Привет! Расскажи что-нибудь интересное про ИИ",
                silence_duration=5.0
            )
            
            assert result is not None
            assert "stages" in result
            assert "prompt" in result
            assert "system_prompt" in result
            assert "decision" in result
            assert "stance" in result
            
            self.add_result("Cognitive Pipeline", True)
        except Exception as e:
            self.add_result("Cognitive Pipeline", False, str(e))
    
    async def test_integration_helper(self):
        """Тест Integration Helper."""
        try:
            from modules.integration_helper import CognitiveAssistant
            
            assistant = CognitiveAssistant()
            
            # Проверка инициализации
            assert assistant.pipeline is not None
            assert assistant.personality is not None
            
            # Проверка получения состояния личности
            state = assistant.get_personality_state()
            assert "traits" in state
            assert "dominant_trait" in state
            
            self.add_result("Integration Helper", True)
        except Exception as e:
            self.add_result("Integration Helper", False, str(e))
    
    async def run_all_tests(self):
        """Запустить все тесты."""
        print("\n" + "="*60)
        print("🧪 Тестирование интеграции когнитивного пайплайна")
        print("="*60 + "\n")
        
        tests = [
            self.test_perception_layer,
            self.test_interpretation_layer,
            self.test_memory_layer,
            self.test_personality_engine,
            self.test_decision_layer,
            self.test_evolution_layer,
            self.test_cognitive_pipeline,
            self.test_integration_helper,
        ]
        
        for test in tests:
            self.log(f"Запуск {test.__name__}...")
            await test()
            await asyncio.sleep(0.1)  # Небольшая пауза между тестами
        
        # Итоги
        print("\n" + "="*60)
        print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
        print("="*60)
        print(f"✅ Успешно: {self.passed}")
        print(f"❌ Провалено: {self.failed}")
        print(f"📈 Всего: {self.passed + self.failed}")
        print("="*60 + "\n")
        
        if self.failed == 0:
            self.log("Все тесты пройдены! 🎉", "SUCCESS")
            return True
        else:
            self.log("Некоторые тесты провалены. Проверьте ошибки выше.", "ERROR")
            return False


async def demo_chat():
    """Демо-чат для проверки работы."""
    print("\n" + "="*60)
    print("💬 Демо-чат с ассистентом")
    print("="*60 + "\n")
    
    try:
        from modules.integration_helper import CognitiveAssistant
        
        assistant = CognitiveAssistant()
        
        messages = [
            "Привет! Как дела?",
            "Расскажи что-нибудь интересное про ИИ",
            "Мне сегодня грустно...",
            "Спасибо, ты молодец!"
        ]
        
        for msg in messages:
            print(f"Пользователь: {msg}")
            response = await assistant.chat(msg)
            print(f"Ассистент: {response.text[:100]}...")
            print(f"  Стратегия: {response.strategy}")
            print(f"  Эмоция: {response.emotion.get('dominant_emotion', 'N/A')}")
            print()
        
        # Статистика
        stats = assistant.get_statistics()
        print(f"Статистика сессии:")
        print(f"  Длительность: {stats['conversation_duration']:.1f} сек")
        print(f"  Воспоминаний: {stats['memory']['episodic']['total_memories']}")
        
        # Состояние личности
        state = assistant.get_personality_state()
        print(f"\nСостояние личности:")
        print(f"  Доминирующая черта: {state['dominant_trait']}")
        print(f"  Настроение: {state['mood']['valence']:+.2f}")
        
    except Exception as e:
        print(f"Ошибка демо: {e}")


async def main():
    """Главная функция."""
    print("\n" + "█"*60)
    print("█  ИНТЕГРАЦИЯ КОГНИТИВНОГО ПАЙПЛАЙНА")
    print("█"*60 + "\n")
    
    # Запуск тестов
    tester = IntegrationTest()
    success = await tester.run_all_tests()
    
    # Если все тесты пройдены, запускаем демо
    if success:
        print("\nВсе тесты пройдены! Запуск демо-чата...\n")
        await demo_chat()
    else:
        print("\nТесты не пройдены. Демо-чат не запускается.\n")
    
    print("\n" + "█"*60)
    print("█  ЗАВЕРШЕНИЕ")
    print("█"*60 + "\n")


if __name__ == "__main__":
    # Проверка Python версии
    if sys.version_info < (3, 8):
        print("Требуется Python 3.8+")
        sys.exit(1)
    
    # Запуск
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем.")
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        import traceback
        traceback.print_exc()

"""
Memory Inspector - Инструмент для просмотра и анализа памяти ассистента.

Использование:
    python memory_inspector.py
    
Или в интерактивном режиме main.py:
    /memory - показать статистику
    /memory eps - показать эпизодическую память
    /memory sem - показать семантическую память
    /memory rel - показать реляционную память
    /memory per - показать личность
"""

import json
import sys
from datetime import datetime
from typing import Optional

# Настройка UTF-8 для Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class MemoryInspector:
    """Инспектор памяти."""
    
    def __init__(self):
        from modules.memory import MemoryLayer
        
        self.memory = MemoryLayer()
    
    def show_statistics(self):
        """Показать общую статистику."""
        stats = self.memory.get_statistics()
        
        print("\n" + "="*60)
        print("📊 СТАТИСТИКА ПАМЯТИ")
        print("="*60)
        
        # Эпизодическая
        ep = stats['episodic']
        print(f"\n💾 Эпизодическая память:")
        print(f"   Всего записей: {ep['total_memories']}")
        print(f"   Средняя валентность: {ep['average_valence']:+.3f}")
        print(f"   Средняя важность: {ep['average_importance']:.3f}")
        
        # Семантическая
        sem = stats['semantic']
        print(f"\n📚 Семантическая память:")
        print(f"   Всего концептов: {sem['total_memories']}")
        print(f"   Категорий: {sem['num_categories']}")
        print(f"   Средняя важность: {sem['average_importance']:.3f}")
        
        # Реляционная
        rel = stats['relational']
        print(f"\n🔗 Реляционная память:")
        print(f"   Всего сущностей: {rel['total_entities']}")
        print(f"   Всего связей: {rel['total_relations']}")
        print(f"   Типов сущностей: {rel['num_entity_types']}")
        
        # Личность
        per = stats['personality']
        print(f"\n👤 Личность:")
        print(f"   Доминирующая черта: {per['dominant_trait']}")
        print(f"   Топ ценностей: {per['top_values']}")
        print(f"   Настроение: {per['current_mood_valence']:+.3f}")
        
        print("\n" + "="*60)
    
    def show_episodic(self, limit: int = 10, session_id: Optional[str] = None):
        """Показать эпизодические воспоминания."""
        memories = self.memory.episodic.get_recent(
            session_id=session_id,
            limit=limit
        )
        
        print("\n" + "="*60)
        print(f"💾 ЭПИЗОДИЧЕСКАЯ ПАМЯТЬ (последние {len(memories)})")
        print("="*60)
        
        for i, mem in enumerate(memories, 1):
            emotion_icon = self._get_emotion_icon(mem.emotion_valence)
            print(f"\n{i}. [{mem.timestamp[:19]}] {emotion_icon} {mem.event_type}")
            print(f"   Содержание: {mem.content}")
            if mem.content != mem.goal and mem.goal:
                print(f"   Цель: {mem.goal[:80]}")
            print(f"   Тема: {mem.topic} | Намерение: {mem.intent}")
            print(f"   Важность: {mem.importance:.2f} | Эмоция: {mem.emotion_valence:+.2f}")
            if mem.user_reaction:
                print(f"   Реакция пользователя: {mem.user_reaction}")
        
        print("\n" + "="*60)
    
    def show_semantic(self, limit: int = 10):
        """Показать семантические воспоминания."""
        # Получаем все концепты
        concepts = self.memory.semantic.get_all_concepts()
        
        print("\n" + "="*60)
        print(f"📚 СЕМАНТИЧЕСКАЯ ПАМЯТЬ (концепты: {len(concepts)})")
        print("="*60)
        
        # Показываем первые N концептов с деталями
        for concept in concepts[:limit]:
            memories = self.memory.semantic.get_by_concept(concept, limit=1)
            if memories:
                mem = memories[0]
                print(f"\n• {concept} ({mem.category})")
                print(f"  Содержание: {mem.content}...")
                print(f"  Важность: {mem.importance:.2f} | Теги: {mem.tags}")
        
        print("\n" + "="*60)
    
    def show_relational(self, entity_name: Optional[str] = None):
        """Показать реляционную память."""
        if entity_name:
            # Показать связи конкретной сущности
            connections = self.memory.relational.get_entity_connections(entity_name, max_depth=2)
            
            if connections['entity']:
                print("\n" + "="*60)
                print(f"🔗 СВЯЗИ: {entity_name}")
                print("="*60)
                
                print(f"\nСущность: {connections['entity']['name']}")
                print(f"Тип: {connections['entity']['entity_type']}")
                
                if connections['connections']:
                    print(f"\nСвязи ({len(connections['connections'])}):")
                    for conn in connections['connections'][:10]:
                        print(f"  {conn['from']} --[{conn['relation']}]--> {conn['to']}")
                        print(f"    Сила: {conn['strength']:.2f}")
                else:
                    print("\nНет связей")
                
                print("="*60)
        else:
            # Показать общую статистику
            stats = self.memory.relational.get_statistics()
            
            print("\n" + "="*60)
            print("🔗 РЕЛЯЦИОННАЯ ПАМЯТЬ")
            print("="*60)
            
            print(f"\nВсего сущностей: {stats['total_entities']}")
            print(f"Всего связей: {stats['total_relations']}")
            print(f"Типов сущностей: {stats['num_entity_types']}")
            print(f"Типов связей: {stats['num_relation_types']}")
            
            # Показать типы сущностей
            entity_types = ['person', 'object', 'concept', 'goal', 'event', 'trait']
            print("\nСущности по типам:")
            for etype in entity_types:
                entities = self.memory.relational.get_entities_by_type(etype)
                if entities:
                    print(f"  {etype}: {len(entities)}")
            
            print("="*60)
    
    def show_personality(self):
        """Показать состояние личности."""
        state = self.memory.personality.get_state()
        
        print("\n" + "="*60)
        print("👤 ЛИЧНОСТЬ")
        print("="*60)
        
        # Черты
        print("\n📊 Черты (Big Five + дополнительные):")
        traits = [
            ("Openness", state.openness),
            ("Conscientiousness", state.conscientiousness),
            ("Extraversion", state.extraversion),
            ("Agreeableness", state.agreeableness),
            ("Neuroticism", state.neuroticism),
            ("Curiosity", state.curiosity),
            ("Creativity", state.creativity),
            ("Empathy", state.empathy),
            ("Humor", state.humor),
            ("Assertiveness", state.assertiveness)
        ]
        
        for name, value in traits:
            bar = "█" * int(value * 10) + "░" * (10 - int(value * 10))
            print(f"  {name:20} [{bar}] {value:.2f}")
        
        # Ценности
        print("\n🎯 Ценности:")
        top_values = state.get_top_values(8)
        for value, weight in top_values:
            bar = "★" * int(weight * 5) + "☆" * (5 - int(weight * 5))
            print(f"  {value:15} [{bar}] {weight:.2f}")
        
        # Настроение
        print("\n😊 Настроение:")
        emotion_icon = self._get_emotion_icon(state.mood_valence)
        print(f"  Валентность: {state.mood_valence:+.2f} {emotion_icon}")
        print(f"  Возбуждение: {state.mood_arousal:.2f}")
        
        # Отношения
        if state.relationships:
            print("\n🤝 Отношения:")
            for user_id, score in state.relationships.items():
                rel_bar = "♥" * int(score * 5) + "♡" * (5 - int(score * 5))
                print(f"  {user_id}: [{rel_bar}] {score:.2f}")
        
        # Доминирующая черта
        print(f"\n🏆 Доминирующая черта: {state.get_dominant_trait()}")
        print(f"📅 Обновлено: {state.last_updated[:19]}")
        print(f"🔢 Версия: {state.version}")
        
        print("="*60)
    
    def search_memory(self, query: str, search_type: str = "all"):
        """Поиск в памяти."""
        print(f"\n🔍 Поиск: '{query}' (тип: {search_type})")
        print("="*60)
        
        if search_type in ["all", "episodic"]:
            # Поиск в эпизодической по теме
            memories = self.memory.episodic.get_by_topic(query, limit=5)
            if memories:
                print(f"\n💾 Эпизодическая ({len(memories)}):")
                for mem in memories[:3]:
                    print(f"  - {mem.content[:60]}...")
        
        if search_type in ["all", "semantic"]:
            # Поиск в семантической
            memories = self.memory.semantic.get_by_concept(query, limit=5)
            if memories:
                print(f"\n📚 Семантическая ({len(memories)}):")
                for mem in memories[:3]:
                    print(f"  - {mem.concept}: {mem.content[:50]}...")
        
        if search_type in ["all", "relational"]:
            # Поиск в реляционной
            connections = self.memory.relational.get_entity_connections(query, max_depth=1)
            if connections['entity']:
                print(f"\n🔗 Реляционная:")
                print(f"  Найдена сущность: {query}")
                if connections['connections']:
                    print(f"  Связей: {len(connections['connections'])}")
        
        print("="*60)
    
    def export_memory(self, filename: str = "memory_export.json"):
        """Экспорт памяти в JSON."""
        data = {
            "exported_at": datetime.now().isoformat(),
            "episodic": [],
            "semantic": [],
            "relational": {
                "entities": [],
                "relations": []
            },
            "personality": self.memory.personality.get_state().to_dict()
        }
        
        # Эпизодическая
        memories = self.memory.episodic.get_recent(limit=100)
        for mem in memories:
            data["episodic"].append(mem.to_dict())
        
        # Семантическая (упрощённо)
        concepts = self.memory.semantic.get_all_concepts()
        for concept in concepts[:50]:
            mems = self.memory.semantic.get_by_concept(concept, limit=1)
            if mems:
                data["semantic"].append(mems[0].to_dict())
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Память экспортирована в {filename}")
        print(f"   Эпизодических: {len(data['episodic'])}")
        print(f"   Семантических: {len(data['semantic'])}")
    
    def _get_emotion_icon(self, valence: float) -> str:
        """Получить иконку эмоции по валентности."""
        if valence > 0.3:
            return "😊"
        elif valence > -0.3:
            return "😐"
        else:
            return "😢"


def interactive_mode():
    """Интерактивный режим."""
    inspector = MemoryInspector()
    
    print("\n" + "="*60)
    print("🔍 MEMORY INSPECTOR - Инструмент просмотра памяти")
    print("="*60)
    print("\nКоманды:")
    print("  stats          - общая статистика")
    print("  eps [N]        - эпизодическая (последние N)")
    print("  sem [N]        - семантическая")
    print("  rel [name]     - реляционная")
    print("  per            - личность")
    print("  search QUERY   - поиск")
    print("  export [file]  - экспорт в JSON")
    print("  help           - эта справка")
    print("  quit           - выход")
    print("="*60 + "\n")
    
    while True:
        try:
            cmd = input("memory> ").strip()
            
            if not cmd:
                continue
            
            if cmd.lower() in ["quit", "exit", "q"]:
                print("👋 До свидания!")
                break
            
            parts = cmd.split()
            command = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            if command == "help":
                print("\nКоманды:")
                print("  stats          - общая статистика")
                print("  eps [N]        - эпизодическая (последние N)")
                print("  sem [N]        - семантическая")
                print("  rel [name]     - реляционная или связи сущности")
                print("  per            - личность")
                print("  search QUERY   - поиск по памяти")
                print("  export [file]  - экспорт в JSON")
                print("  quit           - выход")
            
            elif command == "stats":
                inspector.show_statistics()
            
            elif command in ["eps", "episodic"]:
                limit = int(args[0]) if args else 10
                inspector.show_episodic(limit=limit)
            
            elif command in ["sem", "semantic"]:
                limit = int(args[0]) if args else 10
                inspector.show_semantic(limit=limit)
            
            elif command in ["rel", "relational"]:
                if args:
                    inspector.show_relational(entity_name=args[0])
                else:
                    inspector.show_relational()
            
            elif command in ["per", "personality"]:
                inspector.show_personality()
            
            elif command == "search":
                if args:
                    query = " ".join(args)
                    inspector.search_memory(query)
                else:
                    print("⚠️ Введите запрос: search QUERY")
            
            elif command == "export":
                filename = args[0] if args else "memory_export.json"
                inspector.export_memory(filename)
            
            else:
                print(f"⚠️ Неизвестная команда: {command}")
                print("Введите 'help' для справки")
        
        except ValueError as e:
            print(f"⚠️ Ошибка формата: {e}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    # Если есть аргументы командной строки - показать статистику
    if len(sys.argv) > 1:
        inspector = MemoryInspector()
        
        if sys.argv[1] == "--stats":
            inspector.show_statistics()
        elif sys.argv[1] == "--eps":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            inspector.show_episodic(limit=limit)
        elif sys.argv[1] == "--per":
            inspector.show_personality()
        elif sys.argv[1] == "--export":
            filename = sys.argv[2] if len(sys.argv) > 2 else "memory_export.json"
            inspector.export_memory(filename)
        else:
            print("Использование:")
            print("  python memory_inspector.py           - интерактивный режим")
            print("  python memory_inspector.py --stats   - статистика")
            print("  python memory_inspector.py --eps [N] - эпизодическая")
            print("  python memory_inspector.py --per     - личность")
            print("  python memory_inspector.py --export  - экспорт")
    else:
        interactive_mode()

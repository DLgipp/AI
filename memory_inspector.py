"""
Memory Inspector - Интерактивный инструмент для просмотра и анализа памяти ассистента.

Использование:
    python memory_inspector.py                    - интерактивный режим
    python memory_inspector.py --stats            - показать статистику
    python memory_inspector.py --eps [N]          - эпизодическая память
    python memory_inspector.py --sem [N]          - семантическая память
    python memory_inspector.py --rel [name]       - реляционная память
    python memory_inspector.py --per              - личность
    python memory_inspector.py --export [file]    - экспорт в JSON
"""

import json
import sys
from datetime import datetime
from typing import Optional, List
from dataclasses import asdict

# Настройка UTF-8 для Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.tree import Tree
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️ Rich не установлен. Установите: pip install rich")


class MemoryInspector:
    """Инспектор памяти с красивым выводом."""

    def __init__(self):
        """Инициализация инспектора."""
        from modules.memory import MemoryLayer
        from modules.memory.personality_memory import PersonalityState
        
        self.memory = MemoryLayer()
        self.console = Console() if RICH_AVAILABLE else None

    # ==================== СТАТИСТИКА ====================
    
    def show_statistics(self):
        """Показать общую статистику по всем системам памяти."""
        stats = self.memory.get_statistics()

        if RICH_AVAILABLE:
            self._show_statistics_rich(stats)
        else:
            self._show_statistics_text(stats)

    def _show_statistics_rich(self, stats: dict):
        """Красивый вывод статистики с Rich."""
        self.console.print("\n[bold blue]═" * 70)
        self.console.print(Panel(
            "[bold white]📊 СТАТИСТИКА ПАМЯТИ[/bold white]",
            border_style="blue",
            title="[bold]ОБЗОР[/bold]"
        ))
        self.console.print("[bold blue]═" * 70 + "\n")

        # Эпизодическая память
        ep = stats['episodic']
        table_ep = Table(title="💾 Эпизодическая память", box=box.ROUNDED, border_style="cyan")
        table_ep.add_column("Метрика", style="cyan", justify="left")
        table_ep.add_column("Значение", style="white", justify="right")
        table_ep.add_row("📝 Всего записей", str(ep['total_memories']))
        table_ep.add_row("😊 Средняя валентность", f"{ep['average_valence']:+.3f}")
        table_ep.add_row("⭐ Средняя важность", f"{ep['average_importance']:.3f}")
        self.console.print(table_ep)

        # Семантическая память
        sem = stats['semantic']
        table_sem = Table(title="📚 Семантическая память", box=box.ROUNDED, border_style="green")
        table_sem.add_column("Метрика", style="green", justify="left")
        table_sem.add_column("Значение", style="white", justify="right")
        table_sem.add_row("🧠 Всего концептов", str(sem['total_memories']))
        table_sem.add_row("📁 Категорий", str(sem['num_categories']))
        table_sem.add_row("⭐ Средняя важность", f"{sem['average_importance']:.3f}")
        self.console.print(table_sem)

        # Реляционная память
        rel = stats['relational']
        table_rel = Table(title="🔗 Реляционная память", box=box.ROUNDED, border_style="magenta")
        table_rel.add_column("Метрика", style="magenta", justify="left")
        table_rel.add_column("Значение", style="white", justify="right")
        table_rel.add_row("🎯 Всего сущностей", str(rel['total_entities']))
        table_rel.add_row("🔗 Всего связей", str(rel['total_relations']))
        table_rel.add_row("📊 Типов сущностей", str(rel['num_entity_types']))
        self.console.print(table_rel)

        # Личность
        per = stats['personality']
        table_per = Table(title="👤 Личность", box=box.ROUNDED, border_style="yellow")
        table_per.add_column("Метрика", style="yellow", justify="left")
        table_per.add_column("Значение", style="white", justify="right")
        table_per.add_row("🏆 Доминирующая черта", per['dominant_trait'])
        top_values_str = ", ".join([f"{v} ({w:.1f})" for v, w in per['top_values'][:3]])
        table_per.add_row("🎯 Топ ценностей", top_values_str)
        mood_icon = "😊" if per['current_mood_valence'] > 0 else "😢" if per['current_mood_valence'] < 0 else "😐"
        table_per.add_row("😊 Настроение", f"{per['current_mood_valence']:+.3f} {mood_icon}")
        self.console.print(table_per)

    def _show_statistics_text(self, stats: dict):
        """Текстовый вывод статистики."""
        print("\n" + "="*70)
        print("📊 СТАТИСТИКА ПАМЯТИ")
        print("="*70)

        ep = stats['episodic']
        print(f"\n💾 Эпизодическая память:")
        print(f"   Всего записей: {ep['total_memories']}")
        print(f"   Средняя валентность: {ep['average_valence']:+.3f}")
        print(f"   Средняя важность: {ep['average_importance']:.3f}")

        sem = stats['semantic']
        print(f"\n📚 Семантическая память:")
        print(f"   Всего концептов: {sem['total_memories']}")
        print(f"   Категорий: {sem['num_categories']}")
        print(f"   Средняя важность: {sem['average_importance']:.3f}")

        rel = stats['relational']
        print(f"\n🔗 Реляционная память:")
        print(f"   Всего сущностей: {rel['total_entities']}")
        print(f"   Всего связей: {rel['total_relations']}")
        print(f"   Типов сущностей: {rel['num_entity_types']}")

        per = stats['personality']
        print(f"\n👤 Личность:")
        print(f"   Доминирующая черта: {per['dominant_trait']}")
        print(f"   Топ ценностей: {per['top_values']}")
        print(f"   Настроение: {per['current_mood_valence']:+.3f}")

        print("\n" + "="*70)

    # ==================== ЭПИЗОДИЧЕСКАЯ ПАМЯТЬ ====================

    def show_episodic(self, limit: int = 10, session_id: Optional[str] = None):
        """Показать эпизодические воспоминания."""
        memories = self.memory.episodic.get_recent(
            session_id=session_id,
            limit=limit
        )

        if RICH_AVAILABLE:
            self._show_episodic_rich(memories)
        else:
            self._show_episodic_text(memories)

    def _show_episodic_rich(self, memories: list):
        """Красивый вывод эпизодической памяти."""
        self.console.print("\n[bold cyan]═" * 70)
        self.console.print(Panel(
            f"[bold white]💾 ЭПИЗОДИЧЕСКАЯ ПАМЯТЬ[/bold white] ({len(memories)} записей)",
            border_style="cyan"
        ))
        self.console.print("[bold cyan]═" * 70 + "\n")

        table = Table(title="История событий", box=box.ROUNDED, border_style="cyan")
        table.add_column("№", style="dim", justify="right")
        table.add_column("Время", style="cyan", justify="left")
        table.add_column("Тип", style="yellow", justify="left")
        table.add_column("Содержание", style="white", justify="left")
        table.add_column("Эмоция", justify="center")
        table.add_column("Важн.", justify="right")

        for i, mem in enumerate(memories, 1):
            emotion_icon = self._get_emotion_icon(mem.emotion_valence)
            event_type_map = {
                'user_message': '👤 USER',
                'assistant_message': '🤖 AI',
                'system_event': '⚙️ SYS'
            }
            event_type = event_type_map.get(mem.event_type, mem.event_type)
            
            content_preview = mem.content[:50] + "..." if len(mem.content) > 50 else mem.content
            
            table.add_row(
                str(i),
                mem.timestamp[:16],
                event_type,
                content_preview,
                emotion_icon,
                f"{mem.importance:.2f}"
            )

        self.console.print(table)

    def _show_episodic_text(self, memories: list):
        """Текстовый вывод эпизодической памяти."""
        print("\n" + "="*70)
        print(f"💾 ЭПИЗОДИЧЕСКАЯ ПАМЯТЬ (последние {len(memories)})")
        print("="*70)

        for i, mem in enumerate(memories, 1):
            emotion_icon = self._get_emotion_icon(mem.emotion_valence)
            print(f"\n{i}. [{mem.timestamp[:19]}] {emotion_icon} {mem.event_type}")
            print(f"   Содержание: {mem.content}")
            if mem.goal:
                print(f"   Цель: {mem.goal[:80]}")
            print(f"   Тема: {mem.topic} | Намерение: {mem.intent}")
            print(f"   Важность: {mem.importance:.2f} | Эмоция: {mem.emotion_valence:+.2f}")

        print("\n" + "="*70)

    # ==================== СЕМАНТИЧЕСКАЯ ПАМЯТЬ ====================

    def show_semantic(self, limit: int = 10):
        """Показать семантические воспоминания."""
        concepts = self.memory.semantic.get_all_concepts()
        
        # Получаем детали для каждого концепта
        concept_details = []
        for concept in concepts[:limit]:
            memories = self.memory.semantic.get_by_concept(concept, limit=1)
            if memories:
                mem = memories[0]
                concept_details.append(mem)

        if RICH_AVAILABLE:
            self._show_semantic_rich(concept_details, len(concepts))
        else:
            self._show_semantic_text(concept_details, len(concepts))

    def _show_semantic_rich(self, memories: list, total_concepts: int):
        """Красивый вывод семантической памяти."""
        self.console.print("\n[bold green]═" * 70)
        self.console.print(Panel(
            f"[bold white]📚 СЕМАНТИЧЕСКАЯ ПАМЯТЬ[/bold white] ({total_concepts} концептов)",
            border_style="green"
        ))
        self.console.print("[bold green]═" * 70 + "\n")

        table = Table(title="Концепты и знания", box=box.ROUNDED, border_style="green")
        table.add_column("Концепт", style="green", justify="left")
        table.add_column("Категория", style="yellow", justify="left")
        table.add_column("Содержание", style="white", justify="left")
        table.add_column("Теги", style="cyan", justify="left")
        table.add_column("Важн.", justify="right")

        for mem in memories:
            content_preview = mem.content[:60] + "..." if len(mem.content) > 60 else mem.content
            tags_str = ", ".join(mem.tags[:3]) if mem.tags else "-"
            
            table.add_row(
                mem.concept,
                mem.category,
                content_preview,
                tags_str,
                f"{mem.importance:.2f}"
            )

        self.console.print(table)

    def _show_semantic_text(self, memories: list, total_concepts: int):
        """Текстовый вывод семантической памяти."""
        print("\n" + "="*70)
        print(f"📚 СЕМАНТИЧЕСКАЯ ПАМЯТЬ (концепты: {total_concepts})")
        print("="*70)

        for mem in memories:
            print(f"\n• {mem.concept} ({mem.category})")
            print(f"  Содержание: {mem.content[:80]}...")
            print(f"  Важность: {mem.importance:.2f} | Теги: {', '.join(mem.tags[:3]) if mem.tags else '-'}")

        print("\n" + "="*70)

    # ==================== РЕЛЯЦИОННАЯ ПАМЯТЬ ====================

    def show_relational(self, entity_name: Optional[str] = None):
        """Показать реляционную память."""
        if entity_name:
            self._show_entity_connections(entity_name)
        else:
            self._show_relational_overview()

    def _show_entity_connections(self, entity_name: str):
        """Показать связи конкретной сущности."""
        try:
            connections = self.memory.relational.get_entity_connections(entity_name, max_depth=2)
        except Exception as e:
            if RICH_AVAILABLE:
                self.console.print(f"\n[red]❌ Ошибка: {e}[/red]")
            else:
                print(f"❌ Ошибка: {e}")
            return

        if RICH_AVAILABLE:
            self._show_entity_connections_rich(entity_name, connections)
        else:
            self._show_entity_connections_text(entity_name, connections)

    def _show_entity_connections_rich(self, entity_name: str, connections: dict):
        """Красивый вывод связей сущности."""
        self.console.print("\n[bold magenta]═" * 70)
        self.console.print(Panel(
            f"[bold white]🔗 СВЯЗИ: {entity_name}[/bold white]",
            border_style="magenta"
        ))
        self.console.print("[bold magenta]═" * 70 + "\n")

        if connections.get('entity'):
            entity = connections['entity']
            
            # Информация о сущности
            info_table = Table(box=box.SIMPLE)
            info_table.add_column("Свойство", style="cyan")
            info_table.add_column("Значение", style="white")
            info_table.add_row("🏷️ Название", entity.get('name', 'N/A'))
            info_table.add_row("📊 Тип", entity.get('entity_type', 'N/A'))
            self.console.print(info_table)

            # Связи
            if connections.get('connections'):
                self.console.print("\n[bold]Связи:[/bold]")
                
                tree = Tree(f"[bold]{entity_name}[/bold]")
                
                for conn in connections['connections'][:15]:
                    branch = tree.add(f"[yellow]{conn.get('relation', 'related')}[/yellow]")
                    branch.add(f"[cyan]{conn.get('to', conn.get('from', 'unknown'))}[/cyan]")
                
                self.console.print(tree)
            else:
                self.console.print("\n[yellow]⚠️ Нет связей[/yellow]")
        else:
            self.console.print(f"[yellow]⚠️ Сущность '{entity_name}' не найдена[/yellow]")

    def _show_entity_connections_text(self, entity_name: str, connections: dict):
        """Текстовый вывод связей сущности."""
        print("\n" + "="*70)
        print(f"🔗 СВЯЗИ: {entity_name}")
        print("="*70)

        if connections.get('entity'):
            entity = connections['entity']
            print(f"\nСущность: {entity.get('name', 'N/A')}")
            print(f"Тип: {entity.get('entity_type', 'N/A')}")

            if connections.get('connections'):
                print(f"\nСвязи ({len(connections['connections'])}):")
                for conn in connections['connections'][:10]:
                    print(f"  {conn.get('from', '?')} --[{conn.get('relation', '?')}]--> {conn.get('to', '?')}")
            else:
                print("\nНет связей")
        else:
            print(f"⚠️ Сущность '{entity_name}' не найдена")

        print("="*70)

    def _show_relational_overview(self):
        """Показать общий обзор реляционной памяти."""
        stats = self.memory.relational.get_statistics()

        if RICH_AVAILABLE:
            self._show_relational_overview_rich(stats)
        else:
            self._show_relational_overview_text(stats)

    def _show_relational_overview_rich(self, stats: dict):
        """Красивый общий обзор реляционной памяти."""
        self.console.print("\n[bold magenta]═" * 70)
        self.console.print(Panel(
            "[bold white]🔗 РЕЛЯЦИОННАЯ ПАМЯТЬ[/bold white]",
            border_style="magenta"
        ))
        self.console.print("[bold magenta]═" * 70 + "\n")

        # Общая статистика
        table = Table(title="Статистика графа", box=box.ROUNDED, border_style="magenta")
        table.add_column("Метрика", style="magenta", justify="left")
        table.add_column("Значение", style="white", justify="right")
        table.add_row("🎯 Всего сущностей", str(stats['total_entities']))
        table.add_row("🔗 Всего связей", str(stats['total_relations']))
        table.add_row("📊 Типов сущностей", str(stats['num_entity_types']))
        table.add_row("🔗 Типов связей", str(stats['num_relation_types']))
        self.console.print(table)

        # Типы сущностей
        entity_types = ['person', 'object', 'concept', 'goal', 'event', 'trait']
        
        type_table = Table(title="Сущности по типам", box=box.SIMPLE)
        type_table.add_column("Тип", style="cyan", justify="left")
        type_table.add_column("Количество", style="white", justify="right")

        for etype in entity_types:
            try:
                entities = self.memory.relational.get_entities_by_type(etype)
                count = len(entities) if entities else 0
                if count > 0:
                    type_table.add_row(f"📁 {etype}", str(count))
            except Exception:
                pass

        self.console.print(type_table)

    def _show_relational_overview_text(self, stats: dict):
        """Текстовый общий обзор реляционной памяти."""
        print("\n" + "="*70)
        print("🔗 РЕЛЯЦИОННАЯ ПАМЯТЬ")
        print("="*70)

        print(f"\nВсего сущностей: {stats['total_entities']}")
        print(f"Всего связей: {stats['total_relations']}")
        print(f"Типов сущностей: {stats['num_entity_types']}")
        print(f"Типов связей: {stats['num_relation_types']}")

        # Показать типы сущностей
        entity_types = ['person', 'object', 'concept', 'goal', 'event', 'trait']
        print("\nСущности по типам:")
        for etype in entity_types:
            try:
                entities = self.memory.relational.get_entities_by_type(etype)
                if entities:
                    print(f"  {etype}: {len(entities)}")
            except Exception:
                pass

        print("="*70)

    # ==================== ЛИЧНОСТЬ ====================

    def show_personality(self):
        """Показать состояние личности."""
        state = self.memory.personality.get_state()

        if RICH_AVAILABLE:
            self._show_personality_rich(state)
        else:
            self._show_personality_text(state)

    def _show_personality_rich(self, state):
        """Красивый вывод личности."""
        self.console.print("\n[bold yellow]═" * 70)
        self.console.print(Panel(
            "[bold white]👤 ЛИЧНОСТЬ[/bold white]",
            border_style="yellow"
        ))
        self.console.print("[bold yellow]═" * 70 + "\n")

        # Черты личности
        self.console.print("[bold]📊 Черты личности (Big Five + дополнительные)[/bold]\n")

        traits_table = Table(box=box.SIMPLE)
        traits_table.add_column("Черта", style="cyan", justify="left")
        traits_table.add_column("Шкала", justify="left")
        traits_table.add_column("Значение", style="white", justify="right")

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
            traits_table.add_row(name, f"[green]{bar}[/green]", f"{value:.2f}")

        self.console.print(traits_table)

        # Ценности
        self.console.print("\n[bold]🎯 Ценности (топ-8)[/bold]\n")

        values_table = Table(box=box.SIMPLE)
        values_table.add_column("Ценность", style="yellow", justify="left")
        values_table.add_column("Шкала", justify="left")
        values_table.add_column("Вес", style="white", justify="right")

        top_values = state.get_top_values(8)
        for value, weight in top_values:
            stars = "★" * int(weight * 5) + "☆" * (5 - int(weight * 5))
            values_table.add_row(value, f"[gold]{stars}[/gold]", f"{weight:.2f}")

        self.console.print(values_table)

        # Настроение
        self.console.print("\n[bold]😊 Настроение[/bold]")
        mood_valence = state.mood_valence
        mood_arousal = state.mood_arousal
        
        emotion_icon = self._get_emotion_icon(mood_valence)
        arousal_level = "Высокое" if mood_arousal > 0.7 else "Низкое" if mood_arousal < 0.3 else "Среднее"
        
        mood_text = Text()
        mood_text.append(f"Валентность: {mood_valence:+.2f} ", style="white")
        mood_text.append(f"{emotion_icon} ", style="bold")
        mood_text.append(f"({arousal_level} возбуждение: {mood_arousal:.2f})", style="dim")
        self.console.print(mood_text)

        # Отношения
        if state.relationships:
            self.console.print("\n[bold]🤝 Отношения[/bold]")
            for user_id, score in state.relationships.items():
                hearts = "♥" * int(score * 5) + "♡" * (5 - int(score * 5))
                self.console.print(f"  [red]{hearts}[/red] {user_id}: {score:.2f}")

        # Доминирующая черта
        self.console.print(f"\n[bold]🏆 Доминирующая черта:[/bold] [green]{state.get_dominant_trait()}[/green]")
        self.console.print(f"[bold]📅 Обновлено:[/bold] {state.last_updated[:19] if state.last_updated else 'N/A'}")
        self.console.print(f"[bold]🔢 Версия:[/bold] {state.version}")

    def _show_personality_text(self, state):
        """Текстовый вывод личности."""
        print("\n" + "="*70)
        print("👤 ЛИЧНОСТЬ")
        print("="*70)

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
            stars = "★" * int(weight * 5) + "☆" * (5 - int(weight * 5))
            print(f"  {value:15} [{stars}] {weight:.2f}")

        # Настроение
        print("\n😊 Настроение:")
        emotion_icon = self._get_emotion_icon(state.mood_valence)
        print(f"  Валентность: {state.mood_valence:+.2f} {emotion_icon}")
        print(f"  Возбуждение: {state.mood_arousal:.2f}")

        # Отношения
        if state.relationships:
            print("\n🤝 Отношения:")
            for user_id, score in state.relationships.items():
                hearts = "♥" * int(score * 5) + "♡" * (5 - int(score * 5))
                print(f"  {user_id}: [{hearts}] {score:.2f}")

        # Доминирующая черта
        print(f"\n🏆 Доминирующая черта: {state.get_dominant_trait()}")
        print(f"📅 Обновлено: {state.last_updated[:19] if state.last_updated else 'N/A'}")
        print(f"🔢 Версия: {state.version}")

        print("="*70)

    # ==================== ПОИСК ====================

    def search_memory(self, query: str, search_type: str = "all"):
        """Поиск в памяти."""
        if RICH_AVAILABLE:
            self.console.print(f"\n[bold]🔍 Поиск: '{query}'[/bold] (тип: {search_type})")
            self.console.print("[bold blue]═" * 70 + "\n")
        else:
            print(f"\n🔍 Поиск: '{query}' (тип: {search_type})")
            print("="*70)

        results_found = False

        if search_type in ["all", "episodic"]:
            try:
                memories = self.memory.episodic.get_by_topic(query, limit=5)
                if memories:
                    results_found = True
                    if RICH_AVAILABLE:
                        self.console.print(f"[bold cyan]💾 Эпизодическая ({len(memories)}):[/bold cyan]")
                        for mem in memories[:3]:
                            preview = mem.content[:60] + "..." if len(mem.content) > 60 else mem.content
                            self.console.print(f"  • {preview}")
                        self.console.print()
                    else:
                        print(f"\n💾 Эпизодическая ({len(memories)}):")
                        for mem in memories[:3]:
                            print(f"  - {mem.content[:60]}...")
            except Exception:
                pass

        if search_type in ["all", "semantic"]:
            try:
                memories = self.memory.semantic.get_by_concept(query, limit=5)
                if memories:
                    results_found = True
                    if RICH_AVAILABLE:
                        self.console.print(f"[bold green]📚 Семантическая ({len(memories)}):[/bold green]")
                        for mem in memories[:3]:
                            self.console.print(f"  • {mem.concept}: {mem.content[:50]}...")
                        self.console.print()
                    else:
                        print(f"\n📚 Семантическая ({len(memories)}):")
                        for mem in memories[:3]:
                            print(f"  - {mem.concept}: {mem.content[:50]}...")
            except Exception:
                pass

        if search_type in ["all", "relational"]:
            try:
                connections = self.memory.relational.get_entity_connections(query, max_depth=1)
                if connections.get('entity'):
                    results_found = True
                    if RICH_AVAILABLE:
                        self.console.print(f"[bold magenta]🔗 Реляционная:[/bold magenta]")
                        self.console.print(f"  Найдена сущность: [bold]{query}[/bold]")
                        if connections.get('connections'):
                            self.console.print(f"  Связей: {len(connections['connections'])}")
                        self.console.print()
                    else:
                        print(f"\n🔗 Реляционная:")
                        print(f"  Найдена сущность: {query}")
                        if connections.get('connections'):
                            print(f"  Связей: {len(connections['connections'])}")
            except Exception:
                pass

        if not results_found:
            if RICH_AVAILABLE:
                self.console.print("[yellow]⚠️ Ничего не найдено[/yellow]")
            else:
                print("⚠️ Ничего не найдено")

        print("="*70)

    # ==================== ЭКСПОРТ ====================

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
        try:
            memories = self.memory.episodic.get_recent(limit=100)
            for mem in memories:
                data["episodic"].append(mem.to_dict())
        except Exception as e:
            if RICH_AVAILABLE:
                self.console.print(f"[yellow]⚠️ Ошибка экспорта эпизодической: {e}[/yellow]")
            else:
                print(f"⚠️ Ошибка экспорта эпизодической: {e}")

        # Семантическая
        try:
            concepts = self.memory.semantic.get_all_concepts()
            for concept in concepts[:50]:
                mems = self.memory.semantic.get_by_concept(concept, limit=1)
                if mems:
                    mem_dict = mems[0].to_dict()
                    # Убираем embedding для экономии места
                    mem_dict.pop('embedding', None)
                    data["semantic"].append(mem_dict)
        except Exception as e:
            if RICH_AVAILABLE:
                self.console.print(f"[yellow]⚠️ Ошибка экспорта семантической: {e}[/yellow]")
            else:
                print(f"⚠️ Ошибка экспорта семантической: {e}")

        # Реляционная (упрощённо)
        try:
            stats = self.memory.relational.get_statistics()
            data["relational"]["stats"] = stats
        except Exception:
            pass

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        if RICH_AVAILABLE:
            self.console.print(f"\n[green]✅ Память экспортирована в {filename}[/green]")
            self.console.print(f"   Эпизодических: {len(data['episodic'])}")
            self.console.print(f"   Семантических: {len(data['semantic'])}")
            self.console.print(f"   Личность: {len(data['personality'])} полей")
        else:
            print(f"✅ Память экспортирована в {filename}")
            print(f"   Эпизодических: {len(data['episodic'])}")
            print(f"   Семантических: {len(data['semantic'])}")

    # ==================== УТИЛИТЫ ====================

    def _get_emotion_icon(self, valence: float) -> str:
        """Получить иконку эмоции по валентности."""
        if valence > 0.3:
            return "😊"
        elif valence > -0.3:
            return "😐"
        else:
            return "😢"


def interactive_mode():
    """Интерактивный режим с улучшенным UI."""
    inspector = MemoryInspector()

    if RICH_AVAILABLE:
        inspector.console.print("\n[bold blue]═" * 70)
        inspector.console.print(Panel(
            "[bold white]🔍 MEMORY INSPECTOR[/bold white]\n"
            "[dim]Инструмент просмотра и анализа памяти ассистента[/dim]",
            border_style="blue"
        ))
        inspector.console.print("[bold blue]═" * 70 + "\n")

        inspector.console.print("[bold]Команды:[/bold]")
        commands = [
            ("stats", "Общая статистика"),
            ("eps [N]", "Эпизодическая память (последние N)"),
            ("sem [N]", "Семантическая память"),
            ("rel [name]", "Реляционная память или связи сущности"),
            ("per", "Личность"),
            ("search QUERY", "Поиск по памяти"),
            ("export [file]", "Экспорт в JSON"),
            ("help", "Эта справка"),
            ("quit", "Выход")
        ]
        
        for cmd, desc in commands:
            inspector.console.print(f"  [cyan]{cmd:15}[/cyan] - {desc}")
        
        inspector.console.print("\n" + "[bold blue]═" * 70 + "\n")
    else:
        print("\n" + "="*70)
        print("🔍 MEMORY INSPECTOR - Инструмент просмотра памяти")
        print("="*70)
        print("\nКоманды:")
        print("  stats          - общая статистика")
        print("  eps [N]        - эпизодическая (последние N)")
        print("  sem [N]        - семантическая")
        print("  rel [name]     - реляционная или связи сущности")
        print("  per            - личность")
        print("  search QUERY   - поиск")
        print("  export [file]  - экспорт в JSON")
        print("  help           - эта справка")
        print("  quit           - выход")
        print("="*70 + "\n")

    while True:
        try:
            cmd = input("memory> ").strip()

            if not cmd:
                continue

            if cmd.lower() in ["quit", "exit", "q"]:
                if RICH_AVAILABLE:
                    inspector.console.print("\n[yellow]👋 До свидания![/yellow]\n")
                else:
                    print("👋 До свидания!")
                break

            parts = cmd.split()
            command = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []

            if command == "help":
                if RICH_AVAILABLE:
                    inspector.console.print("\n[bold]Доступные команды:[/bold]")
                    for cmd_name, desc in commands:
                        inspector.console.print(f"  [cyan]{cmd_name:15}[/cyan] - {desc}")
                else:
                    print("\nКоманды:")
                    for cmd_name, desc in commands:
                        print(f"  {cmd_name:15} - {desc}")

            elif command == "stats":
                inspector.show_statistics()

            elif command in ["eps", "episodic"]:
                limit = int(args[0]) if args and args[0].isdigit() else 10
                inspector.show_episodic(limit=limit)

            elif command in ["sem", "semantic"]:
                limit = int(args[0]) if args and args[0].isdigit() else 10
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
                    if RICH_AVAILABLE:
                        inspector.console.print("[yellow]⚠️ Введите запрос: search QUERY[/yellow]")
                    else:
                        print("⚠️ Введите запрос: search QUERY")

            elif command == "export":
                filename = args[0] if args else "memory_export.json"
                inspector.export_memory(filename)

            else:
                if RICH_AVAILABLE:
                    inspector.console.print(f"[yellow]⚠️ Неизвестная команда: {command}[/yellow]")
                    inspector.console.print("[dim]Введите 'help' для справки[/dim]")
                else:
                    print(f"⚠️ Неизвестная команда: {command}")
                    print("Введите 'help' для справки")

        except ValueError as e:
            if RICH_AVAILABLE:
                inspector.console.print(f"[yellow]⚠️ Ошибка формата: {e}[/yellow]")
            else:
                print(f"⚠️ Ошибка формата: {e}")
        except Exception as e:
            if RICH_AVAILABLE:
                inspector.console.print(f"[red]❌ Ошибка: {e}[/red]")
            else:
                print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    # Обработка аргументов командной строки
    if len(sys.argv) > 1:
        inspector = MemoryInspector()

        if sys.argv[1] == "--stats":
            inspector.show_statistics()
        elif sys.argv[1] == "--eps":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            inspector.show_episodic(limit=limit)
        elif sys.argv[1] == "--sem":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            inspector.show_semantic(limit=limit)
        elif sys.argv[1] == "--rel":
            entity_name = sys.argv[2] if len(sys.argv) > 2 else None
            inspector.show_relational(entity_name=entity_name)
        elif sys.argv[1] == "--per":
            inspector.show_personality()
        elif sys.argv[1] == "--export":
            filename = sys.argv[2] if len(sys.argv) > 2 else "memory_export.json"
            inspector.export_memory(filename)
        elif sys.argv[1] == "--search":
            query = sys.argv[2] if len(sys.argv) > 2 else ""
            if query:
                inspector.search_memory(query)
            else:
                print("⚠️ Введите запрос: --search QUERY")
        elif sys.argv[1] in ["--help", "-h"]:
            print("Использование:")
            print("  python memory_inspector.py              - интерактивный режим")
            print("  python memory_inspector.py --stats      - общая статистика")
            print("  python memory_inspector.py --eps [N]    - эпизодическая (последние N)")
            print("  python memory_inspector.py --sem [N]    - семантическая")
            print("  python memory_inspector.py --rel [name] - реляционная или связи")
            print("  python memory_inspector.py --per        - личность")
            print("  python memory_inspector.py --search Q   - поиск")
            print("  python memory_inspector.py --export [f] - экспорт в JSON")
        else:
            print("⚠️ Неизвестный аргумент:", sys.argv[1])
            print("Используйте --help для справки")
    else:
        interactive_mode()

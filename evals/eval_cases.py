"""
Definición de casos de prueba y evaluación para el Swarm de diseño de juegos.

A diferencia de Agents-as-Tools (donde hay UN agente esperado por caso),
en Swarm no hay una ruta fija: se evalúan propiedades de la topología
resultante (qué agentes participaron, cuántos, si convergió) en vez de
una secuencia exacta.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class EvalCase:
    name: str
    premise: str
    entry_point_expected: str = "mechanic_designer"
    min_unique_agents: int = 3          # mismo espíritu que REPETITIVE_HANDOFF_MIN_UNIQUE_AGENTS
    required_agents: List[str] = field(default_factory=list)  # agentes que DEBEN aparecer
    expected_keywords: List[str] = field(default_factory=list)  # palabras clave esperadas en el GDD final


EVAL_CASES = [
    EvalCase(
        name="Roguelike de cocina en castillo maldito",
        premise=(
            "Cooking roguelike set in a cursed castle. The player is a chef "
            "trapped in a castle that reconfigures itself every night. They "
            "must cook dishes using ingredients that only appear in specific "
            "rooms, in order to weaken (or feed) the curse that keeps them "
            "imprisoned."
        ),
        min_unique_agents=3,
        required_agents=["mechanic_designer"],  # el entry point siempre debe aparecer
        expected_keywords=["curse", "ingredient", "castle"],
    ),
]
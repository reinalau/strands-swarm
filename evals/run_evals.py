"""
Evaluaciones del patrón Swarm: combinación de Evaluación por Trayectoria
(topología de handoffs resultante) y Evaluación por Salida (contenido del GDD).

A diferencia de Agents-as-Tools, acá no se compara contra UN agente
esperado, sino contra propiedades estructurales de la ejecución:
- ¿Cuántos agentes únicos participaron?
- ¿El entry point fue el correcto?
- ¿El GDD final contiene las palabras clave del dominio del juego?
"""
from strands_evals.types.evaluation import EvaluationOutput

from evals.eval_cases import EVAL_CASES
from src.config import MODEL_NAME, MODEL_PROVIDER, GEMINI_MODEL_NAME
from src.swarm.build_swarm import build_swarm
from src.output.gdd_builder import build_gdd


def extract_unique_agents(node_history) -> list[str]:
    """Extrae la lista de agentes únicos que participaron en la ejecución."""
    seen = []
    for node in node_history:
        if node.node_id not in seen:
            seen.append(node.node_id)
    return seen


def evaluate_trajectory(case, node_history) -> EvaluationOutput:
    """Evalúa la FORMA de la topología resultante, no una secuencia exacta."""
    if not node_history:
        return EvaluationOutput(
            score=0.0, test_pass=False,
            reason="El swarm no ejecutó ningún nodo.",
        )

    unique_agents = extract_unique_agents(node_history)
    entry_point_ok = node_history[0].node_id == case.entry_point_expected
    enough_agents = len(unique_agents) >= case.min_unique_agents
    required_present = all(a in unique_agents for a in case.required_agents)

    passed = entry_point_ok and enough_agents and required_present
    reason = (
        f"Agentes únicos: {unique_agents} ({len(unique_agents)}/{case.min_unique_agents} mín). "
        f"Entry point correcto: {entry_point_ok}. "
        f"Requeridos presentes: {required_present}."
    )
    return EvaluationOutput(score=1.0 if passed else 0.0, test_pass=passed, reason=reason)


def evaluate_output_keywords(case, gdd_text: str) -> EvaluationOutput:
    """Evalúa si el GDD final contiene las palabras clave del dominio."""
    text_lower = gdd_text.lower()
    missing = [kw for kw in case.expected_keywords if kw.lower() not in text_lower]
    passed = len(missing) == 0
    reason = f"Keywords {case.expected_keywords}. " + (
        "Todas encontradas." if passed else f"Faltaron: {missing}."
    )
    return EvaluationOutput(score=1.0 if passed else 0.0, test_pass=passed, reason=reason)


def main():
    active_model = GEMINI_MODEL_NAME if MODEL_PROVIDER == "gemini" else MODEL_NAME
    print("=== Evaluaciones Completa: Trayectoria + Salida (Swarm) ===")
    print(f"Modelo: {active_model} ({MODEL_PROVIDER})\n")

    results = []
    for case in EVAL_CASES:
        print(f"[DEBUG] Evaluando caso: '{case.name}'", flush=True)

        swarm = build_swarm()
        result = swarm(case.premise)
        gdd_text = build_gdd(case.premise, result)

        # 1. Evaluación por Trayectoria (forma de la topología)
        traj_eval = evaluate_trajectory(case, result.node_history)

        # 2. Evaluación por Salida (keywords en el GDD)
        out_eval = evaluate_output_keywords(case, gdd_text)

        case_passed = traj_eval.test_pass and out_eval.test_pass
        overall_status = "[PASS]" if case_passed else "[FAIL]"

        print(f"  Resultados del caso '{case.name}': {overall_status}")
        print(f"    |- 1. Trayectoria: {'[PASS]' if traj_eval.test_pass else '[FAIL]'} - {traj_eval.reason}")
        print(f"    +- 2. Output:      {'[PASS]' if out_eval.test_pass else '[FAIL]'} - {out_eval.reason}\n")

        results.append((case.name, case_passed))

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"=== Resultado Global: {passed}/{total} casos totalmente aprobados ===")
    return results


if __name__ == "__main__":
    main()
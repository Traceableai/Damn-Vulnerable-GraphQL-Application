from typing import Dict, List, Set
from graphql import parse
from graphql.error import GraphQLError, GraphQLSyntaxError
from graphql.language.ast import FragmentDefinition, FragmentSpread

def detect_circular_fragments(query_str: str) -> None:
    if not query_str or not isinstance(query_str, str):
        return

    try:
        ast = parse(query_str)
    except GraphQLSyntaxError:
        raise
    except Exception:
        return

    fragment_dependencies = _build_fragment_dependencies(ast)
    if not fragment_dependencies:
        return

    visited: Set[str] = set()

    for fragment_name in fragment_dependencies:
        if fragment_name not in visited:
            stack: Set[str] = set()
            _detect_cycle_dfs(fragment_name, fragment_dependencies, visited, stack)


def _build_fragment_dependencies(ast) -> Dict[str, List[str]]:
    """
    Builds a mapping of fragment -> list of fragment spreads it depends on (recursively).
    """

    def collect_spreads(selection_set) -> List[str]:
        spreads = []
        if not selection_set:
            return spreads
        for sel in selection_set.selections:
            if isinstance(sel, FragmentSpread):
                spreads.append(sel.name.value)
            elif hasattr(sel, "selection_set"):  # Field or InlineFragment
                spreads.extend(collect_spreads(sel.selection_set))
        return spreads

    frag_deps: Dict[str, List[str]] = {}
    for definition in ast.definitions:
        if isinstance(definition, FragmentDefinition):
            name = definition.name.value
            spreads = collect_spreads(definition.selection_set)
            frag_deps[name] = spreads
    return frag_deps


def _detect_cycle_dfs(
    fragment: str,
    dependencies: Dict[str, List[str]],
    visited: Set[str],
    stack: Set[str],
) -> None:
    if fragment in stack:
        cycle_path = " -> ".join(list(stack) + [fragment])
        raise GraphQLError(f"Circular fragment dependency detected: {cycle_path}")

    if fragment in visited:
        return

    stack.add(fragment)
    for dep in dependencies.get(fragment, []):
        _detect_cycle_dfs(dep, dependencies, visited, stack)
    stack.remove(fragment)

    visited.add(fragment)  # Mark visited after recursion

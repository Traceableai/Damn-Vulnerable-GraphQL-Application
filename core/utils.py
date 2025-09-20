from typing import Dict, List, Set, Optional
from graphql import parse, GraphQLError, GraphQLSyntaxError
from graphql.language.ast import FragmentDefinition, FragmentSpread, DocumentNode


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
    
    # Check each fragment for circular dependencies
    visited: Set[str] = set()
    
    for fragment_name in fragment_dependencies:
        if fragment_name not in visited:
            stack: Set[str] = set()
            _detect_cycle_dfs(fragment_name, fragment_dependencies, visited, stack)

def _build_fragment_dependencies(ast: DocumentNode) -> Dict[str, List[str]]:
    frag_deps = {}
    
    for definition in ast.definitions:
        if isinstance(definition, FragmentDefinition):
            name = definition.name.value
            spreads = [
                sel.name.value
                for sel in definition.selection_set.selections
                if isinstance(sel, FragmentSpread)
            ]
            frag_deps[name] = spreads
    
    return frag_deps

def _detect_cycle_dfs(
    fragment: str, 
    dependencies: Dict[str, List[str]], 
    visited: Set[str], 
    stack: Set[str]
) -> None:
    if fragment in stack:
        raise GraphQLError(f"Circular fragment dependency detected: {fragment}")
    
    if fragment in visited:
        return
    
    visited.add(fragment)
    stack.add(fragment)
    
    for dependency in dependencies.get(fragment, []):
        _detect_cycle_dfs(dependency, dependencies, visited, stack)
    
    stack.remove(fragment)



from typing import List, Optional, Tuple, Dict, Set
import os
import glob
import yaml

#We store a configuration(aka stand's template) of installations in *.yaml files
#To share common parts of a configuration across several installations
#we have implemented inclusion in yaml files,
#Example:
# stand1.yaml:
# includes:
#   - shared/common.yaml
#   - ru/specific.yml
# ... other stuff
# Every yaml file in the top-level directory describes an installation(aka stand)



def get_stands_for_changed_templates(changed_paths: Set[str], templates_repo_source: str):
    """
    Finds stands affected in Pull request
    :param Set[str] changed_paths: Relative files changed in Pull request
    :param str templates_repo_source: Local path to cloned repository
    :return: the set of affected installations
    """
    changed_paths = {os.path.join(templates_repo_source, d) for d in changed_paths}
    forward_inclusion_graph = _get_forward_graph(templates_repo_source)
    reverse_inclusion_graph = _reverse_graph(forward_inclusion_graph)
    affected_files = _get_reachable_vertices(changed_paths, reverse_inclusion_graph)
    stands = _get_stands(templates_repo_source)
    result = stands.intersection(affected_files)
    return result

graph = Dict[str, Set[str]]

def _get_forward_graph(templates_repo_source: str) -> graph:
    files = _get_templates_paths(templates_repo_source)
    forward_graph = {}
    for f in files:
        forward_graph[f] = set()
        includes = _get_includes_in_file(f)
        for i in includes:
            if i not in files:
                raise Error("{} includes {} that does not exist".format(f, i))
            forward_graph[f].add(i)
    _check_for_cycles(forward_graph)
    return forward_graph

def _reverse_graph(g: graph) -> graph:
    result = {}
    for v, es in g.items():
        if v not in result:
            result[v] = set()
        for e in es:
            if e not in result:
                result[e] = set()
            result[e].add(v)
    return result

def _check_for_cycles(g: graph):
    state = {v: 0 for v in g}

    def dfs(v):
        if state[v] == 1:
            raise Error("There is a cycle with {}".format(v))
        state[v] = 1
        for e in g[v]:
            dfs(e)  # assume that our template graph doesn't have long paths, so we can use recursion
        state[v] = 2
    for v in g:
        if state[v] == 0:
            dfs(v)

def _get_reachable_vertices(starts: Set[str], g: graph) -> Set[str]:
    result = set()
    queue = set()
    for start in starts:
        queue.add(start)
        while queue:
            cur = queue.pop()
            if cur in result:
                continue
            result.add(cur)
            if cur in g:
                queue.update(g[cur])
    return result

def _get_templates_paths(templates_repo_source: str) -> Set[str]:
    result = set()
    for root, _, files in os.walk(templates_repo_source):
        for name in files:
            if not name.endswith(".yaml"):
                continue
            file_full_name = os.path.join(root, name)
            result.add(file_full_name)
    return result


def _get_includes_in_file(path_to_file: str) -> Set[str]:
    if not os.path.exists(path_to_file):
        raise Exception("File {}, included in templates, doesn't exist".format(path_to_file))
    dir_name = os.path.dirname(path_to_file)
    with open(path_to_file) as f:
        file_yaml = yaml.safe_load(f)
        return {os.path.abspath(os.path.join(dir_name, x)) for x in file_yaml.get("include", {})}

def _get_stands(templates_repo_source: str) -> Set[str]:
    return set(glob.glob(os.path.join(templates_repo_source, "*.yaml")))
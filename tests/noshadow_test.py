"""No two functions in a module may share a name.

The second definition silently replaces the first, and every route still
pointing at the name starts serving the wrong thing - which is exactly how
/backup.json quietly began handing back a database file instead of the
re-importable export the Import page asks for.
"""
import ast
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

for name in sorted(f for f in os.listdir(ROOT) if f.endswith(".py")):
    tree = ast.parse(open(os.path.join(ROOT, name)).read())
    seen = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            assert node.name not in seen, (
                "%s defines %s twice, at lines %d and %d"
                % (name, node.name, seen[node.name], node.lineno))
            seen[node.name] = node.lineno

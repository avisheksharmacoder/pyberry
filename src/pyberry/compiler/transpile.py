import ast
import os
from pyberry.compiler.mapper import TYPE_MAPPING
from pyberry.compiler.transformer import PyberryTransformer

def transpile_file(input_path: str, output_path: str):
    with open(input_path, 'r', encoding='utf-8') as f:
        source = f.read()

    tree = ast.parse(source)
    transformer = PyberryTransformer(TYPE_MAPPING)
    transformed_tree = transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    
    # Ensure import cython exists
    has_cython = any(
        isinstance(node, ast.Import) and any(alias.name == 'cython' for alias in node.names)
        for node in transformed_tree.body
    )
    if not has_cython:
        transformed_tree.body.insert(0, ast.Import(names=[ast.alias(name='cython', asname=None)]))
        
    # Inject from pyberry.core.future import FastFuture
    transformed_tree.body.insert(1, ast.ImportFrom(module='pyberry.core.future', names=[ast.alias(name='FastFuture', asname=None)], level=0))
        
    compiled_source = ast.unparse(transformed_tree)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# cython: language_level=3\n")
        f.write(compiled_source)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python -m pyberry.compiler.transpile <input_file> <output_file>")
        sys.exit(1)
    transpile_file(sys.argv[1], sys.argv[2])
    print(f"Transpiled {sys.argv[1]} -> {sys.argv[2]}")

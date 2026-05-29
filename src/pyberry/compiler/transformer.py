import ast

class PyberryTransformer(ast.NodeTransformer):
    def __init__(self, type_mapping):
        self.type_mapping = type_mapping

    def _is_dataclass(self, node):
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name) and dec.id == 'dataclass':
                return True
            if isinstance(dec, ast.Attribute) and dec.attr == 'dataclass':
                return True
        return False

    def visit_ClassDef(self, node):
        if self._is_dataclass(node):
            # Add @cython.cclass (keep dataclass so __init__ is generated)
            node.decorator_list.append(
                ast.Attribute(value=ast.Name(id='cython', ctx=ast.Load()), attr='cclass', ctx=ast.Load())
            )
            
            # Map annotations
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.annotation, ast.Name):
                    mapped = self.type_mapping.get(stmt.annotation.id)
                    if mapped and mapped.startswith("cython."):
                        stmt.annotation = ast.Attribute(
                            value=ast.Name(id='cython', ctx=ast.Load()),
                            attr=mapped.split('.')[1],
                            ctx=ast.Load()
                        )
                        
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node):
        self.generic_visit(node)
        return node

    def visit_Await(self, node):
        node = self.generic_visit(node)
        # Wrap the awaited object in FastFuture
        wrapper = ast.Call(
            func=ast.Name(id='FastFuture', ctx=ast.Load()),
            args=[node.value],
            keywords=[]
        )
        node.value = wrapper
        return node

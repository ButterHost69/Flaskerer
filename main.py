# from collections.abc import AsyncIterator
from typing import AsyncIterator
import os
import json

from typing import AsyncIterator
from langchain_core.documents import Document
from langchain_core.document_loaders import BaseLoader

verbose = True

class PythonDocumentLoader(BaseLoader):
    def __init__(self, file_path:str):
        self.file_path = file_path

    def alazy_load(self) -> AsyncIterator[Document]:
        import aiofiles
        import ast

        with open(self.file_path, 'r') as file:
            file_contents = file.read()
        tree = ast.parse(file_contents)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if verbose : print(f"Function Name: {node.name}")
                args_list = {}
                # Extract and Format all the parameter
                for arg in node.args.args:
                    param_name = arg.arg
                    if verbose : print(f"\tArguments: {param_name}")
                    if isinstance(arg.annotation, ast.Attribute):
                        # Is an Attribute from a class
                        param_classname = arg.annotation.value.id
                        param_variable = arg.annotation.attr
                        if verbose : print(f"\t\tClass: {param_classname}")
                        if verbose : print(f"\t\tVariable: {param_variable}")
                        argument = f"{param_classname}.{param_variable}"

                    elif isinstance(arg.annotation, ast.Subscript):
                        # Is a List, Tuple or a Map
                        param_type = arg.annotation.value.id
                        param_valuetype = arg.annotation.slice.id
                        if verbose : print(f"\t\tId: {param_type}")
                        if verbose : print(f"\t\tValue: {param_valuetype}")
                        argument = f"{param_type}[{param_valuetype}]"
                        
                    elif isinstance(arg.annotation, ast.Name):
                        # Single Value Primitive Data Type
                        if verbose : print(f"\t\tId: {arg.annotation.id}")
                        argument = arg.annotation.id
                    args_list[param_name] = argument

                # TODO: Add Decorator Support
                meta_data = {
                    "type":"function",
                    "name":node.name,
                    "params": args_list,
                    "returns": "" if node.returns == None else node.returns.id
                }
                if verbose : print("metadata = \n", json.dumps(meta_data, indent=4), "\n\n")
                # yield Document(
                #     page_content= node.body,
                #     meta_data = meta_data
                # )
                # if verbose : print("metadata = \n", meta_data, "\n\n")
            
            # elif isinstance(node, ast.ClassDef):

def main():
    loader = PythonDocumentLoader("./input/prac7-main.py")
    loader.alazy_load()

if __name__ == "__main__":
    main()

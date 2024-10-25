# from collections.abc import AsyncIterator
from typing import AsyncIterator
import os
import json
import aiofiles
import ast

from typing import AsyncIterator
from langchain_core.documents import Document
from langchain_core.document_loaders import BaseLoader

verbose = True

class PythonDocumentLoader(BaseLoader):
    def __init__(self, file_path:str):
        self.file_path = file_path

    def __get_meta_data_from_functions__(self, node) -> dict[str, any]:
        """Get all the Metadata About a Function
        
        Note : This provides many Values, use values that are needed for your purpose

        Avoid Passing all the Values provided by it

        Also Returns Class values like self variables used ..., Function Body etc

        Keyword arguments:
        argument -- ast.Node
        Return: dict[str, any]
        """
        
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
            else:
                if verbose : print(f"\t\tElse Id: {arg.annotation}")
                argument = "any"
            args_list[param_name] = argument
        
        # if verbose : print(f"\tBody: {node.body}")
        declared_variables = set()
        if verbose : print(f"\tList of Variables: ")
        for body_node in node.body:
            if isinstance(body_node, (ast.Assign)):
                targets = body_node.targets
                if isinstance(body_node, ast.Assign):
                    # if verbose : print(f"\t\tVariable: {targets}")
                    for var in targets:    
                        if isinstance(var, ast.Name):
                            declared_variables.add(var.id)
                        if isinstance(var, ast.Attribute):
                            declared_variables.add(f"{var.value.id}.{var.attr}")
        if verbose : print(f"\t\tList of Variable: {declared_variables}")
        

        # TODO: Add Decorator Support
        # TODO: Genearate Doc_String if None Provided Using LLM
        meta_data = {
            "type":"function",
            "name":node.name,
            "params": args_list,
            "returns": "" if node.returns == None else node.returns.id,
            "doc_string" : "" if ast.get_docstring(node) == None else ast.get_docstring(node),
            "declared_variables" : declared_variables
        }
        return meta_data
    
    def __get_meta_data_from_class__(self, node):
        """Get all the Metadata About a Class
        
        Note : This provides many Values, use values that are needed for your purpose

        Avoid Passing all the Values provided by it


        Keyword arguments:
        argument -- ast.Node
        Return: dict[str, any]
        """
        
        class_name = node.name
        class_bases = node.bases
        class_decorators = node.decorator_list
        class_instance_variable  = set()
        class_instance_methods = {}
        if verbose : print("Class Name: ", class_name)
        for node in node.body :
            if isinstance(node, ast.FunctionDef):
                function_metadata = self.__get_meta_data_from_functions__(node)
                class_instance_methods[function_metadata["name"]] = {
                    "params":function_metadata["params"],
                    "returns":function_metadata["returns"]
                    }
                declared_vars = function_metadata["declared_variables"]
                for var in declared_vars:
                    if 'self.' in var:
                        class_instance_variable.add(var)
        if verbose : print("\tInstance Variables : ", class_instance_variable)
        
        # TODO: Genearate Doc_String if None Provided Using LLM
        return {
            "type":"class",
            "name":class_name,
            "class_bases":class_bases,
            "class_decorators":class_decorators,
            "instance_variables":list(class_instance_variable),
            "instance_methods":class_instance_methods
        }



    def alazy_load(self) -> AsyncIterator[Document]:
        with open(self.file_path, 'r') as file:
            file_contents = file.read()
        tree = ast.parse(file_contents)
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                ret_meta_data = self.__get_meta_data_from_functions__(node)
                meta_data = {
                    "type":"function",
                    "name":ret_meta_data["name"],
                    "params": ret_meta_data["params"],
                    "returns": ret_meta_data["returns"],
                    "doc_string" : ret_meta_data["doc_string"],
                }
                if verbose : print("metadata = \n", json.dumps(meta_data, indent=4), "\n\n")
                # yield Document(
                #     page_content= node.body,
                #     meta_data = meta_data
                # )
                # if verbose : print("metadata = \n", meta_data, "\n\n")
            
            elif isinstance(node, ast.ClassDef):
                meta_data = self.__get_meta_data_from_class__(node)
                if verbose : print("metadata = \n", json.dumps(meta_data, indent=4), "\n\n")
                # yield Document(
                #     page_content= node.body,
                #     meta_data = meta_data
                # )

def main():
    # loader = PythonDocumentLoader("./input/prac7-main.py")
    loader = PythonDocumentLoader("./input/classinput.py")
    loader.alazy_load()

if __name__ == "__main__":
    main()

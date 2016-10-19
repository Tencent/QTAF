# -*- coding: utf-8 -*-
'''
目的：生成模块的 .pypredef文件，代码帮助提示
'''

#2015/03/19 eeelin 支持全局对象的代码提示

import ast
import re
import os

def _warnning( s ):
    print 'warnning: ' + s
    
class PyPreDefGenerator(object):
    '''pypredef文件生成器
    '''
    INDENT = ' '*4
    SOURCE_ENCODING = 'utf8'
    
    def generate(self, source_file, output_file, encoding='gbk'):
        '''生成pypredef
        :param source_file: 代码文件
        :type source_file: str
        :param output_file: 生成文件
        :type output_file: str
        '''
        with open(source_file,'r') as fd:
            py_source = fd.read()
        pyast = ast.parse(py_source)
        enc = lambda x: x.decode(self.SOURCE_ENCODING, 'ignore').encode(encoding, 'ignore')
        with open(output_file, 'w') as fd:
            fd.write(enc(self._get_docstring(pyast,0)))
            for stmt in pyast.body:
                if isinstance(stmt, ast.Import):
                    fd.write(enc(self._get_import(stmt, 0)))
                elif isinstance(stmt, ast.ImportFrom):
                    fd.write(enc(self._get_import_from(stmt, 0)))
                elif isinstance(stmt, ast.ClassDef):
                    fd.write(enc(self._get_classdef(stmt, 0)))
                elif isinstance(stmt, ast.FunctionDef):
                    fd.write(enc(self._get_funcdef(stmt, 0)))
                elif isinstance(stmt, ast.Assign):
                    fd.write(enc(self._get_vardef(stmt, 0)))
              
    def _get_base_class_name(self, node):
        '''获取父类信息
        
        :param node: AST类节点
        :type node: AST node
        :returns: 父类信息
        :rtype: string
        '''
        if isinstance(node, ast.Attribute):        
            return '%s.%s' % (self._get_base_class_name(node.value), node.attr)
        elif isinstance(node, ast.Name):
            return node.id
        else:
            _warnning('_get_base_class_name got unexpected node: %s' % node)
            
            
    def _get_classdef(self, class_node, depth):
        '''获取类定义
        
        :param class_node: AST类节点
        :type class_node: AST node
        :param depth: 控制缩进深度
        :type depth: int
        '''
        class_def = "%sclass %s(%s):\n" % ( self.INDENT * depth,
                                            class_node.name,
                                            ', '.join([ self._get_base_class_name(it) for it in class_node.bases]))
        
        
   
        class_def += self._get_docstring(class_node, depth+1)
        
        for element_node in class_node.body:
            if isinstance(element_node, ast.ClassDef):
                class_def += self._get_classdef(element_node, depth+1)
            elif isinstance(element_node, ast.FunctionDef):
                class_def += self._get_funcdef(element_node, depth+1)
            elif isinstance(element_node, ast.Assign):
                class_def += self._get_vardef(element_node, depth+1)
                
        return class_def
        
    def _get_func_arg(self, node):
        '''获取函数参数
        
        :param node: AST类节点
        :type node: AST node
        :returns: 函数参数信息
        :rtype: string
        '''
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Tuple):
            return '(%s)'%(', '.join([self._get_func_arg(it) for it in node.elts ]))
        else:
            _warnning('_get_base_class_name got unexpected node: %s' % node)
            
    def _get_funcdef(self, func_node, depth):
        '''获取函数
        
        :param class_node: AST类节点
        :type class_node: AST node
        :param depth: 控制缩进深度
        :type depth: int
        '''
        func_def = ""
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Name):
                func_def += '%s@%s\n'%(self.INDENT*depth, decorator.id)
            else:
                _warnning('_get_funcdef got unexpected decorator node: %s' % decorator)
                
        
        arg_strs = [self._get_func_arg(arg) for arg in func_node.args.args]
        
        if func_node.args.vararg:
            arg_strs.append("*"+str(func_node.args.vararg))
        if func_node.args.kwarg:
            arg_strs.append("**"+str(func_node.args.kwarg))
        func_def += '%sdef %s(%s):\n' % ( self.INDENT*depth,
                                          func_node.name,
                                          ', '.join(arg_strs))
        
        func_def += self._get_docstring(func_node, depth+1)
        func_def += '\n\n'
        return func_def
        
    def _get_vardef(self, assign_stmt, depth ):
        '''获取变量赋值
        
        :param assign_stmt: Assign节点
        :type assign_stmt: Assign
        :param depth: 控制缩进深度
        :type depth: int
        :returns string: assign string
        '''
        target = assign_stmt.targets[0]        
        if isinstance(target, ast.Name):
            return "%s%s = %s\n" % ( self.INDENT*depth,
                                     target.id,
                                     self._get_call_return_type(assign_stmt.value))
            
        elif isinstance(target, ast.Tuple):
            return "%s%s = %s\n" % (self.INDENT*depth,
                                    ', '.join([ it.id for it in target.elts]),
                                    self._get_call_return_type(assign_stmt.value))
        
        elif isinstance(target, ast.Attribute) or isinstance(target, ast.Subscript):
            return ''
        else:
            _warnning('_get_vardef got unexpected node: %s' % target)
            return ''
            
    def _get_call_return_type(self, node ):
        '''获取调用的返回值
        '''
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
        elif isinstance(node, ast.Tuple):
            return ', '.join([ self._get_call_return_type(it) for it in node.elts])
        return type(node).__name__
        
    def _get_import(self, import_stmt, depth ):
        '''获取import
        
        :param import_stmt: Import节点
        :type import_stmt: Import
        :param depth: 控制缩进深度
        :type depth: int
        :returns string: import_string
        '''
        return "%simport %s\n" % (self.INDENT*depth, 
                                  ', '.join([ name.name for name in import_stmt.names]))
        
    def _get_import_from(self, import_stmt, depth ):
        '''获取from xx import xx
        
        :param import_stmt: ImportFrom节点
        :type import_stmt: ImportFrom节点
        :param depth: 控制缩进深度
        :type depth: int
        :returns string: import_string
        '''
        return "%sfrom %s import %s\n" % (self.INDENT*depth, 
                                          import_stmt.module,
                                          ', '.join([ name.name for name in import_stmt.names]))
                                  
                                  
    def _get_docstring(self, node, depth):
        '''获取docstring
        
        :param node: AST类节点
        :type node: AST node
        :param depth: 控制缩进深度
        :type depth: int
        :returns: docstring
        :rtype: string
        '''
        if len(node.body) == 0:
            return ""
            
        first_stmt = node.body[0]
        if isinstance(first_stmt, ast.Expr):
            if isinstance(first_stmt.value, ast.Str):
                return "%s'''%s'''\n" % (self.INDENT*depth, first_stmt.value.s )
            
        if isinstance(node, ast.Module):
            return ""
        else:
            return "%s'''%s\n%s'''\n" % (self.INDENT*depth, node.name,self.INDENT*depth)
        
    def change_encoding(self):
        pass
        
        
def build( source_path, output_path, packages, blacklist, output_encoding='gbk' ):
    '''在指定目录下生成pypredef文件
    
    :param source_path: py源码所在根目录
    :type source_path: string
    :param output_path: 生成文件存放文件夹
    :type output_path: string
    :param packages: 需要生成pypredef包列表
    :type packages: list
    :param blacklist: 不需要生成pypredef模块名匹配正则
    :type blacklist: list
    '''
    pattern = re.compile('|'.join(['(%s)'%it for it in blacklist]))
    gen_files = []
    generator = PyPreDefGenerator()
    for pkgname in os.listdir(source_path):
        if pkgname not in packages:
            continue
        pkgdir = os.path.join(source_path, pkgname)
        for root, dirs, files in os.walk(pkgdir):
            for filename in files:
                if not filename.endswith('.py'):
                    continue
                filepath = os.path.join(root, filename)
                modulename = os.path.relpath(filepath, source_path)[0:-3].replace(os.path.sep, '.')
                if pattern.match(modulename):
                    continue
                outfile = os.path.join(output_path, '%s.pypredef'%modulename )
                print 'generating %s' % outfile
                generator.generate(filepath, outfile, output_encoding)
                gen_files.append(outfile)
    
    return gen_files
    

if __name__ == '__main__':

    import os
    qtaf_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
    target_path = os.path.join(qtaf_dir, 'pypredef')

    build(qtaf_dir, target_path, ["pyqq"], ["pyqq.protocol", "pyqq.mqlib"])
    

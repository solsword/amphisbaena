#!/usr/bin/env python3
"""
eat.py
Loads a Python file and creates statistics on what kind of AST nodes are used
by each top-level function.
"""

import ast
import sys
import os

# List of information gathered for each function:
COLUMNS = [
  "name",
  'conditionals',
  'loops',
  'comprehensions',
  'assignments',
  'returns',
  'calls',
  'recursive_calls',
]

def get_ast(filename):
  """
  Parses the contents of the given file and returns an AST object.
  """
  with open(filename, 'r') as fin:
    return ast.parse(fin.read(), filename=filename, mode='exec')

def get_stats(node):
  """
  Given an AST object (normally representing a module), build and return a list
  of dictionaries containing stats about each function in the module. Each
  dictionary has the following keys:

    'name': The name of the function.
    'conditionals': The number of conditional statements in the function
      (including else-ifs).
    'loops': The total number of for- and while- loops in the function.
    'comprehensions': The number of list/set/dictionary-comprehensions.
    'assignments': The number of assignment statements.
    'returns': The number of return statements.
    'calls': The number of function calls in the function.
    'recursive_calls': The number of recursive calls in the function (mutual
      recursion is not detected, and recursive calls where the function
      involved is the result of an expression are not detected either).
    'called_functions': A set of the names of each called function (only counts
      functions called directly by name; doesn't count methods).
    'called_methods': A set of the names of each called method.
    'resolved_attributes': A set of the names of each resolved attribute.

  If the given AST node does not have a body, an empty list will be returned.
  """
  results = []
  if not hasattr(node, "body"):
    return results

  for child in node.body:
    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
      results.append(collect_stats(child))

  return results

def collect_stats(node):
  """
  Gathers statistics for a single function definition node. See the
  documentation for get_status.
  """
  # Create empty result:
  result = {
    x: 0 for x in COLUMNS
  }
  result['name'] = node.name
  result['called_functions'] = set()
  result['called_methods'] = set()
  result['resolved_attributes'] = set()

  # Count various kinds of nodes:
  for child in ast.walk(node):
    if isinstance(child, ast.Call):
      result['calls'] += 1
      if isinstance(child.func, ast.Name):
        if child.func.id == node.name:
          result['recursive_calls'] += 1
        result['called_functions'].add(child.func.id)
      elif isinstance(child.func, ast.Attribute):
        result['called_methods'].add(child.func.attr)
    elif isinstance(child, ast.Attribute):
      result['resolved_attributes'].add(child.attr)
    elif isinstance(child, ast.Return):
      result['returns'] += 1
    elif isinstance(child, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
      result['assignments'] += 1
    elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp)):
      result['comprehensions'] += 1
    elif isinstance(child, (ast.For, ast.AsyncFor, ast.While)):
      result['loops'] += 1
    elif isinstance(child, (ast.If, ast.IfExp)):
      result['conditionals'] += 1

  return result

if __name__ == "__main__":
  targets = ["eat.py"]
  mode = "show"
  if '--stats' in sys.argv:
    sys.argv.remove('--stats')
    mode = "stats"
  if '--show' in sys.argv:
    sys.argv.remove('--show')
    mode = "show"
  if '--list-calls' in sys.argv:
    sys.argv.remove('--list-calls')
    mode = "list-calls"
  if '--list-attrs' in sys.argv:
    sys.argv.remove('--list-attrs')
    mode = "list-attrs"
  if len(sys.argv) > 1:
    targets = sys.argv[1:]

  combined = set()
  for target in targets:
    tree = get_ast(target)
    stats = get_stats(tree)
    if mode == "stats":
      out = target + ".csv"
      if len(stats) == 0:
        print("Warning: No functions found in file '{}'.".format(target))
      else:
        if os.path.exists(out):
          print("Error: file '{}' already exists. Aborting.".format(out))
          exit(1)
        with open(out, 'w') as fout:
          fout.write(','.join(COLUMNS) + '\n')
          for fs in stats:
            vals = [str(fs[c]) for c in COLUMNS]
            fout.write(','.join(vals) + '\n')
    elif mode == "show":
      if len(stats) == 0:
        print("Warning: No functions found in file '{}'.".format(target))
      else:
        print("File '{}':".format(target))
        for fs in stats:
          print("  In function '{}':".format(fs['name']))
          print("    Calls:")
          for fc in fs['called_functions']:
            print("      " + fc)
          print("    Method calls:")
          for mc in fs['called_methods']:
            print("      " + mc)
          print("    Attributes resolved:")
          for at in fs['resolved_attributes']:
            print("      " + at)
    elif mode == "list-calls":
      for fs in stats:
        for fc in fs['called_functions']:
          combined.add(fc)
        for mc in fs['called_methods']:
          combined.add('.' + mc)
    elif mode == "list-attrs":
      for fs in stats:
        for at in fs['resolved_attributes']:
          combined.add(at)
  if mode in ("list-calls", "list-attrs"):
    for name in sorted(combined):
      print(name)

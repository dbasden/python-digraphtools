#! /usr/bin/env python

'''a collection of tools for working with directed acyclic graphs

A graph is represented as a dict which maps a node to a list
nodes connected via the outgoing edges of that node. 

e.g.

	graph = { 1: [2,3],
		  2: [3],
		  3: [] }

is a DAG represented by the edges  (1,2) (1,3) (2,3)
where the edge 2tuple is in the form of (from,to)

Note: If a DAG represents dependencies, e.g. the edge (1,2) is taken
      to mean "1 depends on 2", this is backwards from a binary relation.
      (1,2) would be the relation 2P1
'''
from collections import defaultdict,deque

def graph_from_edges(edges):
	'''return a graph from a set of edges
	edges are a 2tuple in the form of (from_node, to_node)
	'''
	graph = defaultdict(set)
	for a,b in edges:
		graph[a].add(b)
		graph[b]
	return dict((a,list(b)) for a,b in graph.items())

def copy_graph(graph):
	'''return a copy of a graph'''
	return dict((a,list(b)) for a,b in graph.items())

def iter_edges(graph):
	'''return an iterator over every edge in a graph in the form (from,to)'''
	return ((a,b) for a in graph.iterkeys() for b in graph[a])

def iter_partial_order(graph):
	return ((a,b) for b,a in iter_edges(graph))

def from_partial_order(edges): return [(a,b) for (b,a) in edges]
to_partial_order = from_partial_order

class OrderViolationException(Exception): pass

def verify_partial_order(partial_order, items):
	'''verify that the order of items supplied satisfies the dependency graph
	raises OrderViolationException unless a<b for every aPb in the partial order
	(i.e. if a task is inserted before any of it's dependencies)
	'''
	itempos = dict((item,pos) for pos,item in enumerate(items))
	for a,b in partial_order:
		if itempos[a] >= itempos[b]:
			raise OrderViolationException("item '%s' is in the order before it's dependency '%s'" %( repr(b),repr(a)),items)

def postorder_traversal(graph, root):
	'''traverse a graph post-order and yield a list of nodes'''
	for n in graph[root]:
		for traversed in postorder_traversal(graph,n):
			yield traversed
	yield root

def dfs_topsort_traversal(graph, root):
	'''traverse a graph postorder while not traversing already seen nodes'''
	seen = set()
	for n in postorder_traversal(graph, root):
		if n not in seen:
			yield n
			seen.add(n)

def dfs_traverse_iter_path(graph, root, path=None):
	'''depth first traversal of graph generating every path seen'''
	if path == None: path = []
	if root in path: return
	path.append(root)
	yield path
	for n in graph[root]:
		for traversed in dfs_traverse_iter_path(graph, n, path):
			yield traversed
	path.pop()
	
def dfs_iter_edges(graph, root):
	'''traverse a graph depth-first and yield edges as they are traversed'''
	for n in graph[root]:
		yield root,n
		for edge in dfs_iter_edges(graph,n):
			yield edge

def get_connected_subgraph(graph, root):
	'''return the connected subgraph visible from supplied root node'''
	return graph_from_edges( dfs_iter_edges(graph,root) )

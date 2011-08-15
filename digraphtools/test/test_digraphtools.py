#! /usr/bin/env python

'''unit tests for digraphtools'''

import unittest2 as unittest
import digraphtools

class DigraphTests(unittest.TestCase):
	def test_graph_from_edges(self):
		g = digraphtools.graph_from_edges([(1,2),(1,3),(2,3)])
		self.assertEqual(set(g[1]),set([2,3]))
		self.assertEqual(set(g[2]),set([3]))
		self.assertEqual(set(g[3]),set())
	def test_verify_partial_order(self):
		g = digraphtools.graph_from_edges([(1,2),(1,3),(2,3)])
		# Will raise an exception if incorrect
		digraphtools.verify_partial_order(digraphtools.iter_partial_order(g), [3,2,1])
		self.assertRaises(digraphtools.OrderViolationException,digraphtools.verify_partial_order, digraphtools.iter_partial_order(g), [3,1,2])
	def test_iter_edges(self):
		edges = set([(1,2),(1,3),(2,3)])
		g = digraphtools.graph_from_edges(edges)
		gedges = set(digraphtools.iter_edges(g))
		self.assertEqual(edges,gedges)
	def test_copy_graph(self):
		edges = set([(1,2),(1,3),(2,3)])
		g = digraphtools.graph_from_edges(edges)
		gg = digraphtools.copy_graph(g)
		self.assertEqual(g,gg)
		gedges = set(digraphtools.iter_edges(g))
		ggedges = set(digraphtools.iter_edges(gg))
		self.assertEqual(gedges,ggedges)
		gg[2].remove(3)
		self.assertNotEqual(g,gg)
		gedges = set(digraphtools.iter_edges(g))
		ggedges = set(digraphtools.iter_edges(gg))
		self.assertNotEqual(gedges,ggedges)
	def test_postorder_traversal(self):
		edges = set([(1,2),(1,3),(2,3)])
		g = digraphtools.graph_from_edges(edges)
		po = list(digraphtools.postorder_traversal(g,1))
		self.assertEqual([3,2,3,1],po)
	def test_dfs_topsort_traversal(self):
		edges = set([(1,2),(1,3),(2,3)])
		g = digraphtools.graph_from_edges(edges)
		po = list(digraphtools.dfs_topsort_traversal(g,1))
		self.assertEqual([3,2,1],po)
	def test_dfs_iter_edges(self):
		g = digraphtools.graph_from_edges([(1,2),(1,3),(2,3)])
		edgeiter = digraphtools.dfs_iter_edges(g,1)
		self.assertEqual([(1,2),(2,3),(1,3)],list(edgeiter))
	def test_get_connected_subgraph(self):
		g = digraphtools.graph_from_edges([(1,2),(1,3),(2,3)])
		self.assertEqual(g, digraphtools.get_connected_subgraph(g,1))
		sg = digraphtools.graph_from_edges([(2,3)])
		self.assertEqual(sg, digraphtools.get_connected_subgraph(g,2))

if __name__ == '__main__':
	unittest.main()

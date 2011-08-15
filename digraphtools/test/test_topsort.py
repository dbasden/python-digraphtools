#! /usr/bin/env python

'''unit tests for digraphtools'''

import unittest2 as unittest
import digraphtools
import digraphtools.topsort as topsort

class TopsortTests(unittest.TestCase):
	def test_vr_topsort(self):
	        n = 5
        	partial_order = [(1,2), (2,3), (1,5)]
		g = digraphtools.graph_from_edges(digraphtools.from_partial_order(partial_order))
        	grid = topsort.partial_order_to_grid(partial_order,n)
        	for le in topsort.vr_topsort(n,grid):
			digraphtools.verify_partial_order(digraphtools.iter_partial_order(g), le)

if __name__ == '__main__':
	unittest.main()

#! /usr/bin/env python

'''predicates that can be chained together with boolean expressions before evaluation

e.g.
	a = predicate(lambda s: 'a' in s)
	b = predicate(lambda s: 'b' in s)
	c = predicate(lambda s: 'c' in s)

	anyof = a | b | c
	allof = a & b & c
	not_anyof = anyof != True
	assert anyof('--a--')
	assert allof('-abc-')
	assert not_anyof('12345')

Also, generate predicates such as above from strings

	pf = PredicateContainsFactory()
	anyof2 = pf.predicate_from_string('a | b | c')
	pallof2 = pf.predicate_from_string('a & b & c')
	not_anyof2 = pf.predicate_from_string('!(a & b & c)')
	assert anyof2('--a--')
	assert allof2('-abc-')
	assert not_anyof2('12345')

These can be very useful for filtering of dependency graphs
'''

import operator
import re

def defer(origfunc,*argfs,**argfd):
	'''defer execution of the arguments of a function
	given origfunc return a function such that the code
		f = defer(origfunc, arga, key=argb)
		f(*newargs, **newargd)
	is equivalent to:
		origfunc(arga(*newargs,**newargd), key=argb(*newargs,**newargd))
	'''
	def wrapper(*args, **argd):
		newargs = [argf(*args, **argd) for argf in argfs]
		newargd = dict((k,argf(*args, **argd)) for k,argf in argfd.items())
		return origfunc(*newargs, **newargd)
	wrapper.origfunc = origfunc
	wrapper.argfs = argfs
	wrapper.argfd = argfd
	wrapper.__repr__ = lambda s: "defer <%s>( *(%s) **(%s)) " % (repr(origfunc),repr(argfs),repr(argfd))
	return wrapper

def always(val):
	'''returns a function that always returns val regardless of inputs'''
	def alwaysf(*args, **argd): return val
	alwaysf.val = val
	return alwaysf

class predicate(object):
	'''chainable predicates
	e.g.
		a = predicate(lambda s: 'a' in s)
		b = predicate(lambda s: 'b' in s)
		c = predicate(lambda s: 'c' in s)

		anyof = a | b | c
		allof = a & b & c
		not_anyof = anyof != True
		assert anyof('--a--')
		assert allof('-abc-')
		assert not_anyof('12345')
	'''

	def __init__(self, func):
		self.func = func
	def __call__(self, arg):
		return self.func(arg)
	def __and__(self,other):
		return self.__defer_infix__(other,operator.__and__)
	def __or__(self,other):
		return self.__defer_infix__(other,operator.__or__)
	def __ne__(self,other):
		return self.__defer_infix__(other,operator.__ne__)
	def __defer_infix__(self,other,op):
		if isinstance(other, bool): 
			other = always(other)
		elif not isinstance(other, predicate): 
			return NotImplemented
		return self.__class__(defer(op, self, other))
	def __repr__(self):
		return 'pred( '+repr(self.func)+' )'

class notp(predicate):
	'''exactly the same as a predicate but inverts it's __call__ output'''
	def __call__(self, *args, **argd):
		return not predicate.__call__(self, *args, **argd)



def partition_list(items, partition):
	'''works like str.partition but for lists
	e.g. partition(['aa','bb','cd','ee'],'cd') == ['aa','bb'],'cd',['ee']
	     partition(['aa','bb','cd','ee'],'ff') == ['aa','bb','cd','ee'],None,[]
	'''
	for i,obj in enumerate(items):
		if obj == partition:
			return items[:i],obj,items[i+1:]
	return items,None,[]

class ParseSyntaxError(Exception): pass
class LexParse(object):
	'''very simple lexer/parser'''
	class _leaf(object):
		def __init__(self, data): self.data = data
		def __repr__(self): return '_leaf(%s)' %(repr(self.data))

	valid_tokens = ['(',')','!','&','|']

	def _match_bracket(self, tokens, i, bopen='(',bclose=')'):
		'''find the closing bracket that matches an open bracket
		return None if there is no matching bracket
		otherwise the index into tokens of the close bracket that matches the opening bracket at position i
		'''
		assert i < len(tokens)
		assert tokens[i] == bopen
		depth = 0
		for i in xrange(i,len(tokens)):
			tok = tokens[i]
			if tok == bopen: 
				depth += 1
			elif tok == bclose:
				depth -= 1
				if depth < 0: return None
				if depth == 0: return i
		return None
		
	def lex(self, s):
		'''returns a list of tokens from a string
		tokens returned are anything inside self.valid_tokens or
		any other string not containing tokens, stripped
		of leading and trailing whitespace
		'''
		s = s.strip()
		if s == '': return []
		for tok in self.valid_tokens:
			l,t,r = s.partition(tok)
			if t==tok: return self.lex(l)+[tok]+self.lex(r)
		return [self._leaf(s)]

	def parse(self, tokens):
		'''parse a list of tokens in order of predicence and return the output'''
		if len(tokens) == 0:
			raise ParseSyntaxError('Cannot parse empty subexpression')
		# Brackets
		l,part,r = partition_list(tokens, '(')
		if part != None:
			if ')' in l: raise ParseSyntaxError('unmatched ) near',tokens)
			r.insert(0,'(')
			rindex = self._match_bracket(r, 0)
			if rindex is None: raise ParseSyntaxError('unmatched ( near',tokens)
			assert r[rindex] == ')'
			inner = r[1:rindex]
			r = r[rindex+1:]
			inner = self.brackets(self.parse(inner))
			return self.parse(l+[inner]+r)

		# unary not
		if tokens[0] == '!':
			if len(tokens) < 2: raise ParseSyntaxError('syntax error near',tokens)
			# this only works without other unary operators
			if tokens[1] in self.valid_tokens: raise ParseSyntaxError('syntax error near', tokens)
			argument = self.parse([ tokens[1] ])
			inv = self.notx(argument)
			return self.parse([inv]+tokens[2:])

		# and
		l,part,r = partition_list(tokens, '&')
		if part != None:
			if not len(l) or not len(r):
				raise ParseSyntaxError('syntax error near', tokens)
			l,r = self.parse(l), self.parse(r)
			return self.andx(l,r)

		# or
		l,part,r = partition_list(tokens, '|')
		if part != None:
			if not len(l) or not len(r):
				raise ParseSyntaxError('syntax error near', tokens)
			l,r = self.parse(l), self.parse(r)
			return self.orx(l,r)

		if len(tokens) == 1:
			if isinstance(tokens[0], self._leaf):
				return self.data(tokens[0].data) # base case
			elif tokens[0] in self.valid_tokens:
				raise ParseSyntaxError('syntax error near',tokens)
			return tokens[0] # Already parsed

		# Nothing else is sane
		print repr(tokens)
		raise ParseSyntaxError('syntax error near', tokens)

	def brackets(self, expr): 
		'''You almost never want to override this'''
		return expr 

	def notx(self, expr): pass
	def andx(self, expr_l, expr_r): pass
	def orx(self, expr_l, expr_r): pass
	def data(self, data): pass

class BoolParse(LexParse):
	'''example parser implementation
	bp = BoolParse()
	assert False or (False and not (True or False)) == False
	inp = 'False | (False & ! (True | False))'
	assert bp.parse(bp.lex(inp)) is False
	'''
	notx = lambda s,expr: not expr
	andx = lambda s,l,r: l and r
	orx = lambda s,l,r: l or r
	def data(self,data):
		return not(data.lower() == 'false' or data == '0')


class PredicateContainsFactory(LexParse):
	'''create predicates that act on the contents of a container passed to them'''
	def predicate_from_string(self, definition):
		tokens = self.lex(definition)
		return self.parse(tokens)
	def notx(self, pred):
		return notp(pred)
	def andx(self, pred_l, pred_r):
		return pred_l & pred_r
	def orx(self, pred_l, pred_r):
		return pred_l | pred_r
	def data(self, data):
		return predicate(lambda container: data in container)

if __name__ == "__main__":
	def defer_sample():
		def a(arga, moo=None, argb=None):
			return arga+argb
		def b(arga, moo=None, argb=None):
			return arga^argb
		def c(arga, moo=None, argb=None):
			return arga,argb
		ooer = defer(c, a,argb=b)
		result = ooer(1234,argb=4312)
		assert result == (5546, 5130)

	def predicate_sample():
		a = predicate(lambda s: 'a' in s)
		b = predicate(lambda s: 'b' in s)
		c = predicate(lambda s: 'c' in s)
		d = predicate(lambda s: 'd' in s)

		anyof = a | b | c
		allof = a & b & c

		not_anyof = anyof != True
		not_allof = allof != True


		assert anyof('asdf')
		assert allof('abc')
		assert not anyof('1234')
		assert not allof('ab')
		assert not_anyof('1234')
		assert not_allof('1234')

		nottest = a & b & notp( c | d )
		assert nottest('ab')
		assert not nottest('abc')
		assert not nottest('b')
		assert not nottest('d')
		assert not nottest('bd')
		assert not nottest('abd')

		e = predicate(lambda n: n%2==0)
		t = predicate(lambda n: n%3==0)
		eset = set(filter(e, range(1000)))
		tset = set(filter(t, range(1000)))
		eutset = set(filter(e|t, range(1000)))
		eitset = set(filter(e&t, range(1000)))
		assert eutset == eset.union(tset)
		assert eitset == eset.intersection(tset)

	def parser_internal_test():
		lp = LexParse()
	        #lp._match_bracket(self, tokens, i, bopen='(',bclose=')'):
		assert lp._match_bracket('()',0) == 1
		assert lp._match_bracket('(',0) == None
		assert lp._match_bracket(')))))()))))',5) == 6
		assert lp._match_bracket('((()(()))(()((()(()()))())()))',0) == 29
		assert lp._match_bracket('((()(()))(()((()(()()))())()))',2) == 3 
		assert lp._match_bracket('((()(()))(()((()(()()))())()))',12) == 25
		assert lp._match_bracket('((()(()))(()((()(()()))())()))',23) == 24
		assert lp._match_bracket('((()(()))(()((()(()()))())()))',23) == 24
		assert lp._match_bracket('((()(()))(()((()(()()))())()))',26) == 27
		assert lp._match_bracket('((()(()))(()((()(()()))())()))',9) == 28
		assert lp._match_bracket('((()(()))(()((()(()()))())()))',10) == 11
		assert lp._match_bracket('((()(()))(()((()(()()))())()))',16) == 21

	def parser_sample():
		bp = BoolParse()
		assert False or (False and not (True or False)) == False
		inp = 'False | (False & ! (True | False))'
		assert bp.parse(bp.lex(inp)) is False
		assert bp.parse(bp.lex('true & !false'))

	def predicate_factory_sample():
		pf = PredicateContainsFactory()
		pred = pf.predicate_from_string('fish & !cow')
		assert pred(['fish', 'bat', 'pidgeon'])
		assert not pred( ['fish', 'cow', 'bat'] )
		assert not pred( [] )
		assert not pred( ['cow'] )
		assert not pred( ['bat','pig'] )

		a = predicate(lambda s: 'a' in s)
		b = predicate(lambda s: 'b' in s)
		c = predicate(lambda s: 'c' in s)
		anyof2 = pf.predicate_from_string('a | b | c')
		allof2 = pf.predicate_from_string('a & b & c')
		not_anyof2 = pf.predicate_from_string('!(a & b & c)')
		assert anyof2('--a--')
		assert allof2('-abc-')
		assert not_anyof2('12345')

		pred = pf.predicate_from_string('( a | b | c ) & ( c | e | d )')
		assert not pred('b')
		assert pred('c')
		assert pred('cd')
		assert pred('acd')
		assert not pred('ab')
		assert not pred('a')

	parser_internal_test()
	defer_sample()
	predicate_sample()
	parser_sample()
	predicate_factory_sample()

#! /usr/bin/env python

import operator

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

	defer_sample()
	predicate_sample()

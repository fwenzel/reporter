"""
Reverse Polish Notation template math.

from: http://djangosnippets.org/snippets/1156/
"""
from django import template
register = template.Library()

class stack:
    def __init__(self):
        self.stack = []

    def push(self, o):
        self.stack.append(o)
        #print 'push', self.stack

    def pop(self):
        if len(self.stack) == 0:
            raise KeyError, "Stack is empty"
        o = self.stack[-1]
        #print 'pop', self.stack
        del self.stack[-1]
        return o

    def is_empty(self):
        return len(self.stack) == 0

    def __len__(self):
        return len(self.stack)

# truncate a floating point number only if it has no decimal part (convert from string if necessary)
def number(num):
    f = float(num)
    i = int(f)
    if i == f: #FIXME: floating point equality?
        return i
    return f

stacks = {}

@register.filter
def stnew(value):
    #print 'stnew'
    stacks[value] = stack()
    return value

@register.filter
def stpush(value, arg):
    #print 'stpush:',
    stacks[value].push(number(arg))
    return value

@register.filter
def stpop(value):
    #print 'stpop:',
    if value in stacks:
        stacks[value].pop()
    return value

@register.filter
def stget(value):
    #print 'stget:',
    if value in stacks:
        return stacks[value].pop()

@register.filter
def stadd(value):
    #print 'stadd:',
    two = stacks[value].pop()
    one = stacks[value].pop()
    stacks[value].push(one + two)
    return value

@register.filter
def stsub(value):
    #print 'stsub:',
    two = stacks[value].pop()
    one = stacks[value].pop()
    stacks[value].push(one - two)
    return value

@register.filter
def stmult(value):
    #print 'stmult:',
    two = stacks[value].pop()
    one = stacks[value].pop()
    stacks[value].push(one * two)
    return value

@register.filter
def stdiv(value):
    #print 'stdiv:',
    two = stacks[value].pop()
    one = stacks[value].pop()
    stacks[value].push(number(float(one) / float(two)))
    return value

@register.filter
def stmod(value):
    two = stacks[value].pop()
    one = stacks[value].pop()
    stacks[value].push(one % two)
    return value

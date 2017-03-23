#! /usr/bin/env python3

import sys

"""SPI - Simple Pascal Interpreter"""

################################################################
#                                                              #
#       LEXER                                                  #
#                                                              #
################################################################

# Token types
#
# EOF (end-of-file) token is used to indicate that 
# there is no more input for lexical analysis
INTEGER, PLUS, MINUS, MUL, DIV, LPAREN, RPAREN, EOF = (
    'INTEGER', 'PLUS', 'MINUS', 'MUL', 'DIV', '(', ')', 'EOF'
)

class Token(object):
    def __init__(self, type, value):
        self.type = type
        self.value = value
    
    def __str__(self):
        """String representation of the class instance.

        Examples:
            Token(INTEGER, 3)
            Token(PLUS, '+')
            Token(MUL, '*')
        """
        return 'Token({type}, {value})'.format(
            type = self.type,
            value = repr(self.value)
        )
    
    def __repr__(self):
        return self.__str__()


class Lexer(object):
    def __init__(self, text):
        # client string input, e.g. "4 + 2 * 3 - 6 / 2"
        self.text = text
        # self.pos is an index into self.text
        self.pos = 0
        self.current_char = self.text[self.pos]
    
    def error(self):
        raise Exception('Invalid character')
    
    def advance(self):
        """Advance 'pos' and set 'current_char'"""
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None # indicates end of input
        else:
            self.current_char = self.text[self.pos]
    
    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()
    
    def integer(self):
        """Return a (multidigit) integer consumed from the input"""
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)
    
    def get_next_token(self):
        """Lexical analyser, aka scanner / tokeniser

        This method is responsible for splitting the input apart
        into tokens, one token at a time.
        """
        while self.current_char is not None:

            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            
            if self.current_char.isdigit():
                return Token(INTEGER, self.integer())
            
            if self.current_char == '+':
                self.advance()
                return Token(PLUS, '+')
            
            if self.current_char == '-':
                self.advance()
                return Token(MINUS, '-')
            
            if self.current_char == '*':
                self.advance()
                return Token(MUL, '*')
            
            if self.current_char == '/':
                self.advance()
                return Token(DIV, '/')
            
            if self.current_char == '(':
                self.advance()
                return Token(LPAREN, '(')
            
            if self.current_char == ')':
                self.advance()
                return Token(RPAREN, ')')

            self.error()
        
        return Token(EOF, None)


###############################################################
#                                                             #
#       PARSER                                                #
#                                                             #
###############################################################

class AST(object):
    pass


class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right
    

class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value


class Parser(object):
    def __init__(self, lexer):
        self.lexer = lexer
        # set current token to first token taken from input
        self.current_token = self.lexer.get_next_token()
    
    def error(self):
        raise Exception('Invalid syntax')
    
    def eat(self, token_type):
        # compares current token type to passed token type
        # and if they match then 'eats' the current token
        # and sets current token to self.get_next_token,
        # otherwise raise an Exception
        if self.current_token.type == token_type:
            # that was tasty give me another
            self.current_token = self.lexer.get_next_token() 
        else:
            # Yuck, throw a tantrum
            self.error()
        
    def factor(self):
        """factor   : INTEGER | LPAREN expr RPAREN"""
        token = self.current_token # what am I looking at
        if token.type == INTEGER: # I'm looking at an integer
            self.eat(INTEGER)
            return Num(token) # therefore I should return a Num node
        elif token.type == LPAREN: # this is a bracketed expression
            self.eat(LPAREN)
            node = self.expr() # evaluate the expression in the middle
            self.eat(RPAREN)
            return node # and return it
    
    def term(self):
        """term     : factor ((MUL | DIV) factor)*"""
        node = self.factor() # we've got a factor here

        while self.current_token.type in (MUL, DIV):
            # oh, there's an operator
            token = self.current_token # what kind of operator?
            if token.type == MUL:
                self.eat(MUL)
            elif token.type == DIV:
                self.eat(DIV)
            
            # operator is now the node, with old node on the left and
            # another factor on the right
            node = BinOp(left=node, op=token, right=self.factor())

        return node

    def expr(self):
        """
        expr    : term ((PLUS | MINUS) term)*
        term    : factor ((MUL | DIV) factor)*
        factor  : INTEGER | LPAREN expr RPAREN
        """
        node = self.term()

        while self.current_token.type in (PLUS, MINUS):
            token = self.current_token
            if token.type == PLUS:
                self.eat(PLUS)
            elif token.type == MINUS:
                self.eat(MINUS)

            node = BinOp(left=node, op=token, right=self.term())

        return node

    def parse(self):
        return self.expr()


#####################################################################
#                                                                   #
#       INTERPRETER                                                 #
#                                                                   #
#####################################################################

class NodeVisitor(object):
    def visit(self, node):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception('No visit_{} method'.format(type(node).__name__))


class Interpreter(NodeVisitor):
    def __init__(self, parser):
        self.parser = parser

    def visit_BinOp(self, node):
        if node.op.type == PLUS:
            return self.visit(node.left) + self.visit(node.right)
        if node.op.type == MINUS:
            return self.visit(node.left) - self.visit(node.right)
        if node.op.type == MUL:
            return self.visit(node.left) * self.visit(node.right)
        if node.op.type == DIV:
            return self.visit(node.left) // self.visit(node.right)

    def visit_Num(self, node):
        return node.value

    def interpret(self):
        tree = self.parser.parse()
        return self.visit(tree)


def main():
    while True:
        try:
            text = input('spi> ')
        except EOFError:
            break
        if not text:
            sys.exit()

        lexer = Lexer(text)
        parser = Parser(lexer)
        interpreter = Interpreter(parser)
        result = interpreter.interpret()
        print(result)


if __name__ == '__main__':
    main()
import astroid
import six

from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker
from pylint.checkers.classes import _ancestors_to_call

BASE_ID = 76

def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(UnitTestSetupSuperChecker(linter))

MESSAGES = {
    'E%d01' % BASE_ID: ("super(...).setUp() not called (%s)",
                        'super-setup-not-called',
                        "setUp() must called super(...).setUp()"),
}

class UnitTestSetupSuperChecker(BaseChecker):

    __implements__ = (IAstroidChecker,)

    name = 'unit-test-super-checker'

    MESSAGE_ID = 'super-setup-not-called'
    METHOD_NAME = 'setUp'
    msgs = MESSAGES

    def visit_function(self, node):
        """check method arguments, overriding"""
        # ignore actual functions
        if not node.is_method():
            return

        if not node.name == 'setUp':
            return

        if not self.linter.is_message_enabled(self.MESSAGE_ID):
            return

        klass_node = node.parent.frame()
        to_call = _ancestors_to_call(klass_node, self.METHOD_NAME)

        not_called_yet = dict(to_call)
        for stmt in node.nodes_of_class(astroid.CallFunc):
            expr = stmt.func
            if not isinstance(expr, astroid.Getattr) \
                   or expr.attrname != self.METHOD_NAME:
                continue
            # skip the test if using super
            if isinstance(expr.expr, astroid.CallFunc) and \
                   isinstance(expr.expr.func, astroid.Name) and \
               expr.expr.func.name == 'super':
                return
            try:
                klass = next(expr.expr.infer())
                if klass is YES:
                    continue
                # The infered klass can be super(), which was
                # assigned to a variable and the `__init__` was called later.
                #
                # base = super()
                # base.__init__(...)

                if (isinstance(klass, astroid.Instance) and
                        isinstance(klass._proxied, astroid.Class) and
                        is_builtin_object(klass._proxied) and
                        klass._proxied.name == 'super'):
                    return
                try:
                    del not_called_yet[klass]
                except KeyError:
                    if klass not in to_call:
                        self.add_message('non-parent-setup-called',
                                         node=expr, args=klass.name)
            except astroid.InferenceError:
                continue
        for klass, method in six.iteritems(not_called_yet):
            if klass.name == 'object' or method.parent.name == 'object':
                continue
            self.add_message(self.MESSAGE_ID, args=klass.name, node=node)
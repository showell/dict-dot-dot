class Let:
    def __init__(self, bindings, in_):
        self.bindings = bindings
        self.in_ = in_

    def __str__(self):
        return 'LET:\n' + \
                '\n==\n'.join(self.bindings) + \
                '\nIN:\n' + self.in_

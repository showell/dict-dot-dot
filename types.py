class Let:
    def __init__(self, let, in_):
        self.let = let
        self.in_ = in_

    def __str__(self):
        return 'LET:\n' + self.let + '\nIN:\n' + self.in_

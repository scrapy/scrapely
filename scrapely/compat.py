try:
    utext = unicode
except NameError:
    class utext(str):
        def __repr__(self):
            return 'u{}'.format(super(utext, self).__repr__())

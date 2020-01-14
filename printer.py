####################
## A MODULE FOR INDENTED PRINTING UTILITIES
####################

_PRINTLVL_INDENT = '  ' # two spaces per level of indent

_indent_cache_prevlvlindent = _PRINTLVL_INDENT
_indent_cache = {}
def _getindent(lvl=0):
    if(type(lvl) is not int): raise TypeError("indent lvl must be a positive integer!")
    if(lvl < 0): raise ValueError("indent lvl must be a positive integer!")
    # ensure the cache is still valid; if not, clear it
    global _indent_cache_prevlvlindent
    global _indent_cache
    if(_indent_cache_prevlvlindent != _PRINTLVL_INDENT):
        _indent_cache.clear()
        _indent_cache_prevlvlindent = _PRINTLVL_INDENT
    # lazily initialize cache values as needed
    if lvl not in _indent_cache:
        _indent_cache[lvl] = _PRINTLVL_INDENT * lvl
    return _indent_cache[lvl]

## internal automatic print level management; used for ease of use of the out method
_prtlvl = 0
def get_prtlvl():
    '''get internal automatic print level'''
    return _prtlvl
def set_prtlvl(set_amt=0):
    '''set internal automatic print level to a given amount (default 0)'''
    global _prtlvl
    _prtlvl = int(set_amt)
def inc_prtlvl(inc_amt=1):
    '''increment internal automatic print level by a given amount (default 1)'''
    global _prtlvl
    _prtlvl += int(inc_amt)
def dec_prtlvl(dec_amt=1):
    '''decrement internal automatic print level by a given amount (default 1)'''
    global _prtlvl
    _prtlvl -= int(dec_amt)
    if(_prtlvl < 0):
        _prtlvl = 0

def out(msg='', end='\n', flush=False, prtlvl=None, inc=False, dec=False):
    if(prtlvl==None):
        prtlvl = _prtlvl
    else:
        prtlvl = int(prtlvl)
    if(inc): inc_prtlvl() # always do inc before printing
    if(dec and not inc): dec_prtlvl() # if only dec, do it before printing
    print(_getindent(prtlvl) + msg, end=end, flush=flush)
    if(dec and inc): dec_prtlvl() # if both inc and dec, do dec after printing

SEVERITY_DEBUG = 0
SEVERITY_INFO = 1
SEVERITY_WARNING = 2
SEVERITY_ERROR = 3
_print_severity = SEVERITY_DEBUG
def set_severity_level(severity=SEVERITY_DEBUG):
    global _print_severity
    _print_severity = int(severity)
def debug(msg='', end='\n', flush=False, prtlvl=None, inc=False, dec=False):
    if _print_severity <= SEVERITY_DEBUG:
        out(msg=msg, end=end, flush=flush, prtlvl=prtlvl, inc=inc, dec=dec)
def info(msg='', end='\n', flush=False, prtlvl=None, inc=False, dec=False):
    if _print_severity <= SEVERITY_INFO:
        out(msg=msg, end=end, flush=flush, prtlvl=prtlvl, inc=inc, dec=dec)
def warn(msg='', end='\n', flush=False, prtlvl=None, inc=False, dec=False):
    if _print_severity <= SEVERITY_WARNING:
        out(msg=msg, end=end, flush=flush, prtlvl=prtlvl, inc=inc, dec=dec)
def error(msg='', end='\n', flush=False, prtlvl=None, inc=False, dec=False):
    if _print_severity <= SEVERITY_ERROR:
        out(msg=msg, end=end, flush=flush, prtlvl=prtlvl, inc=inc, dec=dec)


## testing
def _testing():
    print('internal prtlvl = {}'.format(get_prtlvl()))
    out('testing default printing')
    set_prtlvl(3)
    print('internal prtlvl = {}'.format(get_prtlvl()))
    out('testing print out now')
    set_prtlvl()
    print('internal prtlvl = {}'.format(get_prtlvl()))
    out('testing default set params')

    out()
    out('testing inc and dec used in looped printing...')
    inc_prtlvl()
    for i in range(3):
        out('doing stuff {}:'.format(i))
        inc_prtlvl(2)
        for j in range(i+1):
            out('doing really indented stuff {}'.format(j))
        dec_prtlvl(2)
        out('done with stuff {}'.format(i))
    dec_prtlvl()
    out('done testing inc and dec!')
    print('internal prtlvl = {}'.format(get_prtlvl()))

    out()
    out('testing changing internal indent string')
    set_prtlvl(2)
    out('indent 2 example')
    global _PRINTLVL_INDENT
    _PRINTLVL_INDENT = '> '
    out('indent 2 example again')
    inc_prtlvl()
    out('indent 3 example')
    dec_prtlvl(2)
    out('indent 1 example')
    dec_prtlvl(2343)
    out('no indent example')
if __name__ == "__main__":
    _testing()
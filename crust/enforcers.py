from error import ShellValidationError



def enforce_integer(value):

    try:

        return int(value)

    except Exception as e:

        raise ShellValidationError('%s: %s' % (e.__class__.__name__, e.message))

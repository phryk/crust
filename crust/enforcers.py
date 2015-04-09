from error import CommandValidationError



def enforce_integer(value):

    try:

        return int(value)

    except Exception as e:

        raise CommandValidationError('%s: %s' % (e.__class__.__name__, e.message))

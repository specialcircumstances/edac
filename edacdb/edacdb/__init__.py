from django.db.backends.signals import connection_created


def deactivate_synchronous(sender, connection, **kwargs):
    """Try to improve write preformance for those large JSON imports"""
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA synchronous = OFF;')
        cursor.execute('PRAGMA journal_mode = MEMORY;')
        cursor.execute('PRAGMA cache_size = 100000;')


connection_created.connect(deactivate_synchronous)

class ReadOnlyDBRouter:
    """
    A database router that directs all read operations to either 'readonly_db' or 
    'production_scheduler', while preventing write operations and migrations.
    """
    
    def db_for_read(self, model, **hints):
        """ Directs read operations for specific models to 'readonly_db'. """
        if model._meta.app_label == 'main':  # Change 'myapp' to the relevant app
            return 'readonly_db'  # Use readonly database
        elif model._meta.app_label == 'scheduler':  # assuming this is the app label for ProductionScheduler-related models
            return 'production_scheduler'
        return None

    def db_for_write(self, model, **hints):
        """ Prevent write operations for the read-only database. """
        return None  # Prevents writing to 'readonly_db'

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """ Prevents migrations for the read-only database. """
        if db in ['readonly_db', 'production_scheduler']:
            return False  # No migrations on the read-only DB
        return None

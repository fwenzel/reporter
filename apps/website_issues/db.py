class DatabaseRouter(object):
    """
    Route all operations on the websites issues models to the
    'websites_issues' database and only to that.
    """

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'website_issues':
            return 'website_issues'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'website_issues':
            return 'website_issues'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'website_issues' and \
           obj2._meta.app_label == 'website_issues':
            return True
        return None

    def allow_syncdb(self, db, model):
        if db == 'website_issues':
            return model._meta.app_label == 'website_issues'
        elif model._meta.app_label == 'website_issues':
            return False
        return None

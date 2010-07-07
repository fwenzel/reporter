from django.db import models


class InnerQuery(models.query.sql.Query):
    """
    Extends sql.Query to always treat LEFT JOINs as INNER JOINs.
    Only use this if you know INNER JOINs will return the correct results
    for your data.
    """
    LOUTER = 'INNER JOIN'

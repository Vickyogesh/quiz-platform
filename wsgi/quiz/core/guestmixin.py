from datetime import datetime


class GuestMixin(object):
    """Mixin for processing guest access."""
    def __init__(self):
        self.__getinfo = self.sql("""SELECT * FROM guest_access WHERE
                                  id=:id AND quiz_type=:quiz_type""")

        self.__fresh = self.sql("""UPDATE guest_access SET num_requests=1,
            period_end=UTC_TIMESTAMP() + interval 1 hour WHERE id=:id AND
            quiz_type=:quiz_type""")

    def processGuestAccess(self, quiz_type, user_id):
        """Process guest access.

        Request is allowed if total number of requests within one hour
        is less than X (10 by default).

        Returns:
            True if service allows guest request.
        """
        row = self.__getinfo.execute(id=user_id, quiz_type=quiz_type).fetchone()
        num_requests = row[2]
        period_end = row[3]

        allow = False

        # If number of requests is less than limit then
        # we don't check access perion end time.
        if num_requests <= self.guest_allowed_requests:
            allow = True

        # If number of requests is more than limit
        # and access period is expired then we
        # set new access period time and reset num of requests to 1.
        elif datetime.utcnow() >= period_end:
            self.__fresh.execute(id=user_id, quiz_type=quiz_type)
            allow = True

        return allow

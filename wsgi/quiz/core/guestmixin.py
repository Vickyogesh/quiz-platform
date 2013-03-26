from datetime import datetime
from sqlalchemy import text


class GuestMixin(object):
    """Mixin for processing guest access. Used in QuizCore."""
    def __init__(self):
        self.__getinfo = text("SELECT * FROM guest_access WHERE id=:id")
        self.__getinfo = self.__getinfo.compile(self.engine)

        self.__fresh = text("""UPDATE guest_access SET num_requests=1,
            period_end=UTC_TIMESTAMP() + interval 1 hour WHERE id=:id""")
        self.__fresh = self.__fresh.compile(self.engine)

    def processGuestAccess(self, user_id):
        """Process guest access.

        Request is allowed if total number of requests within one hour
        is less than X (10 by default).

        Return True if service allows guest request.
        """
        row = self.__getinfo.execute(id=user_id).fetchone()
        num_requests = row[1]
        period_end = row[2]

        allow = False

        # If number of requests is less than limit then
        # we don't check access perion end time.
        if num_requests <= self.guest_allowed_requests:
            allow = True

        # If number of requests is more than limit
        # and access period is expired then we
        # set new access period time and reset num of requests to 1.
        elif datetime.utcnow() >= period_end:
            self.__fresh.execute(id=user_id)
            allow = True

        return allow

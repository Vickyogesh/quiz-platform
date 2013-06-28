class AdminMixin(object):
    """This mixin provides administration features. Used in QuizCore."""

    # used
    # TODO: just delete all related users
    # NOTE: triggers will delete school's users and
    # their data on school delete.
    # See _createFuncs() in the misc/dbtools.py
    def deleteSchool(self, id):
        # We have to remove all related data like students and their data.
        t = self.users
        dl = t.delete().where(t.c.school_id == id)
        self.engine.execute(dl)
        return {}

class AdminMixin(object):
    """This mixin provides administration features."""

    def deleteSchool(self, id):
        """Delete all school info from the DB.

        Args:
            id: School ID.

        Note:
            Triggers will delete school's users and their data on school delete.
            See :file:`misc/dbtools/func.py`.
        """
        # We have to remove all related data like students and their data.
        t = self.users
        dl = t.delete().where(t.c.school_id == id)
        self.engine.execute(dl)
        return {}

    def getStatByExams(self):
        # See update() in stat.py
        sql = self.stat_json.select().where(self.stat_json.c.name == 'exams')
        res = self.engine.execute(sql).fetchone()
        if res:
            return res[1]

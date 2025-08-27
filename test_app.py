import unittest
from app import app, mongo

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_mongo_connection(self):
        # BEGIN: Test MongoDB connection
        try:
            mongo.db.command("ping")
            connection_status = True
        except Exception as e:
            connection_status = False
        # END: Test MongoDB connection
        self.assertTrue(connection_status, "MongoDB connection failed")

if __name__ == "__main__":
    unittest.main()
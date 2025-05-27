import unittest
from ai_whisperer.commands.echo import EchoCommand
from ai_whisperer.commands.status import StatusCommand

class TestCommands(unittest.TestCase):
    def test_echo(self):
        cmd = EchoCommand()
        self.assertEqual(cmd.run('hello world'), 'hello world')
        self.assertEqual(cmd.run(''), '')

    def test_status(self):
        cmd = StatusCommand()
        self.assertEqual(cmd.run(''), 'Status: OK')

if __name__ == '__main__':
    unittest.main()

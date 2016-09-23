import unittest

import bslint
import bslint.error_messages_builder.error_builder.error_messages_constants as err_const
import bslint.error_messages_builder.error_message_handler as err
import bslint.utilities.commands as commands
import bslint.lexer as lexer


class TestSkipFileCommand(unittest.TestCase):

    WARNINGS = 'Warnings'

    def testSkipFileCommandSkipStart(self):
        exp_result = []
        result = lexer.lex("'BSLint_skip_file \nxgygu= 22\ny=4\n sdfsf=2 \n")
        self.assertEqual(exp_result, result[self.WARNINGS])

    def testSkipFileCommandSkipHalfWay(self):
        exp_result = []
        result = lexer.lex("one = 22\ntwo = 4\n'BSLint_skip_file \n sdfsf=2 \n")
        self.assertEqual(exp_result, result[self.WARNINGS])

    def testSkipFileCommandSkipStartInactive(self):
        bslint.load_config_file("BSLintCommands/inactive-skip-file-config.json")
        exp_result = [err.get_message(err_const.TYPO_IN_CODE, [2])]
        result = lexer.lex("'BSLint_skip_file \nxgygu = 22\ny = 4")
        self.assertEqual(exp_result, result[self.WARNINGS])

    def testSkipFileCommandSkipHalfwayInactive(self):
        exp_result = []
        result = lexer.lex("one = 22\ntwo = 4\n'BSLint_skip_file\ntwo = 2\n")
        self.assertEqual(exp_result, result[self.WARNINGS])
